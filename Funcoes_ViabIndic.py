
import pandas as pd
import matplotlib.pyplot as plt

def ViabIndic(df_resultado):
    indicadores = {}

    # Viabilidade Econômica
    viabilidade = df_resultado.groupby('Ano').agg(
        Receitas_Totais=('DRE_Rec_Total', 'sum'),
        Despesas_Captacoes=('DRE_Desp_Captacao', 'sum'),
        Despesas_Impostos=('DRE_Desp_Impostos', 'sum'),
        Despesas_Comissoes=('DRE_Desp_Comissoes', 'sum'),
        Outras_Despesas=('DRE_Desp_Outras', 'sum'),
        LAIR=('LAIR', 'sum'),
        Lucro=('Resultado_Liquido', 'sum')
    )
    indicadores['viabilidade'] = viabilidade

    # Ativos e Passivos
    ativos_passivos = df_resultado.groupby('Ano').agg(
        Carteira=('Saldo_Carteira', 'last'),
        PDD=('PDDAcum', 'last'),
        Originacoes=('DFC_Des_Emprestimos', lambda x: -x.sum()),
        Depositos=('Saldo_Captacao', 'last'),
        Captacoes=('DFC_Rec_Captacao', lambda x: -x.sum()),
        Caixa=('DFC_Caixa_Acum', 'last')
    )
    indicadores['ativos_passivos'] = ativos_passivos

    # Payback
    df_sorted = df_resultado.sort_values(['Ano', 'Mes']).reset_index(drop=True)
    payback = None
    for i in range(len(df_sorted)):
        if df_sorted.loc[i, 'DFC_Caixa_Acum'] >= 1:
            if (df_sorted.loc[i:, 'DFC_Caixa_Acum'] >= 1).all():
                payback = i
                break
    indicadores['payback'] = payback

    # Breakeven
    breakeven = None
    for i in range(len(df_sorted)):
        if df_sorted.loc[i, 'Resultado_Liq_Acum'] >= 1:
            if (df_sorted.loc[i:, 'Resultado_Liq_Acum'] >= 1).all():
                breakeven = i
                break
    indicadores['breakeven'] = breakeven

    return indicadores
