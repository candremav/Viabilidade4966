
def CDBPre(P, i, inicio, liq, contrato, q=1, agg='S', freq_i='A', comiss=0.0):

    """
    Calcula o plano de pagamento de um Certificado de Depósito Bancário (CDB) pré-fixado.

    Parameters
    ----------
    P : float
        Valor principal do CDB.
    i : float
        Taxa de juros anual efetiva do CDB.
    inicio : str or datetime-like
        Data de início do CDB.
    liq : str or datetime-like
        Data de liquidação do CDB.
    contrato : str
        Identificador do contrato.
    q : int, optional
        Quantidade de CDBs, padrão é 1.
    agg : str, optional
        Agregação dos dados ('S' para mensal, 'N' para diário), padrão é 'S'.
    freq_i : str, optional
        Frequência dos juros ('A' para anual, 'M' para mensal, 'D' para diário), padrão é 'A'.
    comiss : float, optional
        Valor da comissão em dinheiro (R$), padrão é 0.0.

    Returns
    -------
    pandas.DataFrame
        DataFrame contendo o plano de pagamento do CDB, incluindo juros, amortização, saldo devedor,
        e informações adicionais conforme configurado pelos parâmetros.

    Examples
    --------
    >>> df_cdb_pre = CDBPre(10000, 0.08, '2023-01-01', '2023-12-31', 'XYZ123', pd.date_range('2023-01-01', '2023-12-31', freq='B'))
    >>> print(df_cdb_pre.head())

    Notes
    -----
    Esta função calcula o plano de pagamento de um Certificado de Depósito Bancário (CDB) pré-fixado,
    levando em consideração os dias úteis para o cálculo dos juros e a frequência de capitalização dos mesmos.
    """

    import pandas as pd
    import numpy as np
    from datetime import datetime

    #Numero de Contratos
    P = q*P

    # Convertendo 'inicio' para datetime
    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(liq)

    if freq_i == 'A':
        i_diario = (1 + i)**(1/360) - 1
    elif freq_i == 'M':
        i_anual = (1 + i)**12 - 1  # Taxa anual equivalente
        i_diario = (1 + i_anual)**(1/360) - 1
    elif freq_i == 'D':
        i_diario = i

    # Gerando série temporal diária entre 'inicio' e 'liq'
    datas = pd.date_range(start=inicio, end=liq, freq='D')

    # Inicializando o DataFrame
    df = pd.DataFrame(index=datas)
    df['Data'] = df.index
    df['Periodo'] = np.arange(len(df))
    df['Saldo'] = 0.0
    df['Juros'] = 0.0
    df['Comissao'] = 0.0
    df['DespComissao'] = 0.0
    df['Captacao'] = 0.0
    df['Parcela'] = 0.0
    df['Amortizacao'] = 0.0 
    df['Contrato'] = contrato

    df.loc[df['Data'] == fim, 'Amortizacao'] = P

    juros_acumulados = 0.0

    if len(datas) == 0:
        comiss_du = 0.0
    else:
        comiss_du = comiss/len(datas)

    df.at[inicio, 'Saldo'] = P  # O saldo inicial é P
    df.at[inicio, 'Comissao'] = comiss  # O saldo inicial é P
    df.at[inicio, 'Captacao'] = df.at[inicio, 'Saldo']  - df.at[inicio, 'Comissao'] # Saldo menos o pagamento da comissão

    # Atualizando juros e saldo
    for idx in df.index[1:]:  # Começa a partir do segundo dia
        dia_anterior = idx - pd.Timedelta(days=1)
        juros = 0.0
        comiss_dia = 0.0

        juros = df.at[dia_anterior, 'Saldo'] * i_diario
        juros_acumulados += juros
        comiss_dia = comiss_du

        df.at[idx, 'Juros'] = juros
        df.at[idx, 'DespComissao'] =  comiss_dia
        df.at[idx, 'Comissao'] =  df.at[dia_anterior, 'Comissao'] - comiss_dia

        if df.at[idx, 'Amortizacao'] > 0:
            df.at[idx, 'Parcela'] = df.at[idx, 'Amortizacao'] + juros_acumulados
            juros_acumulados = 0.0
        else:
            df.at[idx, 'Parcela'] = 0.0

        df.at[idx, 'Saldo'] = df.at[dia_anterior, 'Saldo'] + juros - df.at[idx, 'Parcela']

    # Adicionando colunas 'Mes' e 'Ano'
    df['Ano'] = df['Data'].dt.year
    df['Mes'] = df['Data'].dt.month

    if agg=='S':
        # Agregação por 'Ano' e 'Mes'
        aggregations = {
            'Data': 'last',
            'Periodo': 'last',
            'Saldo': 'last',
            'Amortizacao': 'sum',
            'Contrato': 'last',
            'Juros': 'sum',
            'Comissao': 'last',
            'Captacao': 'sum',
            'DespComissao': 'sum', 
            'Parcela': 'sum'
            }

        df = df.groupby(['Ano', 'Mes']).agg(aggregations).reset_index()
    else:
        df = df.reset_index(drop=True)

    # Arredondando colunas numéricas
    for coluna in ['Parcela', 'Juros', 'Comissao', 'Captacao', 'DespComissao', 'Amortizacao', 'Saldo']:
        df[coluna] = df[coluna].round(2)

    # Reordenando as colunas conforme especificado
    df=df[['Periodo', 'Parcela', 'Juros', 'Amortizacao', 'Saldo', 'Captacao', 'Comissao', 'DespComissao',
    'Data', 'Contrato', 'Mes', 'Ano']]

    return df
