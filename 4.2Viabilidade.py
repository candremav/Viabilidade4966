import streamlit as st
import streamlit.components.v1 as components
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import io
import numpy as np

from babel.numbers import format_currency

pd.options.display.float_format = '{:,.2f}'.format

from Funcoes_Viab4966 import Viab4966

# Lê a curva do CDI
df_cdi = pd.read_csv('7.9.9Juros_Pos.csv', parse_dates=['Data'])

st.set_page_config(page_title="Simulador de Viabilidade 4966", layout="wide")
st.title("Viabilidade de Contratos - Modelo 4966")

with st.sidebar:
    st.header("Parâmetros do Contrato")
    base_tipo = st.selectbox("Tipo de contrato", ['CONSIG', 'PESS', 'FGTS'], index=0)
    base_inad = st.number_input("Inadimplência por safra (%)", value=6.0, format="%.2f") / 100
    base_taxa = st.number_input("Taxa de juros mensal (%)", value=2.70, format="%.2f") / 100
    base_prazo = st.number_input("Prazo do contrato (meses)", value=48)
    base_periodos = st.number_input("Nº de safras (meses)", value=12)
    
    base_quantid = st.number_input("Contratos por Safra (Contratos)", value=1500)
    
    base_saldo = st.number_input("Ticket médio por contrato (R$)", value=3000.0)
    base_ini = st.date_input("Data inicial da simulação AAAA-MM-DD", value=datetime.today().date())
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
    base_desp_outras = st.number_input("Despesas variáveis por safra (R$)", value=10000.0, format="%.2f")

    st.header("Captação")
    base_capt = st.selectbox("Tipo de captação", ['PRE', 'POS'], index=0)
    base_prazo_capt = st.number_input("Prazo da captação (meses)", value=12)
    base_pre = st.number_input("Taxa de captação pré-fixada (anual %)", value=17.0, format="%.2f") / 100
    base_pos_pct_capt = st.number_input("Fator CDI p/ captação pós (% do CDI)", value=115.0, format="%.2f") / 100

# Parse dos valores de lista
def parse_input_list(txt):
    return list(map(float, txt.strip().split(',')))

if st.button("Executar Simulação"):
    try:
        df_resultado = Viab4966(
            base_tipo=base_tipo,
            base_inad=base_inad,
            base_taxa=base_taxa,
            base_prazo=base_prazo,
            base_periodos=base_periodos,
            base_quantid=base_quantid,
            base_saldo=base_saldo,
            base_ini=pd.to_datetime(base_ini),
            base_tc=base_tc,
            base_comiss_flat=base_comiss_flat,
            base_comiss_dif=base_comiss_dif,
            aliq_IRCSLL=aliq_IRCSLL,
            aliq_PISCOFINS=aliq_PISCOFINS,
            aliq_ISS=aliq_ISS,
            base_desp_mensal=base_desp_mensal,
            base_desp_outras=base_desp_outras,
            base_capt=base_capt,
            base_comiss_capt=0.01,
            base_prazo_capt=base_prazo_capt,
            base_pos_pct_capt=base_pos_pct_capt,
            base_pre=base_pre,
            cdi=df_cdi
        )

        st.success("Simulação executada com sucesso!")
        #st.subheader("Resultado da Viabilidade Financeira")
        #st.dataframe(df_resultado.drop(columns=['Data','Indic_Alav','Indic_ROAA', 'Indic_MargLiq']).round(0))

# ---------------------------------------------------------------------

        # --- Viabilidade Econômica ---
        #st.subheader("📊 Demonstração do Resultado Anual")

        st.markdown("""
                    **📊 Demonstração do Resultado Anual**
                    """)

        df_viab = df_resultado.groupby('Ano').agg(
            Receitas_Totais=('DRE_Rec_Total', 'sum'), Receitas_Juros=('Receita_Juros', 'sum'), Receitas_TC=('Receita_TC', 'sum'),
            Despesas_Totais=('DRE_Desp_Total', 'sum'), Despesas_Captacoes=('DRE_Desp_Captacao', 'sum'), Despesas_Impostos=('DRE_Desp_Impostos', 'sum'), 
            Despesas_Comissoes=('DRE_Desp_Comissoes', 'sum'),Despesas_Admin=('DRE_Desp_Admin', 'sum'), Desp_PDD=('DRE_Desp_PDD', 'sum'),LAIR=('LAIR', 'sum'),
            IR_CSLL=('Desp_IR_CSLL', 'sum'), Lucro=('Resultado_Liquido', 'sum'), Lucro_Acumulado=('Resultado_Liq_Acum', 'last')
        )

        # Transpor e renomear as linhas (agora elas são índice)
        df_dre = df_viab.T.rename(index={
            "Receitas_Totais": "Receita Total",
            "Receitas_Juros": " (+) Receita c/ Crédito",
            "Receitas_TC": " (+) Receita c/ Serviço",
            "Despesas_Totais": "Despesas Totais",
            "Despesas_Captacoes": " (-) Captação",
            "Despesas_Admin": " (-) Administrativas",
            "Despesas_Comissoes": " (-) Correspondentes",
            "Despesas_Impostos": " (-) Tributárias",
            "Desp_PDD": " (+/-) PDD",
            "LAIR": "Resultado Ex-IRPJ e CSLL",
            "IR_CSLL": " (-) IRPJ e CSLL",
            "Lucro": "Resultado Líquido",
            "Lucro_Acumulado": "Resultado Líquido Acumulado"
        })

        # Linhas a destacar em negrito
        linhas_negrito = {"Receita Total", "Despesas Totais", "Resultado Ex-IRPJ e CSLL", "Resultado Líquido", "Resultado Líquido Acumulado"}

        # Função para formatar valores numéricos
        def formatar(val):
            if pd.isna(val): return ""
            if val == 0: return "--"
            val_fmt = f"{abs(val):,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return f"({val_fmt})" if val < 0 else val_fmt

        # Aplicar a formatação numérica
        df_fmt = df_dre.copy()
        for col in df_fmt.columns:
            df_fmt[col] = df_fmt[col].apply(formatar)

        # Função para aplicar HTML por linha
        def estilo_linha(row, nome_linha):
            return [
                f'<span style="font-weight:bold; color:red">{val}</span>' if val.startswith("(") and nome_linha in linhas_negrito else
                f'<span style="font-weight:bold">{val}</span>' if nome_linha in linhas_negrito else
                f'<span style="color:red">{val}</span>' if val.startswith("(") else val
                for val in row
            ]

        # Construir o DataFrame HTML
        index_nomes = df_fmt.index.tolist()
        index_html = [f'<span style="font-weight:bold">{i}</span>' if i in linhas_negrito else i for i in index_nomes]
        html_data = [estilo_linha(row, nome_linha) for row, nome_linha in zip(df_fmt.values.tolist(), index_nomes)]
        df_html = pd.DataFrame(html_data, index=index_html, columns=df_fmt.columns)

        # Construir tabela em HTML
        html_table = "<thead><tr><th></th>" + "".join([f"<th style='text-align: center'>{col}</th>" for col in df_html.columns]) + "</tr></thead><tbody>"
        for i, row in df_html.iterrows():
            html_table += f"<tr><td>{i}</td>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
        html_table += "</tbody>"

        # Estilo e exibição final no Streamlit
        tabela_html = f"""
        <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: "Times New Roman", Times, serif;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 6px;
            text-align: center;
        }}
        th:first-child, td:first-child {{
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
        }}
        </style>
        <table>{html_table}</table>
        """

        components.html(tabela_html, height=450, scrolling=True)

        #st.dataframe(df_viab.round(0).T)

        # --- Receitas ---
        st.markdown("📁 <b>Receitas</b>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>Receita de Juros:</b> {format_currency(df_resultado['Receita_Juros'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>Receita de Serviços:</b> {format_currency(df_resultado['Receita_TC'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)

        # --- Despesas Gerais ---
        st.markdown("📁 <b>Despesas Gerais</b>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>Captação:</b> {format_currency(df_resultado['DRE_Desp_Captacao'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>Comissões:</b> {format_currency(df_resultado['DRE_Desp_Comissoes'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>Administrativas:</b> {format_currency(df_resultado['DRE_Desp_Admin'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>PDD:</b> {format_currency(df_resultado['DRE_Desp_PDD'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)

        # --- Impostos ---
        st.markdown("📁 <b>Impostos</b>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>PIS/COFINS/ISS:</b> {format_currency(df_resultado['DRE_Desp_Impostos'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)
        st.markdown(f"<small>&emsp;🔹 <b>IR/CSLL:</b> {format_currency(df_resultado['Desp_IR_CSLL'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)

        # --- Resultado Líquido ---
        st.markdown(f"<small><b>✅ Resultado Líquido:</b> {format_currency(df_resultado['Resultado_Liquido'].sum(), 'BRL', locale='pt_BR')}</small>", unsafe_allow_html=True)


# ---------------------------------------------------------------------

        # --- Ativos e Passivos ---
        #st.subheader("📈 Ativos e Passivos")

        st.markdown("""
                    
                    **📈 Ativos e Passivos**
                    """)

        # Agrupamento e transposição
        df_atv_pass = df_resultado.groupby('Ano').agg(
            Carteira=('Saldo_Carteira', 'last'),
            PDD=('PDDAcum', 'last'),
            Carteira_Liquida=('Saldo_Cart_Liq', 'last'),
            Originacoes=('DFC_Des_Emprestimos', lambda x: -x.sum()),
            Depositos=('Saldo_Captacao', 'last'),
            Captacoes=('DFC_Rec_Captacao', lambda x: -x.sum()),
            Caixa=('DFC_Caixa_Acum', 'last')
        ).T.rename(index={
            'Carteira': 'Carteira Bruta',
            'PDD': 'PDD',
            'Carteira_Liquida': 'Carteira Líquida',
            'Originacoes': 'Originações',
            'Depositos': 'Depósitos',
            'Captacoes': 'Captações',
            'Caixa': 'Caixa'
        })

        # Linhas a destacar em negrito
        linhas_negrito_atv = {"Carteira Bruta", "Carteira Líquida", "Caixa"}

        # Aplicar a formatação numérica
        df_fmt_atv = df_atv_pass.copy()
        for col in df_fmt_atv.columns:
            df_fmt_atv[col] = df_fmt_atv[col].apply(formatar)

        # Estilo condicional
        def estilo_linha_atv(row, nome_linha):
            return [
                f'<span style="font-weight:bold; color:red">{val}</span>' if val.startswith("(") and nome_linha in linhas_negrito_atv else
                f'<span style="font-weight:bold">{val}</span>' if nome_linha in linhas_negrito_atv else
                f'<span style="color:red">{val}</span>' if val.startswith("(") else val
                for val in row
            ]

        # Construir HTML
        index_nomes_atv = df_fmt_atv.index.tolist()
        index_html_atv = [f'<span style="font-weight:bold">{i}</span>' if i in linhas_negrito_atv else i for i in index_nomes_atv]
        html_data_atv = [estilo_linha_atv(row, nome_linha) for row, nome_linha in zip(df_fmt_atv.values.tolist(), index_nomes_atv)]
        df_html_atv = pd.DataFrame(html_data_atv, index=index_html_atv, columns=df_fmt_atv.columns)

        html_table_atv = "<thead><tr><th></th>" + "".join([f"<th style='text-align: center'>{col}</th>" for col in df_html_atv.columns]) + "</tr></thead><tbody>"
        for i, row in df_html_atv.iterrows():
            html_table_atv += f"<tr><td>{i}</td>" + "".join([f"<td>{cell}</td>" for cell in row]) + "</tr>"
        html_table_atv += "</tbody>"

        # Estilo final reaproveitado
        tabela_html_atv = f"""
        <style>
        table {{
            border-collapse: collapse;
            width: 100%;
            font-family: "Times New Roman", Times, serif;
            font-size: 13px;
        }}
        th, td {{
            border: 1px solid #ccc;
            padding: 6px;
            text-align: center;
        }}
        th:first-child, td:first-child {{
            text-align: left;
        }}
        th {{
            background-color: #f0f0f0;
        }}
        </style>
        <table>{html_table_atv}</table>
        """

        # Exibir no Streamlit
        components.html(tabela_html_atv, height=250, scrolling=True)
        #st.dataframe(df_atv_pass.round(0).T)

# ---------------------------------------------------------------------

        # --- Indicadores Financeiros ---
        #st.subheader("📌 Indicadores Financeiros")
        
        # Legenda dos indicadores
        st.markdown("""
                    **📌 Indicadores Financeiros**  
                    - **Alavancagem:** Depósitos Totais / Carteira Líquida 
                    - **ROAA (%):** Lucro Líquido Anualizado / Carteira Líquida Média  
                    - **Margem Líquida (%):** Lucro Líquido / Receita Total
                    """)
        
        df_resultado['Indic_Alav'] = (df_resultado['Saldo_Captacao'] / df_resultado['Saldo_Cart_Liq'].replace(0, pd.NA)).fillna(0).replace([np.inf, -np.inf], 0)

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
        df_indic = df_indic[['Indic_Alav', 'Indic_ROAA%', 'Indic_MargLiq%']].copy()
        df_indic.columns = ['Alavancagem', 'ROAA (%)', 'Margem Líquida (%)']
        
        # --- TABELA HTML DOS INDICADORES FINANCEIROS ---

        # Copiar e formatar os valores
        df_fmt_indic = df_indic.copy()

        # Formatar valores numéricos e destacar negativos
        for col in df_fmt_indic.columns:
            df_fmt_indic[col] = df_fmt_indic[col].apply(
                lambda v: f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_fmt_indic[col] = df_fmt_indic[col].apply(
                lambda v: f'<span style="color:red">({v})</span>' if "-" in v or "(" in v else v)

        # Transpor para ter anos como índice e indicadores como colunas
        df_fmt_indic = df_fmt_indic.T

        # Construir a tabela com anos nas linhas
        tabela_indic = "<thead><tr><th>Ano</th>" + "".join(
            [f"<th style='text-align: center'>{col}</th>" for col in df_fmt_indic.columns]) + "</tr></thead><tbody>"
        for ano in df_fmt_indic.index:
            tabela_indic += f"<tr><td><b>{ano}</b></td>" + "".join(
                [f"<td>{df_fmt_indic.at[ano, indicador]}</td>" for indicador in df_fmt_indic.columns]) + "</tr>"
        tabela_indic += "</tbody>"

        # Renderização final
        st.markdown(f"""
        <table style='border-collapse: collapse; width: 100%; font-family: "Times New Roman"; font-size: 12px; border-color: green'>
            {tabela_indic}
        </table>
        """, unsafe_allow_html=True)

        #st.dataframe(df_indic.T)

        st.markdown(f"&emsp;🔹 **Margem Líquida Total:** {(df_resultado['Resultado_Liquido'].sum()/df_resultado['DRE_Rec_Total'].sum())* 100:.2f}%".replace(".", ","))
        st.markdown(f"&emsp;🔹 **ROAA Médio:** {(df_resultado['Resultado_Liquido'].sum()/len(df_resultado)*12/df_resultado['Saldo_Cart_Liq'].mean())* 100:.2f}%".replace(".", ","))

# ---------------------------------------------------------------------

        # --- Payback ---
        df_sorted = df_resultado.sort_values(['Ano', 'Mes']).reset_index(drop=True)
        payback = None
        for i in range(len(df_sorted)):
            if df_sorted.loc[i, 'DFC_Caixa_Acum'] >= 1:
                if (df_sorted.loc[i:, 'DFC_Caixa_Acum'] >= 1).all():
                    payback = i
                    break

# ---------------------------------------------------------------------

        # --- Breakeven ---
        breakeven = None
        for i in range(len(df_sorted)):
            if df_sorted.loc[i, 'Resultado_Liq_Acum'] >= 1:
                if (df_sorted.loc[i:, 'Resultado_Liq_Acum'] >= 1).all():
                    breakeven = i
                    break

        st.markdown("""
                    **📍 Retornos no Tempo**
                    """)

        #st.subheader("📍 Retornos no Tempo")
        st.write(f"✅ **Payback:** {payback} meses" if payback is not None else "❌ O caixa nunca se torna permanentemente positivo.")
        st.write(f"✅ **Breakeven:** {breakeven} meses" if breakeven is not None else "❌ O breakeven nunca é alcançado.")

        # --- Download em Excel com múltiplas abas ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_resultado.to_excel(writer, index=False, sheet_name='Simulacao')
            df_viab.to_excel(writer, sheet_name='Viabilidade')
            df_indic.to_excel(writer, sheet_name='Indicadores')
            df_atv_pass.to_excel(writer, sheet_name='Ativos_Passivos')
        st.download_button(
            label="📊 Baixar Resultado em Excel",
            data=output.getvalue(),
            file_name="Viabilidade.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Erro na simulação: {e}")