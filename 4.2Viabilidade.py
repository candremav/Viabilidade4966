import streamlit as st
import pandas as pd
from datetime import datetime

from Funcoes_Viab4966 import Viab4966
from Funcoes_ViabIndic import ViabIndic

# Lê a curva do CDI
df_cdi = pd.read_csv('7.9.9Juros_Pos.csv', parse_dates=['Data'])

st.set_page_config(page_title="Simulador de Viabilidade 4966", layout="wide")
st.title("Viabilidade de Contratos - Modelo 4966")

with st.sidebar:
    st.header("Parâmetros do Contrato")
    base_tipo = st.selectbox("Tipo de contrato", ['CONSIG', 'PESS', 'FGTS'], index=0)
    base_inad = st.number_input("Inadimplência mensal esperada (%)", value=0.06, format="%0.4f")
    base_taxa = st.number_input("Taxa de juros mensal (%)", value=0.027, format="%0.4f")
    base_prazo = st.number_input("Prazo do contrato (meses)", value=96)
    base_periodos = st.number_input("Nº de safras mensais", value=12)
    base_quantid = st.text_input("Lista de contratos por safra", value="850,1020,1190,1360,1530,1700,1700,1700,1700,1700,1700,1700")
    base_saldo = st.number_input("Ticket médio por contrato (R$)", value=3000.0)
    base_ini = st.date_input("Data inicial da simulação", value=datetime.today())
    base_tc = st.number_input("Taxa de cadastro por contrato (R$)", value=50.0)

    st.header("Comissões")
    base_comiss_flat = st.number_input("Comissão flat por contrato (%)", value=0.05)
    base_comiss_dif = st.number_input("Comissão diferida por parcela (%)", value=0.01)

    st.header("Alíquotas")
    aliq_IRCSLL = st.number_input("IRPJ + CSLL", value=0.4)
    aliq_PISCOFINS = st.number_input("PIS + COFINS", value=0.0465)
    aliq_ISS = st.number_input("ISS", value=0.05)

    st.header("Despesas Operacionais")
    base_desp_mensal = st.number_input("Despesas fixas mensais (R$)", value=15000.0)
    base_desp_outras = st.text_input("Despesas variáveis por safra (R$)", value="0,0,0,0,0,0,0,0,0,0,0,1000")

    st.header("Captação")
    base_capt = st.selectbox("Tipo de captação", ['POS', 'PRE'], index=0)
    base_comiss_capt = st.number_input("Comissão de captação (%)", value=0.04)
    base_prazo_capt = st.number_input("Prazo da captação (meses)", value=12)
    base_pos_pct_capt = st.number_input("Fator CDI p/ captação pós", value=1.15)
    base_pre = st.number_input("Taxa de captação pré-fixada (anual)", value=0.17)

# Parse dos valores de lista
def parse_input_list(txt):
    return list(map(float, txt.strip().split(',')))

if st.button("Executar Simulação"):
    try:
        base_quantid_list = parse_input_list(base_quantid)
        base_desp_outras_list = parse_input_list(base_desp_outras)

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
        st.dataframe(df_resultado.head(20))

        # Gráfico de linha - Saldo ao longo do tempo
        st.subheader("Evolução do Saldo e Juros")
        fig, ax = plt.subplots()
        df_resultado.groupby('Data')[['Saldo', 'Juros']].sum().plot(ax=ax)
        ax.set_ylabel("R$")
        ax.set_xlabel("Data")
        ax.set_title("Fluxos Mensais Consolidados")
        st.pyplot(fig)

        # Indicadores
        indicadores = indicadores_chave(df_resultado)

        st.subheader("📊 Viabilidade Econômica")
        st.dataframe(indicadores['viabilidade'])

        st.subheader("📈 Ativos e Passivos")
        st.dataframe(indicadores['ativos_passivos'])

        st.subheader("🔹 Indicadores-Chave")
        st.write(f"✅ **Payback:** {indicadores['payback']} meses" if indicadores['payback'] is not None else "❌ O caixa nunca se torna permanentemente positivo.")
        st.write(f"✅ **Breakeven:** {indicadores['breakeven']} meses" if indicadores['breakeven'] is not None else "❌ O breakeven nunca é alcançado.")

        # Download Excel
        csv = df_resultado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📅 Baixar Resultado em CSV",
            data=csv,
            file_name='resultado_viabilidade.csv',
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Erro na simulação: {e}")
