import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import io
import numpy as np

from Funcoes_Viab4966 import Viab4966

# Lê a curva do CDI
df_cdi = pd.read_csv('7.9.9Juros_Pos.csv', parse_dates=['Data'])

st.set_page_config(page_title="Simulador de Viabilidade 4966", layout="wide")
st.title("Viabilidade de Contratos - Modelo 4966")

with st.sidebar:
    st.header("Parâmetros do Contrato")
    base_tipo = st.selectbox("Tipo de contrato", ['CONSIG', 'PESS', 'FGTS'], index=0)
    base_inad = st.number_input("Inadimplência mensal esperada (%)", value=6.0, format="%.2f") / 100
    base_taxa = st.number_input("Taxa de juros mensal (%)", value=2.70, format="%.2f") / 100
    base_prazo = st.number_input("Prazo do contrato (meses)", value=96)
    base_periodos = st.number_input("Nº de safras (meses)", value=12)
    
    contratos_safra_unit = st.number_input("Contratos por Safra (Contratos)", value=1500)
    despesas_outras_unit = st.number_input("Despesa variável por Safra (R$)", value=1000.0)
    
    base_saldo = st.number_input("Ticket médio por contrato (R$)", value=3000.0)
    base_ini = st.date_input("Data inicial da simulação", value=datetime.today().date())
    base_tc = st.number_input("Taxa de cadastro por contrato (R$)", value=50.0)

    st.header("Comissões")
    base_comiss_flat = st.number_input("Comissão flat por contrato (%)", value=5.0, format="%.2f") / 100
    base_comiss_dif = st.number_input("Comissão diferida por parcela (%)", value=1.0, format="%.2f") / 100

    st.header("Alíquotas")
    aliq_IRCSLL = st.number_input("IRPJ + CSLL (%)", value=40.0, format="%.2f") / 100
    aliq_PISCOFINS = st.number_input("PIS + COFINS (%)", value=4.65, format="%.2f") / 100
    aliq_ISS = st.number_input("ISS (%)", value=5.0, format="%.2f") / 100

    st.header("Despesas Operacionais")
    base_desp_mensal = st.number_input("Despesas fixas mensais (R$)", value=15000.0)

    st.header("Captação")
    base_capt = st.selectbox("Tipo de captação", ['POS', 'PRE'], index=0)
    base_comiss_capt = st.number_input("Comissão de captação (%)", value=4.0, format="%.2f") / 100
    base_prazo_capt = st.number_input("Prazo da captação (meses)", value=12)
    base_pos_pct_capt = st.number_input("Fator CDI p/ captação pós (% do CDI)", value=115.0, format="%.2f") / 100
    base_pre = st.number_input("Taxa de captação pré-fixada (anual %)", value=17.0, format="%.2f") / 100

# Transformações automáticas para listas
base_quantid = [contratos_safra_unit] * int(base_periodos)
base_desp_outras = [despesas_outras_unit] * int(base_periodos)

# Parse dos valores de lista
def parse_input_list(txt):
    return list(map(float, txt.strip().split(',')))

if st.button("Executar Simulação"):
    try:
        base_quantid_list = base_quantid
        base_desp_outras_list = base_desp_outras

        df_resultado = Viab4966(
            base_tipo=base_tipo,
            base_inad=base_inad,
            base_taxa=base_taxa,
            base_prazo=base_prazo,
            base_periodos=base_periodos,
            base_quantid=base_quantid_list,
            base_saldo=base_saldo,
            base_ini=pd.to_datetime(base_ini),
            base_tc=base_tc,
            base_comiss_flat=base_comiss_flat,
            base_comiss_dif=base_comiss_dif,
            aliq_IRCSLL=aliq_IRCSLL,
            aliq_PISCOFINS=aliq_PISCOFINS,
            aliq_ISS=aliq_ISS,
            base_desp_mensal=base_desp_mensal,
            base_desp_outras=base_desp_outras_list,
            base_capt=base_capt,
            base_comiss_capt=base_comiss_capt,
            base_prazo_capt=base_prazo_capt,
            base_pos_pct_capt=base_pos_pct_capt,
            base_pre=base_pre,
            cdi=df_cdi
        )

        st.success("Simulação executada com sucesso!")
        st.subheader("Resultado da Viabilidade Financeira")
        st.dataframe(df_resultado)

        # --- Viabilidade Econômica ---
        st.subheader("📊 Viabilidade Econômica")
        df_viab = df_resultado.groupby('Ano').agg(
            Receitas_Totais=('DRE_Rec_Total', 'sum'),
            Despesas_Captacoes=('DRE_Desp_Captacao', 'sum'),
            Despesas_Impostos=('DRE_Desp_Impostos', 'sum'),
            Despesas_Comissoes=('DRE_Desp_Comissoes', 'sum'),
            Outras_Despesas=('DRE_Desp_Outras', 'sum'),
            LAIR=('LAIR', 'sum'),
            Lucro=('Resultado_Liquido', 'sum')
        )
        st.dataframe(df_viab)

        # --- Ativos e Passivos ---
        st.subheader("📈 Ativos e Passivos")
        df_atv_pass = df_resultado.groupby('Ano').agg(
            Carteira=('Saldo_Carteira', 'last'),
            PDD=('PDDAcum', 'last'),
            Carteira_Liquida=('Saldo_Cart_Liq', 'last'),
            Originacoes=('DFC_Des_Emprestimos', lambda x: -x.sum()),
            Depositos=('Saldo_Captacao', 'last'),
            Captacoes=('DFC_Rec_Captacao', lambda x: -x.sum()),
            Caixa=('DFC_Caixa_Acum', 'last')
        )
        st.dataframe(df_atv_pass)

        # --- Indicadores Financeiros ---
        st.subheader("📌 Indicadores Financeiros")
        df_resultado['Indic_Alav'] = (df_resultado['Saldo_Cart_Liq'] / df_resultado['Saldo_Captacao'].replace(0, pd.NA)).fillna(0).replace([np.inf, -np.inf], 0)

        df_indic = df_resultado[['Mes', 'Ano', 'Saldo_Cart_Liq', 'Saldo_Captacao', 'Indic_Alav', 'Resultado_Liquido', 'DRE_Rec_Total']].copy()
        df_indic = df_indic.groupby('Ano').agg(
            Carteira_Ult=('Saldo_Cart_Liq', 'last'),
            Carteira_Med=('Saldo_Cart_Liq', 'mean'),
            Result_Liq=('Resultado_Liquido', 'last'),
            Rec_Total=('DRE_Rec_Total', 'last'),
            Indic_Alav=('Indic_Alav', 'last'),
            Meses=('Mes', 'count')
        )
        df_indic['Indic_ROAA%'] = df_indic['Result_Liq'] * (1200 / df_indic['Meses']) / df_indic['Carteira_Med']
        df_indic['Indic_MargLiq%'] = df_indic['Result_Liq'] * 100 / df_indic['Rec_Total']
        st.dataframe(df_indic[['Indic_Alav', 'Indic_ROAA%', 'Indic_MargLiq%']])

        # --- Payback ---
        df_sorted = df_resultado.sort_values(['Ano', 'Mes']).reset_index(drop=True)
        payback = None
        for i in range(len(df_sorted)):
            if df_sorted.loc[i, 'DFC_Caixa_Acum'] >= 1:
                if (df_sorted.loc[i:, 'DFC_Caixa_Acum'] >= 1).all():
                    payback = i
                    break

        # --- Breakeven ---
        breakeven = None
        for i in range(len(df_sorted)):
            if df_sorted.loc[i, 'Resultado_Liq_Acum'] >= 1:
                if (df_sorted.loc[i:, 'Resultado_Liq_Acum'] >= 1).all():
                    breakeven = i
                    break

        st.subheader("📍 Retornos no Tempo")
        st.write(f"✅ **Payback:** {payback} meses" if payback is not None else "❌ O caixa nunca se torna permanentemente positivo.")
        st.write(f"✅ **Breakeven:** {breakeven} meses" if breakeven is not None else "❌ O breakeven nunca é alcançado.")

        # --- Download em Excel com múltiplas abas ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Simulacao')
            viabilidade.to_excel(writer, sheet_name='Viabilidade')
            ativos_passivos.to_excel(writer, sheet_name='Ativos_Passivos')
        st.download_button(
            label="📊 Baixar Resultado em Excel",
            data=output.getvalue(),
            file_name="resultado_viabilidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro na simulação: {e}")