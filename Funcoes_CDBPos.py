
def CDBPos(P, df_i, inicio, liq, contrato, d_uteis, pct_index=1.20, q=1, agg='S', freq_i='D', comiss=0.0):

    """
    Calcula o plano de pagamento de um Certificado de Depósito Bancário (CDB) pós-fixado.

    Parameters
    ----------
    P : float
        Valor principal do CDB.
    df_i : pandas.DataFrame
        DataFrame contendo as taxas DI (CDI) ao longo do tempo.
    inicio : str or datetime-like
        Data de início do CDB.
    liq : str or datetime-like
        Data de liquidação do CDB.
    contrato : str
        Identificador do contrato.
    d_uteis : list or pd.DatetimeIndex
        Lista de dias úteis para o cálculo dos juros.
    pct_index : float, optional
        Percentual do CDI indexador do CDB, padrão é 1.20.
    q : int, optional
        Quantidade de CDBs, padrão é 1.
    agg : str, optional
        Agregação dos dados ('S' para mensal, 'N' para diário), padrão é 'S'.
    freq_i : str, optional
        Frequência das taxas DI ('A' para anual, 'M' para mensal, 'D' para diário), padrão é 'D'.
    comiss : float, optional
        Valor da comissão em dinheiro (R$), padrão é 0.0.

    Returns
    -------
    pandas.DataFrame
        DataFrame contendo o plano de pagamento do CDB, incluindo juros, amortização, saldo devedor,
        e informações adicionais conforme configurado pelos parâmetros.

    Examples
    --------
    >>> df_cdb_pos = CDBPos(10000, df_taxas_DI, '2023-01-01', '2023-12-31', 'XYZ123', pd.date_range('2023-01-01', '2023-12-31', freq='B'))
    >>> print(df_cdb_pos.head())

    Notes
    -----
    Esta função calcula o plano de pagamento de um Certificado de Depósito Bancário (CDB) pós-fixado,
    utilizando as taxas DI (CDI) como indexador, e leva em consideração os dias úteis para o cálculo dos juros.
    """

    import pandas as pd
    import numpy as np
    from datetime import datetime

    #Numero de Contratos
    P = q*P

    # Convertendo 'inicio' para datetime
    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(liq)

    cdi=df_i.copy()

    if freq_i == 'A':
        cdi['Taxa'] = (1 + cdi['Taxa'])**(1/252) - 1
    elif freq_i == 'M':
        cdi['Taxa'] = (1 + cdi['Taxa'])**12 - 1
        cdi['Taxa'] = (1 + cdi['Taxa'])**(1/252) - 1
    elif freq_i == 'D':
        cdi['Taxa'] = cdi['Taxa']

    # Gerando série temporal diária entre 'inicio' e 'liq'
    datas = pd.date_range(start=inicio, end=liq, freq='D')

    # Inicializando o DataFrame
    df = pd.DataFrame(index=datas)
    df['Data'] = df.index
    df['Periodo'] = np.arange(len(df))
    df['Saldo'] = P
    df['Juros'] = 0.0
    df['Comissao'] = 0.0
    df['DespComissao'] = 0.0
    df['Captacao'] = 0.0
    df['Parcela'] = 0.0
    df['Amortizacao'] = 0.0 
    df['Contrato'] = contrato

    df = pd.merge(df, cdi[['Data', 'Taxa']], on='Data', how='left')
    df.rename(columns={'Taxa': 'CDI'}, inplace=True)

    # Preenchendo os valores NaN na coluna 'CDI' resultante com 0
    df['CDI'] = df['CDI'].fillna(0)

    df['Taxa'] = df['CDI']*pct_index

    df.loc[df['Data'] == fim, 'Amortizacao'] = P

    df['Data_Index']=df['Data']

    df.set_index('Data_Index', inplace=True)

    juros_acumulados = 0.0
    n_d_uteis = df.iloc[1:]['Data'].isin(d_uteis).sum()

    if len(datas) == 0:
        comiss_du = 0.0
    else:
        comiss_du = comiss/len(datas)

    df.at[inicio, 'Saldo'] = P  # O saldo inicial é P
    df.at[inicio, 'Comissao'] = comiss  # O saldo inicial é P
    df.at[inicio, 'Captacao'] = df.at[inicio, 'Saldo'] - df.at[inicio, 'Comissao']  # Saldo menos o pagamento da comissão

    # Atualizando juros, saldo e comissao
    for idx in df.index[1:]:  # Começa a partir do segundo dia
        dia_anterior = idx - pd.Timedelta(days=1)
        juros = 0.0
        comiss_dia = 0.0

        if idx in d_uteis:
            juros = df.at[dia_anterior, 'Saldo'] * df.at[idx,'Taxa']
            juros_acumulados += juros
            comiss_dia = comiss_du

        df.at[idx, 'Juros'] = juros
        df.at[idx, 'DespComissao'] =  comiss_dia
        df.at[idx, 'Comissao'] =  df.at[dia_anterior, 'Comissao'] - comiss_dia

        if df.at[idx, 'Amortizacao'] > 0:
            df.at[idx, 'Parcela'] = df.at[idx, 'Amortizacao'] + juros_acumulados
            juros_acumulados = 0.0
            comissao_acumulada = 0.0
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
            'Parcela': 'sum',
            'CDI': 'mean',
            'Taxa': 'mean'
            }

        df = df.groupby(['Ano', 'Mes']).agg(aggregations).reset_index()
    else:
        df = df.reset_index(drop=True)

    # Arredondando colunas numéricas
    for coluna in ['Parcela', 'Juros', 'Comissao', 'Captacao', 'DespComissao', 'Amortizacao', 'Saldo']:
        df[coluna] = df[coluna].round(2)

    # Arredondando colunas numéricas
    for coluna in ['Taxa', 'CDI']:
        df[coluna] = df[coluna].round(7)

    # Reordenando as colunas conforme especificado
    df=df[['Periodo', 'Parcela', 'Juros', 'Amortizacao', 'Saldo', 'Captacao', 'Comissao', 'DespComissao',
    'Data', 'Contrato', 'CDI', 'Taxa', 'Mes', 'Ano']]

    return df
