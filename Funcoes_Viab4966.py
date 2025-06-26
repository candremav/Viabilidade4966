
import pandas as pd
import numpy as np
import numpy_financial as npf
from datetime import datetime
import os
import sys

from Funcoes_Funcao4966 import Funcao4966
from Funcoes_DU import Dias_Uteis
from Funcoes_CDBPre import CDBPre
from Funcoes_CDBPos import CDBPos

def Viab4966(
    base_tipo='CONSIG',
    base_inad=0.06,
    base_taxa=0.027,
    base_prazo=96,
    base_periodos=12,
    base_quantid=[850, 1020, 1190, 1360, 1530, 1700, 1700, 1700, 1700, 1700, 1700, 1700],
    base_saldo=3000,
    base_ini=datetime.today().date(),
    base_tc=50.0,
    base_comiss_flat=0.05,
    base_comiss_dif=0.01,
    aliq_IRCSLL=0.4,
    aliq_PISCOFINS=0.0465,
    aliq_ISS=0.05,
    base_desp_mensal=15000,
    base_desp_outras=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1000],
    base_capt='POS',
    base_comiss_capt=0.04,
    base_prazo_capt=12,
    base_pos_pct_capt=1.15,
    base_pre=0.17,
    padrao_atraso=None,
    cdi=None):

    """
    Calcula a viabilidade financeira de um conjunto de contratos de empréstimos, considerando juros, inadimplência,
    comissões, despesas operacionais, impostos e características da captação.

    Parâmetros
    ----------
    base_tipo : str
        Tipo de contrato ('CONSIG', 'PESS', 'FGTS').
    base_inad : float
        Inadimplência mensal esperada (%).
    base_taxa : float
        Taxa de juros mensal aplicada aos contratos.
    base_prazo : int
        Prazo de cada contrato em meses.
    base_periodos : int
        Número de safras de originação (em meses).
    base_quantid : list
        Lista com a quantidade de contratos originados por mês.
    base_saldo : float
        Valor médio por contrato (ticket médio).
    base_ini : datetime
        Data inicial da simulação.
    base_tc : float
        Taxa de cadastro por contrato (R$).
    base_comiss_flat : float
        Comissão percentual por contrato originado.
    base_comiss_dif : float
        Comissão percentual diferida sobre cada parcela recebida.
    aliq_IRCSLL : float
        Alíquota combinada de IRPJ e CSLL.
    aliq_PISCOFINS : float
        Alíquota combinada de PIS e COFINS.
    aliq_ISS : float
        Alíquota do ISS incidente sobre receitas.
    base_desp_mensal : float
        Despesas operacionais fixas mensais (R$).
    base_desp_outras : list
        Lista de despesas variáveis por safra.
    base_capt : str
        Tipo de captação ('PRE' ou 'POS').
    base_comiss_capt : float
        Comissão de captação percentual.
    base_prazo_capt : int
        Prazo da captação em meses.
    base_pos_pct_capt : float
        Fator multiplicador sobre o CDI para captação pós-fixada.
    base_pre : float
        Taxa de captação pré-fixada anual.
    padrao_atraso : object
        Estrutura de atrasos, se aplicável. Default None.
    cdi: pandas.DataFrame
        DataFrame com a curva de CDI, contendo colunas 'Data' e 'CDI'. Se None, utiliza o CDI padrão.

    Retorno
    -------
    pandas.DataFrame
        DataFrame com os indicadores financeiros mensais da operação simulada.

    Notas
    -----
    A função consolida a lógica de originação, cálculo de fluxo de caixa e simulação de resultados financeiros
    com base nas premissas informadas. Pode ser utilizada como base para projeções, stress tests ou decisões de funding.
    """

    dias_uteis = Dias_Uteis()

    datas = [base_ini + pd.DateOffset(months=i) for i in range(base_periodos)]

    if base_tipo == 'FGTS':
        base_prazo = base_prazo//12
    originacao = pd.DataFrame({
        'Base_Prazo': [base_prazo] * base_periodos,
        'Base_Taxa': [base_taxa] * base_periodos,
        'Base_Ticket': [base_saldo] * base_periodos,
        'Base_Data': datas,
        'Base_Qtd': base_quantid,
        'Base_Tipo': [base_tipo] * base_periodos,
        'Base_Contrato': ['Contrato'] * base_periodos
    })

    originacao['Base_Saldo'] = originacao['Base_Ticket'] * originacao['Base_Qtd']
    originacao['Taxa_Origem'] = pd.NA
    originacao['Origem'] = pd.NA
    originacao['Ano'] = originacao['Base_Data'].dt.year
    originacao['Mes'] = originacao['Base_Data'].dt.month
    originacao['Receita_TC'] = base_tc * originacao['Base_Qtd']
    originacao['Desp_Comiss_Flat'] = base_comiss_flat * originacao['Base_Saldo']
    originacao['Desp_Outras'] = base_desp_outras


    #FUNÇÕES ---------------------------------------------------
    # Agregação por 'Ano' e 'Mes'
    aggregations = {
        'Parcela': 'sum',
        'Saldo': 'last',
        'SaldoCont': 'last',
        'SaldoPremio': 'last',
        'AmortPremio': 'sum',
        'Juros': 'sum',
        'JurosLiq': 'sum',
        'PDDAcum': 'last',
        'DespPDD': 'sum',
        'RevPDD': 'sum',
        'Cessao': 'sum',
        'DedutAcum': 'last',
        'DedutPeriodo': 'sum',
        'Dif_Temp': 'last',
        'C1': 'last', 'C2': 'last', 'C3': 'last', 'C4': 'last', 'C5': 'last',
        'Atraso_0_14': 'last', 'Atraso_15_30': 'last', 'Atraso_31_60': 'last', 'Atraso_61_90': 'last', 'Atraso_91_120': 'last',
        'Atraso_121_150': 'last', 'Atraso_151_180': 'last', 'Atraso_181_210': 'last', 'Atraso_211_240': 'last', 'Atraso_241_270': 'last',
        'Atraso_271_300': 'last', 'Atraso_301_330': 'last', 'Atraso_331_360': 'last', 'Atraso_361_390': 'last', 'Atraso_391_420': 'last',
        'Atraso_421_450': 'last', 'Atraso_451_480': 'last', 'Atraso_481_510': 'last', 'Atraso_511_540': 'last', 'Atraso_541_570': 'last',
        'Atraso_571_600': 'last', 'Atraso_601_630': 'last', 'Atraso_631_660': 'last', 'Atraso_661_690': 'last'}

    daily_agg = ['Parcela', 'Saldo', 'SaldoCont', 'SaldoPremio', 'AmortPremio',
                'Juros', 'JurosLiq', 'PDDAcum', 'DespPDD', 'RevPDD', 'Cessao', 'DedutAcum',
                'DedutPeriodo', 'Dif_Temp', 'C1', 'C2', 'C3', 'C4', 'C5',
                'Atraso_0_14', 'Atraso_15_30', 'Atraso_31_60', 'Atraso_61_90',
                'Atraso_91_120', 'Atraso_121_150', 'Atraso_151_180', 'Atraso_181_210',
                'Atraso_211_240', 'Atraso_241_270', 'Atraso_271_300', 'Atraso_301_330',
                'Atraso_331_360', 'Atraso_361_390', 'Atraso_391_420', 'Atraso_421_450',
                'Atraso_451_480', 'Atraso_481_510', 'Atraso_511_540', 'Atraso_541_570',
                'Atraso_571_600', 'Atraso_601_630', 'Atraso_631_660', 'Atraso_661_690']

    def calc_SAC(P, n, i):
        """Calcula as parcelas pelo método SAC (Sistema de Amortização Constante)."""
        A = P / n
        parcelas = []
        i = ((1+i)**12)-1
        for t in range(1, n + 1):
            saldo_devedor_anterior = P - (t - 1) * A
            juros = saldo_devedor_anterior * i
            parcela_total = A + juros
            parcelas.append(parcela_total)
        return parcelas

    def calc_PRICE(P, n, i):
        """Calcula as parcelas fixas pelo método PRICE."""
        parcela_fixa = P * i / (1 - (1 + i) ** -n)
        parcelas = [parcela_fixa] * n
        return parcelas

    def calc_VP(parcelas_vf, datas_parcelas, base_data, taxa_juros):
        """
        Calcula o valor presente de cada parcela futura com base nas datas futuras e na data base.

        :param parcelas_vf: Lista de parcelas futuras.
        :param datas_parcelas: Lista de datas futuras das parcelas.
        :param base_data: Data base para calcular o valor presente.
        :param taxa_juros: Taxa de juros mensal (proporcional).
        :return: Lista com os valores presentes de cada parcela.
        """

        parcelas_orig = []
        for parcela, data_parcela in zip(parcelas_vf, datas_parcelas):
            meses_diferenca = (data_parcela.year - base_data.year) * 12 + (data_parcela.month - base_data.month)
            vp = parcela / ((1 + taxa_juros) ** meses_diferenca)
            parcelas_orig.append(vp)
        return parcelas_orig


    #BASE ---------------------------------------------------
    contratos_fut_clean = originacao.copy()
    contratos_fut_clean['Base_Saldo'] = contratos_fut_clean['Base_Saldo'] * (1-base_inad)

    contratos_fut_inad = originacao.copy()
    contratos_fut_inad['Base_Saldo'] = contratos_fut_inad['Base_Saldo'] * (base_inad)

    # Supondo que contratos_fut_consig seja seu DataFrame original
    lista_fut_contratos_clean = []
    lista_fut_contratos_inad = []
    for _, row in contratos_fut_clean.iterrows():

        # Número de parcelas
        n = row['Base_Prazo']  # Usando 'Base_Prazo' como o número de parcelas

        # Taxa de juros
        i = row['Base_Taxa']

        # Saldo inicial da operação
        P = row['Base_Saldo']

        i_original = row['Taxa_Origem'] 

        # Calcular as parcelas futuras (ParcelasVF) usando SAC ou PRICE
        parcelas_vf = calc_SAC(P, n, i) if row['Base_Tipo'] == 'FGTS' else calc_PRICE(P, n, i)

        # Criar a lista de datas das parcelas
        datas_parcelas = [(row['Base_Data'] + pd.DateOffset(years=i) if row['Base_Tipo'] == 'FGTS'
                           else row['Base_Data'] + pd.DateOffset(months=i)) for i in range(1, n + 1)]

        # Calcular o valor presente das parcelas usando as datas futuras e a taxa de juros
        parcelas_orig = calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i) if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i_original)

        # Criar o dicionário diretamente com a fórmula para 'DatasParcelasMax' e 'DatasParcelas'
        contrato_dict = {
            'DataBase': row['Base_Data'],
            'Contrato': row['Base_Contrato'],
            'Qtd_Parcelas': row['Base_Prazo'],
            'Saldo': P  if pd.isna(row['Origem']) else sum(parcelas_orig),
            'DataInicio': row['Base_Data'],
            'DatasParcelasMax': (row['Base_Data'] + pd.DateOffset(years=row['Base_Prazo'])
                                 if row['Base_Tipo'] == 'FGTS' 
                                 else row['Base_Data'] + pd.DateOffset(months=row['Base_Prazo'])),
            'DiasAtrasoCont': 0,
            'RatingContrato': 'A',
            'TaxaOriginal': row['Base_Taxa'] * 100,
            'TipoTaxa': 'PRE',
            'TipoOperacao': row['Base_Tipo'],
            'Classif': ('C5' if row['Base_Tipo'] in ['CG', 'CONSIG', 'PESS', 'FGTS']
                        else 'C2' if row['Base_Tipo'] == 'RURAL'
                        else 'Desconhecido'),
            'DatasParcelas': datas_parcelas,  # Lista sequencial
            'DatasLiq': [pd.NA],  # Lista com uma observação como NaN
            'Cessao': [pd.NA],    # Lista com uma observação como NaN
            'ParcelasVF': parcelas_vf,  # Parcelas futuras
            'ParcelasOrig': parcelas_orig if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i_original),  # Valor presente das parcelas
            'Aquisicao': [pd.NA] if pd.isna(row['Origem']) else [row['Base_Data']] * n,  # Lista com uma observação como NaN
            'VlrPcCedida': [np.nan] if pd.isna(row['Origem']) else parcelas_vf,  # Lista com uma observação como NaN
            'VlrPcAquisicao': [np.nan] if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i),  # Lista com uma observação como NaN
            'VlrPcCurva': [np.nan] if pd.isna(row['Origem']) else parcelas_orig,  # Lista com uma observação como NaN
            'PremioApropriado': 0.0,
            #'PremioPendente': [np.nan] if pd.isna(row['Origem']) else (sum(calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i)) - sum(parcelas_orig)), 
            'Origem': row['Origem'],
            'TaxaOrigem': row['Taxa_Origem'] * 100
        }


        # Adicionar o dicionário à lista final
        lista_fut_contratos_clean.append(contrato_dict)
    for _, row in contratos_fut_inad.iterrows():

        # Número de parcelas
        n = row['Base_Prazo']  # Usando 'Base_Prazo' como o número de parcelas

        # Taxa de juros
        i = row['Base_Taxa']

        # Saldo inicial da operação
        P = row['Base_Saldo']

        i_original = row['Taxa_Origem'] 

        # Calcular as parcelas futuras (ParcelasVF) usando SAC ou PRICE
        parcelas_vf = calc_SAC(P, n, i) if row['Base_Tipo'] == 'FGTS' else calc_PRICE(P, n, i)

        # Criar a lista de datas das parcelas
        datas_parcelas = [(row['Base_Data'] + pd.DateOffset(years=i) if row['Base_Tipo'] == 'FGTS'
                           else row['Base_Data'] + pd.DateOffset(months=i)) for i in range(1, n + 1)]

        # Calcular o valor presente das parcelas usando as datas futuras e a taxa de juros
        parcelas_orig = calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i) if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i_original)

        # Criar o dicionário diretamente com a fórmula para 'DatasParcelasMax' e 'DatasParcelas'
        contrato_dict = {
            'DataBase': row['Base_Data'],
            'Contrato': row['Base_Contrato'],
            'Qtd_Parcelas': row['Base_Prazo'],
            'Saldo': P  if pd.isna(row['Origem']) else sum(parcelas_orig),
            'DataInicio': row['Base_Data'],
            'DatasParcelasMax': (row['Base_Data'] + pd.DateOffset(years=row['Base_Prazo']) 
                                 if row['Base_Tipo'] == 'FGTS' 
                                 else row['Base_Data'] + pd.DateOffset(months=row['Base_Prazo'])),
            'DiasAtrasoCont': 0,
            'RatingContrato': 'A',
            'TaxaOriginal': row['Base_Taxa'] * 100,
            'TipoTaxa': 'PRE',
            'TipoOperacao': row['Base_Tipo'],
            'Classif': ('C5' if row['Base_Tipo'] in ['CG', 'CONSIG', 'PESS', 'FGTS'] else 'C2' if row['Base_Tipo'] == 'RURAL' else 'Desconhecido'),
            'DatasParcelas': datas_parcelas,  # Lista sequencial
            'DatasLiq': [pd.NA],  # Lista com uma observação como NaN
            'Cessao': [pd.NA],    # Lista com uma observação como NaN
            'ParcelasVF': parcelas_vf,  # Parcelas futuras
            'ParcelasOrig': parcelas_orig if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i_original),  # Valor presente das parcelas
            'Aquisicao': [pd.NA] if pd.isna(row['Origem']) else [row['Base_Data']] * n,  # Lista com uma observação como NaN
            'VlrPcCedida': [np.nan] if pd.isna(row['Origem']) else parcelas_vf,  # Lista com uma observação como NaN
            'VlrPcAquisicao': [np.nan] if pd.isna(row['Origem']) else calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i),  # Lista com uma observação como NaN
            'VlrPcCurva': [np.nan] if pd.isna(row['Origem']) else parcelas_orig,  # Lista com uma observação como NaN
            'PremioApropriado': 0.0,
            #'PremioPendente': [np.nan] if pd.isna(row['Origem']) else (sum(calc_VP(parcelas_vf, datas_parcelas, row['Base_Data'], i)) - sum(parcelas_orig)), 
            'Origem': row['Origem'],
            'TaxaOrigem': row['Taxa_Origem'] * 100
        }

        # Adicionar o dicionário à lista final
        lista_fut_contratos_inad.append(contrato_dict)


        #EMPRÉSTIMOS ---------------------------------------------------

    if base_tipo == 'CONSIG':
        consig='S'
    else:
        consig='N'
    contratos = []

    for contrato in lista_fut_contratos_inad:
        df_resultado = Funcao4966(data_base=contrato['DataBase'], contrato=contrato['Contrato'],
                                  comiss=0.0, saldo=contrato['Saldo'], data_max=contrato['DatasParcelasMax'],
                                  atraso=contrato['DiasAtrasoCont'], inad='S', tx_juros=contrato['TaxaOriginal']/100,
                                  datas_pmt=contrato['DatasParcelas'], datas_liq=contrato['DatasLiq'],
                                  cessao=contrato['Cessao'], vf_pmt=contrato['ParcelasVF'],
                                  padrao_atraso=padrao_atraso, #Ajustar quando necessário -------------------------
                                  vp_pmt=contrato['ParcelasOrig'], aquis=contrato['Aquisicao'],
                                  vlr_cessao=contrato['VlrPcCedida'], vlr_aquis=contrato['VlrPcAquisicao'],
                                  vlr_curva=contrato['VlrPcCurva'], classif=contrato['Classif'], consig=consig)

        contratos.append(df_resultado)

    for contrato in lista_fut_contratos_clean:
        df_resultado = Funcao4966(data_base=contrato['DataBase'], contrato=contrato['Contrato'],
                                    comiss=0.0, saldo=contrato['Saldo'], data_max=contrato['DatasParcelasMax'],
                                    atraso=contrato['DiasAtrasoCont'], inad='N', tx_juros=contrato['TaxaOriginal']/100,
                                    datas_pmt=contrato['DatasParcelas'], datas_liq=contrato['DatasLiq'],
                                    cessao=contrato['Cessao'], vf_pmt=contrato['ParcelasVF'],
                                    padrao_atraso=padrao_atraso, #Ajustar quando necessário -------------------------
                                    vp_pmt=contrato['ParcelasOrig'], aquis=contrato['Aquisicao'],
                                    vlr_cessao=contrato['VlrPcCedida'], vlr_aquis=contrato['VlrPcAquisicao'],
                                    vlr_curva=contrato['VlrPcCurva'], classif=contrato['Classif'], consig=consig)

        contratos.append(df_resultado)
    # Contar quantos contratos possuem todas as colunas como NAs antes de remover as colunas
    contratos_na_count = sum([df.isna().all(axis=1).all() for df in contratos])

    # Filtrar os DataFrames da lista contratos_CONSIG para remover as colunas completamente vazias
    contratos = [df.dropna(how='all', axis=1) for df in contratos]

    # Concatenando todos os DataFrames em um único DataFrame
    df_concatenado = pd.concat(contratos, ignore_index=True)

    # Realizando o groupby nas colunas 'Ano' e 'Mes', e somando as colunas 'Saldo' e 'Juros'
    TabelasDiarias = df_concatenado.groupby('Data')[daily_agg].sum().reset_index().round(2)

    TabelasDiarias['Mes'] = TabelasDiarias['Data'].dt.month
    TabelasDiarias['Ano'] = TabelasDiarias['Data'].dt.year

    TabelasMensais = TabelasDiarias.groupby(['Ano', 'Mes']).agg(aggregations).reset_index().round(2)

    TabelasMensais['Var_PDD'] = (-(TabelasMensais['PDDAcum'] - TabelasMensais['PDDAcum'].shift(1))).fillna(-TabelasMensais.loc[0,'PDDAcum'])

    TabelasMensais['DespPDD'] = np.where(TabelasMensais['Var_PDD'] < 0, TabelasMensais['Var_PDD'], 0.0)
    TabelasMensais['RevPDD'] = np.where(TabelasMensais['Var_PDD'] > 0, TabelasMensais['Var_PDD'], 0.0)

    TabelasMensais = TabelasMensais[['Ano', 'Mes', 'Parcela', 'Saldo', 'Juros', 'PDDAcum', 'DespPDD',
                                     'RevPDD', 'DedutAcum', 'DedutPeriodo', 'Dif_Temp']].copy()

    TabelasMensais = TabelasMensais.merge(originacao[['Ano', 'Mes', 'Base_Saldo', 'Receita_TC', 'Desp_Comiss_Flat', 'Desp_Outras']], on=['Ano', 'Mes'], how='left')

    TabelasMensais = TabelasMensais.rename(columns={'Base_Saldo': 'Desembolsos', 'Juros': 'Receita_Juros', 'Saldo': 'Saldo_Carteira'})

    TabelasMensais['Desembolsos'] = -TabelasMensais['Desembolsos']
    TabelasMensais['Desp_Comiss_Flat'] = -TabelasMensais['Desp_Comiss_Flat']
    TabelasMensais['Desp_Comiss_Dif'] = -TabelasMensais['Parcela'] * base_comiss_dif
    TabelasMensais['Desp_Outras'] = -TabelasMensais['Desp_Outras']
    TabelasMensais['Desp_Mensais'] = -base_desp_mensal
    TabelasMensais['Desp_ISS'] = -TabelasMensais['Receita_TC'] * aliq_ISS
    TabelasMensais['DedutPeriodo'] = -TabelasMensais['DedutPeriodo']
    TabelasMensais['PDDAcum'] = -TabelasMensais['PDDAcum']

    TabelasMensais = TabelasMensais.fillna(0.0)
    TabelasMensais['DFC_Rec_Parcelas'] = TabelasMensais['Parcela']
    TabelasMensais['DFC_Rec_TC'] = TabelasMensais['Receita_TC']
    TabelasMensais['DFC_Des_Emprestimos'] = TabelasMensais['Desembolsos']

    TabelasMensais['DFC_Pgto_ComissFlat'] = TabelasMensais['Desp_Comiss_Flat']
    TabelasMensais['DFC_Pgto_ComissDif'] = TabelasMensais['Desp_Comiss_Dif']
    TabelasMensais['DFC_Pgto_Mensais'] = TabelasMensais['Desp_Mensais']
    TabelasMensais['DFC_Pgto_Outras'] = TabelasMensais['Desp_Outras']

    #DRE
    TabelasMensais['Desp_Captacao']=0.0
    TabelasMensais['Desp_Comiss_Capt']=0.0
    TabelasMensais['Desp_PISCOFINS']=0.0
    TabelasMensais['LAIR']=0.0
    TabelasMensais['Desp_IR_CSLL']=0.0
    TabelasMensais['Resultado_Liquido']=0.0

    #APURAÇÃO IR/CSLL
    TabelasMensais['Fiscal_Resultado']=0.0
    TabelasMensais['Fiscal_Preju_Acum']=0.0
    TabelasMensais['Fiscal_Compensacao']=0.0

    #DFC
    TabelasMensais['DFC_Pgto_PISCOFINS'] = 0.0
    TabelasMensais['DFC_Pgto_ISS'] = 0.0
    TabelasMensais['DFC_Pgto_IRCSLL'] = 0.0
    TabelasMensais['DFC_Rec_Captacao'] = 0.0
    TabelasMensais['DFC_Des_Captacao'] = 0.0
    TabelasMensais['DFC_Necess_Caixa'] = 0.0
    TabelasMensais['DFC_FC_Liquido'] = 0.0
    TabelasMensais['DFC_Caixa_Acum'] = 0.0

    #CONTROLE
    TabelasMensais['Saldo_Captacao'] = 0.0
    TabelasMensais['Saldo_Comissoes'] = 0.0

    Viabilidade = TabelasMensais[['Ano', 'Mes',
                                  #DRE
                                  'Receita_Juros', 'Receita_TC', 'Desp_Captacao', 'Desp_PISCOFINS', 'Desp_ISS', 
                                  'Desp_Comiss_Flat', 'Desp_Comiss_Dif', 'Desp_Comiss_Capt', 'Desp_Mensais', 'Desp_Outras',
                                  'DespPDD', 'RevPDD', 'DedutPeriodo', 'LAIR', 'Desp_IR_CSLL', 'Resultado_Liquido',

                                  #BALANÇO
                                  'Saldo_Carteira', 'PDDAcum', 'DedutAcum', 'Dif_Temp', 'Saldo_Captacao', 'Saldo_Comissoes',

                                  #DFC
                                  'DFC_Rec_Parcelas', 'DFC_Rec_TC', 'DFC_Des_Emprestimos','DFC_Pgto_ComissFlat', 'DFC_Pgto_ComissDif', 'DFC_Pgto_Mensais',
                                  'DFC_Pgto_Outras', 'DFC_Pgto_PISCOFINS', 'DFC_Pgto_ISS', 'DFC_Pgto_IRCSLL', 'DFC_Rec_Captacao',
                                'DFC_Des_Captacao', 'DFC_Necess_Caixa', 'DFC_FC_Liquido', 'DFC_Caixa_Acum',

                                  #APURAÇÃO IR/CSLL
                                  'Fiscal_Resultado', 'Fiscal_Preju_Acum', 'Fiscal_Compensacao']].copy()
    datas = [base_ini + pd.DateOffset(months=i) for i in range(len(Viabilidade))]

    Viabilidade['Data'] = datas
    Viabilidade.loc[0, 'DFC_Necess_Caixa'] = (Viabilidade.loc[0, 'DFC_Rec_Parcelas'] + Viabilidade.loc[0, 'DFC_Des_Emprestimos'] +
                                          Viabilidade.loc[0, 'DFC_Rec_TC'] + Viabilidade.loc[0, 'DFC_Pgto_ComissFlat'] + Viabilidade.loc[0, 'DFC_Pgto_ComissDif'] +
                                          Viabilidade.loc[0, 'DFC_Pgto_Mensais'] + Viabilidade.loc[0, 'DFC_Pgto_Outras'] +
                                          Viabilidade.loc[0, 'DFC_Pgto_PISCOFINS'] + Viabilidade.loc[0, 'DFC_Pgto_ISS'] +
                                          Viabilidade.loc[0, 'DFC_Pgto_IRCSLL'] + Viabilidade.loc[0, 'DFC_Rec_Captacao'] +
                                          Viabilidade.loc[0, 'DFC_Des_Captacao'] + Viabilidade.loc[0, 'DFC_Caixa_Acum'])
    if Viabilidade.loc[0, 'DFC_Necess_Caixa'] < 0:
        if base_capt == 'POS':
            Simul_CDB=CDBPos(P=-Viabilidade.loc[0, 'DFC_Necess_Caixa']*(1+base_comiss_capt), df_i=CDI_Full, inicio=Viabilidade.loc[0, 'Data'],
                                liq=Viabilidade.loc[0, 'Data'] + pd.DateOffset(months=base_prazo_capt), contrato='B', d_uteis=CDI_Full['Data'].tolist(),
                                pct_index=base_pos_pct_capt, q=1, agg='S', freq_i='D', comiss=-Viabilidade.loc[0, 'DFC_Necess_Caixa']*(base_comiss_capt))
        elif base_capt == 'PRE':
            Simul_CDB=CDBPre(P=-Viabilidade.loc[0, 'DFC_Necess_Caixa']*(1+base_comiss_capt), inicio=Viabilidade.loc[0, 'Data'],
                                liq=Viabilidade.loc[0, 'Data'] + pd.DateOffset(months=base_prazo_capt), contrato='B', 
                                i=base_pre, q=1, agg='S', freq_i='A', comiss=-Viabilidade.loc[0, 'DFC_Necess_Caixa']*(base_comiss_capt))
    Simul_CDB = Simul_CDB[['Ano', 'Mes', 'Parcela', 'Juros', 'Saldo', 'Captacao', 'Comissao', 'DespComissao']]

    Simul_CDB = Simul_CDB.rename(columns={'Captacao': 'DFC_Rec_Captacao', 'Parcela': 'DFC_Des_Captacao', 'DespComissao':'Desp_Comiss_Capt', 
                                          'Juros': 'Desp_Captacao', 'Saldo': 'Saldo_Captacao', 'Comissao': 'Saldo_Comissoes'})

    Simul_CDB['DFC_Des_Captacao'] = -Simul_CDB['DFC_Des_Captacao']
    Simul_CDB['Desp_Comiss_Capt'] = -Simul_CDB['Desp_Comiss_Capt']
    Simul_CDB['Desp_Captacao'] = -Simul_CDB['Desp_Captacao']

    Viabilidade = pd.merge(Viabilidade, Simul_CDB, on=['Ano', 'Mes'], how='outer', suffixes=('','_simul'))

    Viabilidade = Viabilidade.fillna(0.0)

    Viabilidade['DFC_Des_Captacao'] += Viabilidade['DFC_Des_Captacao_simul']
    Viabilidade['Desp_Captacao'] += Viabilidade['Desp_Captacao_simul']
    Viabilidade['Saldo_Captacao'] += Viabilidade['Saldo_Captacao_simul']
    Viabilidade['Saldo_Comissoes'] += Viabilidade['Saldo_Comissoes_simul']
    Viabilidade['Desp_Comiss_Capt'] += Viabilidade['Desp_Comiss_Capt_simul']

    Viabilidade['DFC_Rec_Captacao'] += Viabilidade['DFC_Rec_Captacao_simul']

    cols_para_excl = ['DFC_Des_Captacao_simul', 'Desp_Captacao_simul', 'Saldo_Captacao_simul',
                      'DFC_Rec_Captacao_simul', 'Saldo_Comissoes_simul', 'Desp_Comiss_Capt_simul']

    Viabilidade = Viabilidade.drop(columns=cols_para_excl)
    Viabilidade.loc[0, 'Desp_PISCOFINS'] = -(((Viabilidade.loc[0,'Receita_Juros'] + Viabilidade.loc[0,'Desp_Captacao'] + Viabilidade.loc[0,'Receita_TC']) * aliq_PISCOFINS))
    Viabilidade.loc[0, 'LAIR'] = (Viabilidade.loc[0, 'Receita_Juros'] + Viabilidade.loc[0, 'Receita_TC'] + Viabilidade.loc[0, 'Desp_Captacao'] +
                                  Viabilidade.loc[0, 'Desp_PISCOFINS'] + Viabilidade.loc[0, 'Desp_ISS'] + Viabilidade.loc[0, 'Desp_Comiss_Flat'] +
                                  Viabilidade.loc[0, 'Desp_Comiss_Dif'] + Viabilidade.loc[0, 'Desp_Comiss_Capt'] + Viabilidade.loc[0, 'Desp_Mensais'] +
                                  Viabilidade.loc[0, 'Desp_Outras'] + Viabilidade.loc[0, 'DespPDD'] + Viabilidade.loc[0, 'RevPDD'])

    Viabilidade.loc[0, 'Fiscal_Resultado'] = Viabilidade.loc[0, 'LAIR'] - Viabilidade.loc[0, 'DespPDD'] - Viabilidade.loc[0, 'RevPDD'] + Viabilidade.loc[0, 'DedutPeriodo']

    if Viabilidade.loc[0, 'Fiscal_Resultado'] < 0:
        Viabilidade.loc[0, 'Desp_IR_CSLL'] = 0.0
        Viabilidade.loc[0, 'Fiscal_Preju_Acum'] += Viabilidade.loc[0, 'Fiscal_Resultado']
    else:
        Viabilidade.loc[0, 'Desp_IR_CSLL'] = Viabilidade.loc[0, 'Fiscal_Resultado'] * aliq_IRCSLL

    Viabilidade.loc[0, 'Resultado_Liquido'] = Viabilidade.loc[0, 'LAIR'] + Viabilidade.loc[0, 'Desp_IR_CSLL']
    Viabilidade.loc[:, Viabilidade.columns != 'Data'] = Viabilidade.loc[:, Viabilidade.columns != 'Data'].fillna(0)

    df=Viabilidade.copy()

    for idx in df.index[1:]:

        df.at[idx, 'DFC_Pgto_PISCOFINS'] = df.at[idx-1, 'Desp_PISCOFINS']
        df.at[idx, 'DFC_Pgto_ISS'] = df.at[idx-1, 'Desp_ISS']
        df.at[idx, 'Pgto_IRCSLL'] = df.at[idx-1, 'Desp_IR_CSLL']

        Necess_Caixa = (df.at[idx, 'DFC_Rec_Parcelas'] + df.at[idx, 'DFC_Rec_TC'] + df.at[idx, 'DFC_Des_Emprestimos'] + df.at[idx, 'DFC_Pgto_PISCOFINS'] +
                        df.at[idx, 'DFC_Pgto_ISS'] + df.at[idx, 'DFC_Pgto_ComissFlat'] + df.at[idx, 'DFC_Pgto_ComissDif'] +
                        df.at[idx, 'DFC_Pgto_Mensais'] + df.at[idx, 'DFC_Pgto_Outras'] + df.at[idx, 'DFC_Pgto_IRCSLL'] +
                        df.at[idx, 'DFC_Rec_Captacao'] + df.at[idx,'DFC_Des_Captacao'] +
                        df.at[idx-1, 'DFC_Caixa_Acum'])

        df.at[idx, 'DFC_Necess_Caixa'] = Necess_Caixa

        if Necess_Caixa < 0:

            if base_capt == 'POS':
                Simul_CDB=CDBPos(P=-Necess_Caixa*(1+base_comiss_capt), df_i=CDI_Full, inicio=df.at[idx, 'Data'],
                                    liq=df.at[idx, 'Data'] + pd.DateOffset(months=base_prazo_capt), contrato='B', d_uteis=CDI_Full['Data'].tolist(),
                                    pct_index=base_pos_pct_capt, q=1, agg='S', freq_i='D', comiss=-Necess_Caixa*(base_comiss_capt))
            elif base_capt == 'PRE':
                Simul_CDB=CDBPre(P=-Necess_Caixa*(1+base_comiss_capt), inicio=df.at[idx, 'Data'],
                                    liq=df.at[idx, 'Data'] + pd.DateOffset(months=base_prazo_capt), contrato='B', 
                                    i=base_pre, q=1, agg='S', freq_i='A', comiss=-Necess_Caixa*(base_comiss_capt))
            Simul_CDB = Simul_CDB[['Ano', 'Mes', 'Parcela', 'Juros', 'Saldo', 'Captacao', 'Comissao', 'DespComissao']]

            Simul_CDB = Simul_CDB.rename(columns={'Captacao': 'DFC_Rec_Captacao', 'Parcela': 'DFC_Des_Captacao', 'DespComissao':'Desp_Comiss_Capt', 
                                          'Juros': 'Desp_Captacao', 'Saldo': 'Saldo_Captacao', 'Comissao': 'Saldo_Comissoes'})

            Simul_CDB['DFC_Des_Captacao'] = -Simul_CDB['DFC_Des_Captacao']
            Simul_CDB['Desp_Comiss_Capt'] = -Simul_CDB['Desp_Comiss_Capt']
            Simul_CDB['Desp_Captacao'] = -Simul_CDB['Desp_Captacao']

            df = pd.merge(df, Simul_CDB, on=['Ano', 'Mes'], how='outer', suffixes=('','_simul'))

            df.loc[:, df.columns != 'Data'] = df.loc[:, df.columns != 'Data'].fillna(0.0)

            df['DFC_Des_Captacao'] += df['DFC_Des_Captacao_simul']
            df['Desp_Captacao'] += df['Desp_Captacao_simul']
            df['Saldo_Captacao'] += df['Saldo_Captacao_simul']
            df['Saldo_Comissoes'] += df['Saldo_Comissoes_simul']
            df['Desp_Comiss_Capt'] += df['Desp_Comiss_Capt_simul']

            df['DFC_Rec_Captacao'] += df['DFC_Rec_Captacao_simul']

            cols_para_excl = ['DFC_Des_Captacao_simul', 'Desp_Captacao_simul', 'Saldo_Captacao_simul',
                              'DFC_Rec_Captacao_simul', 'Saldo_Comissoes_simul', 'Desp_Comiss_Capt_simul']

            df = df.drop(columns=cols_para_excl)

            del Simul_CDB

        else:
            df.at[idx, 'DFC_Necess_Caixa'] = 0.0

        FC_Liquido = (df.at[idx, 'DFC_Rec_Parcelas'] + df.at[idx, 'DFC_Rec_TC'] + df.at[idx, 'DFC_Des_Emprestimos'] + df.at[idx, 'DFC_Pgto_PISCOFINS'] +
                      df.at[idx, 'DFC_Pgto_ISS'] + df.at[idx, 'DFC_Pgto_IRCSLL'] + df.at[idx, 'DFC_Pgto_ComissFlat'] +
                      df.at[idx, 'DFC_Pgto_ComissDif'] + df.at[idx, 'DFC_Pgto_Mensais'] + df.at[idx, 'DFC_Pgto_Outras'] +
                      df.at[idx, 'DFC_Rec_Captacao'] + df.at[idx, 'DFC_Des_Captacao'])

        df.at[idx, 'DFC_FC_Liquido'] = FC_Liquido

        df.at[idx, 'DFC_Caixa_Acum'] = df.at[idx-1, 'DFC_Caixa_Acum'] + df.at[idx, 'DFC_FC_Liquido']

        PIS_COFINS = ((df.at[idx, 'Receita_Juros'] + df.at[idx, 'Desp_Captacao'] + df.at[idx, 'Receita_TC']) * aliq_PISCOFINS)
        if PIS_COFINS < 0:
            PIS_COFINS = 0.0
        ISS = (df.at[idx, 'Receita_TC'] * aliq_ISS)

        df.at[idx, 'Desp_PISCOFINS'] = -PIS_COFINS
        df.at[idx, 'Desp_ISS'] = -ISS

        df.at[idx, 'LAIR'] = (df.at[idx, 'Receita_Juros'] + df.at[idx, 'Receita_TC'] + df.at[idx, 'Desp_Captacao'] +
                                  df.at[idx, 'Desp_PISCOFINS'] + df.at[idx, 'Desp_ISS'] + df.at[idx, 'Desp_Comiss_Flat'] +
                                  df.at[idx, 'Desp_Comiss_Dif'] + df.at[idx, 'Desp_Comiss_Capt'] + df.at[idx, 'Desp_Mensais'] +
                                  df.at[idx, 'Desp_Outras'] + df.at[idx, 'DespPDD'] + df.at[idx, 'RevPDD'])

        df.at[idx, 'Fiscal_Resultado'] = df.at[idx, 'LAIR'] - df.at[idx, 'DespPDD'] - df.at[idx, 'RevPDD'] + df.at[idx, 'DedutPeriodo']

        #Se o resultado fiscal for negativo, o prejuízo fiscal é acumulado e não há despesa de IR/CSLL
        if df.at[idx, 'Fiscal_Resultado'] < 0:
            df.at[idx, 'Desp_IR_CSLL'] = 0.0
            df.at[idx, 'Fiscal_Preju_Acum'] += df.at[idx, 'Fiscal_Resultado']
        #Se o resultado fiscal for positivo, calcula primeiramente o limite de compensação
        else:
            Lim_Compens = df.at[idx, 'Fiscal_Resultado'] * -0.3
            #Maior valor (menos negativo) entre o limite de compensação e o prejuízo fiscal acumulado do período anterior
            df.at[idx, 'Fiscal_Compensacao'] = max(Lim_Compens, df.at[idx-1, 'Fiscal_Preju_Acum'])

            #Possíveis erros, onde a compensação fiscal fica positiva
            if df.at[idx, 'Fiscal_Compensacao'] > 0:
                df.at[idx, 'Fiscal_Compensacao'] = 0
            Result_Impostos = df.at[idx, 'Fiscal_Resultado'] + df.at[idx, 'Fiscal_Compensacao']
            df.at[idx, 'Desp_IR_CSLL'] = Result_Impostos * -aliq_IRCSLL

        df.at[idx, 'Fiscal_Preju_Acum'] = (df.at[idx-1, 'Fiscal_Preju_Acum'] - df.at[idx, 'Fiscal_Compensacao'])
        if df.at[idx, 'Fiscal_Resultado'] < 0:
            df.at[idx, 'Fiscal_Preju_Acum'] += df.at[idx, 'Fiscal_Resultado']


        df.at[idx, 'Resultado_Liquido'] = df.at[idx, 'LAIR'] + df.at[idx, 'Desp_IR_CSLL']

        #Possíveis erros, onde o prejuízo fiscal acumulado fica positivo
        if df.at[idx, 'Fiscal_Preju_Acum'] > 0:
            df.at[idx, 'Fiscal_Preju_Acum'] = 0.0

    # --------------------------------------------------

    # Verificar se há algum valor NA na coluna 'Data'
    if df['Data'].isna().any():

        # Remover todas as linhas com valores NA na coluna 'Data'
        df = df.dropna(subset=['Data'])

        # Selecionar o último valor da coluna 'Saldo_Captacao' e alocar na variável 'saldo_capt'
        saldo_capt = df['Saldo_Captacao'].iloc[-1]

        # Transformar o valor do último elemento da coluna 'Saldo_Captacao' em 0
        df.at[df.index[-1], 'Saldo_Captacao'] = 0

        # Diminuir este valor do último valor das colunas 'DFC_Necess_Caixa', 'DFC_FC_Liquido' e 'DFC_Caixa_Acum'
        df.at[df.index[-1], 'DFC_Necess_Caixa'] -= saldo_capt
        df.at[df.index[-1], 'DFC_FC_Liquido'] -= saldo_capt
        df.at[df.index[-1], 'DFC_Caixa_Acum'] -= saldo_capt

    # --------------------------------------------------

    df['Resultado_Liq_Acum'] = df['Resultado_Liquido'].cumsum()

    df=df[[#PERIODOS
        'Ano', 'Mes', 'Data',
        #DRE
        'Receita_Juros', 'Receita_TC', 'Desp_Captacao', 'Desp_PISCOFINS', 'Desp_ISS',
        'Desp_Comiss_Flat', 'Desp_Comiss_Dif', 'Desp_Comiss_Capt', 'Desp_Mensais', 'Desp_Outras',
        'DespPDD', 'RevPDD', 'DedutPeriodo', 'LAIR', 'Desp_IR_CSLL', 'Resultado_Liquido', 'Resultado_Liq_Acum',

        #BALANÇO
        'Saldo_Carteira', 'PDDAcum', 'DedutAcum', 'Dif_Temp', 'Saldo_Captacao', 'Saldo_Comissoes',

        #DFC
        'DFC_Rec_Parcelas', 'DFC_Rec_TC', 'DFC_Des_Emprestimos','DFC_Pgto_ComissFlat', 'DFC_Pgto_ComissDif', 'DFC_Pgto_Mensais',
        'DFC_Pgto_Outras', 'DFC_Pgto_PISCOFINS', 'DFC_Pgto_ISS', 'DFC_Pgto_IRCSLL', 'DFC_Des_Captacao', 'DFC_Rec_Captacao',
        'DFC_Necess_Caixa', 'DFC_FC_Liquido', 'DFC_Caixa_Acum',

        #APURAÇÃO IR/CSLL
        'Fiscal_Resultado', 'Fiscal_Preju_Acum', 'Fiscal_Compensacao']].copy()

    arred = [col for col in df.columns if col not in ['Ano', 'Mes', 'Data']]

    df[arred] = df[arred].round(2)

    return df
