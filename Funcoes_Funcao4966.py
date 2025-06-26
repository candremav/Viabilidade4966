
def Funcao4966(data_base, contrato, saldo, data_max, atraso, tx_juros, datas_pmt, vf_pmt, vp_pmt, classif='C5', consig='N', comiss=0.0, inad='N', datas_liq=None, cessao=None, aquis=None, vlr_cessao=None, vlr_aquis=None, vlr_curva=None, padrao_atraso=None):

    import pandas as pd
    import numpy as np
    import numpy_financial as npf
    from datetime import datetime

    n = len(datas_pmt)

    # Cálculo da taxa de juros diária
    tx_juros_dia = ((1 + tx_juros) ** (1 / 30)) - 1

    # Caso as datas de liquidação não sejam fornecidas, as datas de pagamento serão usadas
    datas_pmt_efetivo = datas_pmt

    ### ---------------------------------------------------------------------------------
    ### CÁLCULO DOS JUROS POR PARCELA ---------------------------------------------------
    ### ---------------------------------------------------------------------------------

    ### 1. QUANDO HÁ ATRASO, MAS AS PARCELAS SERÃO PAGAS E NÃO INCIDEM JUROS E MULTA ----

    if inad == 'N':  # Verifica se não há inadimplência

        if atraso > 0:
            # Criação do DataFrame de Juros
            df_juros = pd.DataFrame({
                'inicio': [data_base] * n,  # Data base do cálculo
                'datas_pmt_efetivo': datas_pmt_efetivo,  # Datas de pagamento efetivas
                'vf_pmt': vf_pmt,  # Valor futuro de cada pagamento
                'vp_pmt': vp_pmt  # Valor presente de cada pagamento
                })

            # Ajuste do saldo com base nos pagamentos realizados antes da data base
            saldo_aj = saldo - df_juros[df_juros['datas_pmt_efetivo'] < pd.to_datetime(data_base)]['vp_pmt'].sum()

            # Resetar o atraso, já que os pagamentos realizados ajustam o saldo
            atraso = 0

            # Filtrar para manter apenas os pagamentos que ocorrem após ou na data base
            df_juros = df_juros[df_juros['datas_pmt_efetivo'] >= pd.to_datetime(data_base)]

            # DataFrame final para armazenar os cálculos de juros diários
            df_juros_final = pd.DataFrame()

            # Lista para armazenar os DataFrames de cada iteração
            df_list = []

            # Loop para calcular os juros diários para cada parcela
            for i, row in df_juros.iterrows():
                parcelas_inicio = row['inicio']
                parcelas_fim = row['datas_pmt_efetivo']

                # Criação de uma série de datas diárias entre o início e o fim do período da parcela
                datas_diarias = pd.date_range(start=parcelas_inicio, end=parcelas_fim, freq='D')

                # DataFrame para armazenar os dados diários de juros da parcela
                df_juros_diarios = pd.DataFrame({
                    'datas': datas_diarias,  # Datas diárias
                    'vp_pmt': row['vp_pmt'],  # Valor presente da parcela
                    'vf_pmt': row['vf_pmt']  # Valor futuro da parcela
                })

                # Cálculo da diferença em dias, garantindo que não seja negativa
                df_juros_diarios['dif_diaria'] = (df_juros_diarios['datas'] - parcelas_inicio).dt.days
                df_juros_diarios['dif_diaria'] = np.where(df_juros_diarios['dif_diaria'] < 0, 0, df_juros_diarios['dif_diaria'])

                max_dif_diaria = df_juros_diarios['dif_diaria'].max()
                if max_dif_diaria > 0:
                    df_juros_diarios['taxa'] = (df_juros_diarios['vf_pmt'] / df_juros_diarios['vp_pmt']) ** (1 / max_dif_diaria) - 1
                else:
                    # Defina a taxa como zero ou outro valor apropriado quando max_dif_diaria for 0
                    df_juros_diarios['taxa'] = 0

                # Atualização do valor presente pela taxa de juros e dias corridos
                df_juros_diarios['pmt'] = df_juros_diarios['vp_pmt'] * ((1 + df_juros_diarios['taxa']) ** df_juros_diarios['dif_diaria'])

                # Cálculo dos juros diários, ou seja, a diferença entre os pagamentos sucessivos
                df_juros_diarios['juros_dia'] = df_juros_diarios['pmt'].diff().fillna(0)

                # Armazenar o DataFrame na lista
                df_list.append(df_juros_diarios)

# ---------------------------------------------------------------------------------------
            # Verificar se a lista df_list não está vazia antes de concatenar
            if df_list:

                # Concatenar todos os DataFrames da lista de uma vez
                df_juros_final = pd.concat(df_list, ignore_index=True)

                # Agrupar os resultados por data e somar os valores de 'pmt' e 'juros_dia'
                df_juros_final_grouped = df_juros_final.groupby('datas').agg({
                    'pmt': 'sum', 
                    'juros_dia': 'sum'
                }).reset_index()

                # Ajustar o índice para facilitar visualização
                df_juros_final_grouped['datas_copy'] = df_juros_final_grouped['datas']
                df_juros_final_grouped.set_index('datas_copy', inplace=True)

                # Renomear as colunas do DataFrame final
                df_juros_final_grouped.columns = ['datas', 'valor_presente', 'juros_dia']
            else:
                # Caso a lista df_list esteja vazia, criar um DataFrame vazio
                df_juros_final_grouped = pd.DataFrame(columns=['datas', 'valor_presente', 'juros_dia'])
# ---------------------------------------------------------------------------------------

    ### 2. QUANDO NÃO HÁ ATRASO E AS PARCELAS SERÃO PAGAS -------------------------------

        else:
            # Criação do DataFrame de Juros
            df_juros = pd.DataFrame({
                'inicio': [data_base] * n,  # Data base do cálculo
                'datas_pmt_efetivo': datas_pmt_efetivo,  # Datas de pagamento efetivas
                'vf_pmt': vf_pmt,  # Valor futuro de cada pagamento
                'vp_pmt': vp_pmt  # Valor presente de cada pagamento
                })

            saldo_aj = saldo

            # DataFrame final para armazenar os cálculos de juros diários
            df_juros_final = pd.DataFrame()

            # Lista para armazenar os DataFrames de cada iteração
            df_list = []

            # Loop para calcular os juros diários para cada parcela
            for i, row in df_juros.iterrows():
                parcelas_inicio = row['inicio']
                parcelas_fim = row['datas_pmt_efetivo']

                # Criação de uma série de datas diárias entre o início e o fim do período da parcela
                datas_diarias = pd.date_range(start=parcelas_inicio, end=parcelas_fim, freq='D')

                # DataFrame para armazenar os dados diários de juros da parcela
                df_juros_diarios = pd.DataFrame({
                    'datas': datas_diarias,  # Datas diárias
                    'vp_pmt': row['vp_pmt'],  # Valor presente da parcela
                    'vf_pmt': row['vf_pmt']  # Valor futuro da parcela
                })

                # Cálculo da diferença em dias, garantindo que não seja negativa
                df_juros_diarios['dif_diaria'] = (df_juros_diarios['datas'] - parcelas_inicio).dt.days
                df_juros_diarios['dif_diaria'] = np.where(df_juros_diarios['dif_diaria'] < 0, 0, df_juros_diarios['dif_diaria'])

                max_dif_diaria = df_juros_diarios['dif_diaria'].max()
                if max_dif_diaria > 0:
                    df_juros_diarios['taxa'] = (df_juros_diarios['vf_pmt'] / df_juros_diarios['vp_pmt']) ** (1 / max_dif_diaria) - 1
                else:
                    # Defina a taxa como zero ou outro valor apropriado quando max_dif_diaria for 0
                    df_juros_diarios['taxa'] = 0

                # Atualização do valor presente pela taxa de juros e dias corridos
                df_juros_diarios['pmt'] = df_juros_diarios['vp_pmt'] * ((1 + df_juros_diarios['taxa']) ** df_juros_diarios['dif_diaria'])

                # Cálculo dos juros diários, ou seja, a diferença entre os pagamentos sucessivos
                df_juros_diarios['juros_dia'] = df_juros_diarios['pmt'].diff().fillna(0)

                # Armazenar o DataFrame na lista
                df_list.append(df_juros_diarios)

# ---------------------------------------------------------------------------------------
            # Verificar se a lista df_list não está vazia antes de concatenar
            if df_list:
                # Concatenar todos os DataFrames da lista de uma vez
                df_juros_final = pd.concat(df_list, ignore_index=True)

                # Agrupar os resultados por data e somar os valores de 'pmt' e 'juros_dia'
                df_juros_final_grouped = df_juros_final.groupby('datas').agg({
                    'pmt': 'sum', 
                    'juros_dia': 'sum'
                }).reset_index()

                # Ajustar o índice para facilitar visualização
                df_juros_final_grouped['datas_copy'] = df_juros_final_grouped['datas']
                df_juros_final_grouped.set_index('datas_copy', inplace=True)

                # Renomear as colunas do DataFrame final
                df_juros_final_grouped.columns = ['datas', 'valor_presente', 'juros_dia']
            else:
                # Caso a lista df_list esteja vazia, criar um DataFrame vazio
                df_juros_final_grouped = pd.DataFrame(columns=['datas', 'valor_presente', 'juros_dia'])
# ---------------------------------------------------------------------------------------

    ### 3. QUANDO HÁ ATRASO +90D E AS PARCELAS NÃO SERÃO PAGAS --------------------------

    if inad == 'S':  # Verifica se não há inadimplência

        saldo_aj = saldo

        if atraso > 90:
            # Criar um avanço diário das datas desde 'data_base' até o máximo valor de 'datas_pmt_efetivo'
            datas_diarias = pd.date_range(start=pd.to_datetime(data_base),
                                            end=pd.to_datetime(datas_pmt_efetivo).max(),
                                            freq='D')

            # Criar o DataFrame df_juros_final_grouped
            df_juros_final_grouped = pd.DataFrame({
                'datas': datas_diarias,  # Datas diárias do intervalo
                'valor_presente': [saldo] * len(datas_diarias),  # Repetir o valor de 'saldo' para todas as linhas
                'juros_dia': [0] * len(datas_diarias)  # Definir a coluna 'juros_dia' como zero
            })

    ### 4. QUANDO NÃO HÁ ATRASO +90D E AS PARCELAS NÃO SERÃO PAGAS ----------------------
    ### HÁ CÁLCULO DE MULTA E JUROS -----------------------------------------------------

        else:

            saldo_aj = saldo


            dias_de_juros = 90 - atraso

            # Criação do DataFrame de Juros
            df_juros = pd.DataFrame({
                'inicio': [data_base] * n,  # Data base do cálculo
                'datas_pmt_efetivo': datas_pmt_efetivo,  # Datas de pagamento efetivas
                'vf_pmt': vf_pmt,  # Valor futuro de cada pagamento
                'vp_pmt': vp_pmt  # Valor presente de cada pagamento
                })

            # DataFrame final para armazenar os cálculos de juros diários
            df_juros_final = pd.DataFrame()

            # Lista para armazenar os DataFrames de cada iteração
            df_list = []

            # Loop para calcular os juros diários para cada parcela
            for i, row in df_juros.iterrows():
                parcelas_inicio = row['inicio']

                # Calcular parcelas_fim como parcelas_inicio + dias_de_juros
                parcelas_fim = parcelas_inicio + pd.to_timedelta(dias_de_juros, unit='D')

                # Criação de uma série de datas diárias entre o início e o fim do período da parcela
                datas_diarias = pd.date_range(start=parcelas_inicio, end=parcelas_fim, freq='D')

                # DataFrame para armazenar os dados diários de juros da parcela
                df_juros_diarios = pd.DataFrame({
                    'datas': datas_diarias,  # Datas diárias
                    'vp_pmt': row['vp_pmt'],  # Valor presente da parcela
                    'vf_pmt': row['vf_pmt']  # Valor futuro da parcela
                })

                # Cálculo da diferença em dias, garantindo que não seja negativa
                df_juros_diarios['dif_diaria'] = (df_juros_diarios['datas'] - parcelas_inicio).dt.days

                # Atualização do valor presente pela taxa de juros e dias corridos
                df_juros_diarios['pmt'] = df_juros_diarios['vp_pmt'] * ((1 + tx_juros_dia) ** df_juros_diarios['dif_diaria'])

                # Cálculo dos juros diários, ou seja, a diferença entre os pagamentos sucessivos
                df_juros_diarios['juros_dia'] = df_juros_diarios['pmt'].diff().fillna(0)

                # Armazenar o DataFrame na lista
                df_list.append(df_juros_diarios)

# ---------------------------------------------------------------------------------------
            # Verificar se a lista df_list não está vazia antes de concatenar
            if df_list:
                # Concatenar todos os DataFrames da lista de uma vez
                df_juros_final = pd.concat(df_list, ignore_index=True)

                # Agrupar os resultados por data e somar os valores de 'pmt' e 'juros_dia'
                df_juros_final_grouped = df_juros_final.groupby('datas').agg({
                    'pmt': 'sum', 
                    'juros_dia': 'sum'
                }).reset_index()

                # Ajustar o índice para facilitar visualização
                df_juros_final_grouped['datas_copy'] = df_juros_final_grouped['datas']
                df_juros_final_grouped.set_index('datas_copy', inplace=True)

                # Renomear as colunas do DataFrame final
                df_juros_final_grouped.columns = ['datas', 'valor_presente', 'juros_dia']
            else:
                # Caso a lista df_list esteja vazia, criar um DataFrame vazio
                df_juros_final_grouped = pd.DataFrame(columns=['datas', 'valor_presente', 'juros_dia'])
# ---------------------------------------------------------------------------------------

    ### ---------------------------------------------------------------------------------
    ### CÁLCULO DA AMORTIZAÇÃO DO PREMIO POR PARCELA, QUANDO HOUVER ---------------------
    ### ---------------------------------------------------------------------------------

    # Verificar se há valores válidos em 'aquis'
    if pd.notna(aquis).all():

        n = len(vlr_cessao)

        # Criação do DataFrame
        df_premio = pd.DataFrame({
            'inicio': aquis,  # Preencher a coluna 'inicio' com a data de início em todas as linhas
            'datas': datas_pmt,  # Coluna com as datas mensais geradas
            'pmt': vlr_cessao,  # Preencher a coluna 'pmt' com o valor do pagamento em todas as linhas
            'pmt_origin': vlr_curva,
            'pmt_aquis': vlr_aquis
        })

        # Cálculo da diferença de dias entre 'datas' e 'inicio'
        df_premio['dias'] = (df_premio['datas'] - df_premio['inicio']).dt.days

        # Cálculo do prêmio
        df_premio['premio'] = df_premio['pmt_aquis'] - df_premio['pmt_origin']

        # Ajuste do pagamento pelo prêmio
        df_premio['pmt_premio'] = df_premio['pmt'] - df_premio['premio']

        # Cálculo do fator
        df_premio['fator_premio'] = (df_premio['pmt'] / df_premio['pmt_premio']) ** (360 / df_premio['dias'])
        df_premio['fator_origin'] = (df_premio['pmt'] / df_premio['pmt_origin']) ** (360 / df_premio['dias'])

        #### --------------- LOOP APROPRIAÇÃO PREMIO
        ### ---------------------------------------------------------------------------------

        # Lista para armazenar os DataFrames intermediários
        df_list_premio = []

        # Loop sobre cada linha do DataFrame df
        for i in range(len(df_premio)):
            # Selecionar a linha atual
            parcelas_inicio = df_premio.loc[i, 'inicio']
            parcelas_fim = df_premio.loc[i, 'datas']

            # Criar uma série de datas diárias de 'inicio' até 'fim'
            datas_diarias = pd.date_range(start=parcelas_inicio, end=parcelas_fim, freq='D')

            # Criar o novo DataFrame df_parcelas para a linha atual
            df_premio_parcelas = pd.DataFrame({
                'datas': datas_diarias,
                'fator_premio': df_premio.loc[i, 'fator_premio'],
                'pmt_premio': df_premio.loc[i, 'pmt_premio']
            })

            # Calcular a diferença diária
            df_premio_parcelas['dif_diaria'] = (df_premio_parcelas['datas'] - parcelas_inicio).dt.days

            # Calcular a apropriação do prêmio
            df_premio_parcelas['apropr_premio'] = ((df_premio_parcelas['fator_premio'] ** (df_premio_parcelas['dif_diaria'] / 360)) - 1) * df_premio_parcelas['pmt_premio']

            # Calcular o prêmio amortizado como a diferença linha a linha da apropriação do prêmio
            df_premio_parcelas['premio_amortizado'] = df_premio_parcelas['apropr_premio'].diff().fillna(0)
            df_premio_parcelas['saldo_a_apropr'] = df_premio_parcelas['premio_amortizado'].sum() - df_premio_parcelas['apropr_premio']

            # Armazenar o DataFrame na lista
            df_list_premio.append(df_premio_parcelas)

        # Concatenar todos os DataFrames da lista de uma vez
        df_premio_final = pd.concat(df_list_premio, ignore_index=True)

        # Agrupar o df_final por 'datas' e somar as colunas 'premio_amortizado' e 'saldo_a_apropr'
        df_premio_final_grouped = df_premio_final.groupby('datas').agg({'premio_amortizado': 'sum', 'saldo_a_apropr': 'sum'}).reset_index()

        df_premio_final_grouped['datas_copy'] = df_premio_final_grouped['datas']  # Fazer uma cópia da coluna
        df_premio_final_grouped.set_index('datas_copy', inplace=True)  # Definir o índice sem perder a cópia

        df_premio_final_grouped.columns=['datas', 'premio_dia', 'premio_a_apropriar']

        if inad == 'S':
            if atraso > 90:
                # Calcular data_limite como data_base - (atraso - 90)
                limite_premio = pd.to_datetime(data_base) - pd.to_timedelta(atraso - 90, unit='D')
            else:
                # Calcular data_limite como data_base + (90 - atraso)
                limite_premio = pd.to_datetime(data_base) + pd.to_timedelta(90 - atraso, unit='D')
            df_premio_final_grouped['premio_dia'] = np.where(df_premio_final_grouped['datas'] > limite_premio, 0.0,
                                                            df_premio_final_grouped['premio_dia'])
            df_premio_final_grouped.loc[df_premio_final_grouped['datas'] > limite_premio, 'premio_a_apropriar'] = np.nan
            df_premio_final_grouped['premio_a_apropriar'] = df_premio_final_grouped['premio_a_apropriar'].ffill()


    ### ---------------------------------------------------------------------------------
    ### INTEGRAÇÃO DO DATAFRAME ---------------------------------------------------------
    ### ---------------------------------------------------------------------------------


    # Gerar a coluna 'datas' com as datas diárias entre data_base e data_max
    datas = pd.date_range(start=data_base, end=data_max, freq='D')

    # Criar o DataFrame
    df_accruals = pd.DataFrame({'datas': datas})

    # Converter a coluna 'datas' de df_juros_final_grouped para datetime, caso necessário
    df_juros_final_grouped['datas'] = pd.to_datetime(df_juros_final_grouped['datas'])

    # Converter a coluna 'datas' de df_accruals para datetime, caso necessário
    df_accruals['datas'] = pd.to_datetime(df_accruals['datas'])

    df_accruals = pd.merge(df_accruals, df_juros_final_grouped, on='datas', how='left')

    # Verificar se há valores válidos em 'aquis'
    if pd.notna(aquis).all():
        # Se df_premio_final_grouped existe, fazer o merge
        df_accruals = pd.merge(df_accruals, df_premio_final_grouped, on='datas', how='left')
    else:
        # Se df_premio_final_grouped não existe, criar as colunas com valores zero
        df_accruals['premio_dia'] = 0.0
        df_accruals['premio_a_apropriar'] = 0.0

    # Substituir os NaNs na coluna 'juros_dia' por 0
    df_accruals['juros_dia'] = df_accruals['juros_dia'].fillna(0.0)

    # Substituir os NaNs na coluna 'valor_presente' pelo último valor válido (método forward fill)
    df_accruals['valor_presente'] = df_accruals['valor_presente'].ffill()

    ### ---------------------------------------------------------------------------------
    ### PROVISÃO ------------------------------------------------------------------------
    ### ---------------------------------------------------------------------------------


    # Controle de PDD
    df_atraso = pd.DataFrame({
        'DiasAtraso': range(0, 692),
        'C1': [0.014] * 15 + [0.035] * 16 + [0.045] * 30 + [0.050] * 30 + [0.100] * 30 + [0.145] * 30 + [0.190] * 30 + [0.235] * 30 + [0.280] * 30 + [0.325] * 30 + [0.370] * 30 + [0.415] * 30 + [0.460] * 30 + [0.505] * 30 + [0.550] * 30 + [0.595] * 30 + [0.640] * 30 + [0.685] * 30 + [0.730] * 30 + [0.775] * 30 + [0.820] * 30 + [0.865] * 30 + [0.910] * 30 + [0.955] * 30 + [1.000] * 1,
        'C2': [0.014] * 15 + [0.035] * 16 + [0.060] * 30 + [0.170] * 30 + [0.334] * 30 + [0.368] * 30 + [0.402] * 30 + [0.436] * 30 + [0.470] * 30 + [0.504] * 30 + [0.538] * 30 + [0.572] * 30 + [0.606] * 30 + [0.640] * 30 + [0.674] * 30 + [0.708] * 30 + [0.742] * 30 + [0.776] * 30 + [0.810] * 30 + [0.844] * 30 + [0.878] * 30 + [0.912] * 30 + [0.946] * 30 + [0.980] * 30 + [1.000] * 1,
        'C3': [0.019] * 15 + [0.035] * 16 + [0.130] * 30 + [0.320] * 30 + [0.487] * 30 + [0.524] * 30 + [0.561] * 30 + [0.598] * 30 + [0.635] * 30 + [0.672] * 30 + [0.709] * 30 + [0.746] * 30 + [0.783] * 30 + [0.820] * 30 + [0.857] * 30 + [0.894] * 30 + [0.931] * 30 + [0.968] * 30 + [1.000] * 1 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30,
        'C4': [0.019] * 15 + [0.035] * 16 + [0.130] * 30 + [0.320] * 30 + [0.395] * 30 + [0.440] * 30 + [0.485] * 30 + [0.530] * 30 + [0.575] * 30 + [0.620] * 30 + [0.665] * 30 + [0.710] * 30 + [0.755] * 30 + [0.800] * 30 + [0.845] * 30 + [0.890] * 30 + [0.935] * 30 + [0.980] * 30 + [1.000] * 1 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30,
        'C5': [0.019] * 15 + [0.075] * 16 + [0.150] * 30 + [0.380] * 30 + [0.534] * 30 + [0.568] * 30 + [0.602] * 30 + [0.636] * 30 + [0.670] * 30 + [0.704] * 30 + [0.738] * 30 + [0.772] * 30 + [0.806] * 30 + [0.840] * 30 + [0.874] * 30 + [0.908] * 30 + [0.942] * 30 + [0.976] * 30 + [1.000] * 1 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30 + [np.nan] * 30,
        'Faixa': ['Atraso_0_14']*15 + ['Atraso_15_30'] * 16 + ['Atraso_31_60'] * 30 + ['Atraso_61_90'] * 30 + ['Atraso_91_120'] * 30 + ['Atraso_121_150'] * 30 + ['Atraso_151_180'] * 30 + ['Atraso_181_210'] * 30 + ['Atraso_211_240'] * 30 + ['Atraso_241_270'] * 30 + ['Atraso_271_300'] * 30 + ['Atraso_301_330'] * 30 + ['Atraso_331_360'] * 30 + ['Atraso_361_390'] * 30 + ['Atraso_391_420'] * 30 + ['Atraso_421_450'] * 30 + ['Atraso_451_480'] * 30 + ['Atraso_481_510'] * 30 + ['Atraso_511_540'] * 30 + ['Atraso_541_570'] * 30 + ['Atraso_571_600'] * 30 + ['Atraso_601_630'] * 30 + ['Atraso_631_660'] * 30 + ['Atraso_661_690'] * 30 + ['Atraso_Acima_691'] * 1
        })

    # Filtro da classe
    df_atraso = df_atraso[['DiasAtraso', classif,'Faixa']].rename(columns={classif: 'PercPDD'})

    if consig == 'S':
        df_atraso.loc[df_atraso.index[:15], 'PercPDD'] = 0.005

    df_atraso = df_atraso.dropna()

    len_atraso = len(df_atraso)

    # Controle de Dedutibilidade Fiscal
    df_dedutib = pd.DataFrame({
        'DiasAtraso': range(0, 692),
        'C1': [0.000] * 91 + [0.100] * 30 + [0.145] * 30 + [0.190] * 30 + [0.235] * 30 + [0.280] * 30 + [0.325] * 30 + [0.370] * 30 + [0.415] * 30 + [0.460] * 30 + [0.505] * 30 + [0.550] * 30 + [0.595] * 30 + [0.640] * 30 + [0.685] * 30 + [0.730] * 30 + [0.775] * 30 + [0.820] * 30 + [0.865] * 30 + [0.910] * 30 + [0.955] * 30 + [1.000] * 1,
        'C2': [0.000] * 91 + [0.334] * 30 + [0.368] * 30 + [0.402] * 30 + [0.436] * 30 + [0.470] * 30 + [0.504] * 30 + [0.538] * 30 + [0.572] * 30 + [0.606] * 30 + [0.640] * 30 + [0.674] * 30 + [0.708] * 30 + [0.742] * 30 + [0.776] * 30 + [0.810] * 30 + [0.844] * 30 + [0.878] * 30 + [0.912] * 30 + [0.946] * 30 + [0.980] * 30 + [1.000] * 1,
        'C3': [0.000] * 91 + [0.487] * 30 + [0.524] * 30 + [0.561] * 30 + [0.598] * 30 + [0.635] * 30 + [0.672] * 30 + [0.709] * 30 + [0.746] * 30 + [0.783] * 30 + [0.820] * 30 + [0.857] * 30 + [0.894] * 30 + [0.931] * 30 + [0.968] * 30 + [1.000] * 1 + [np.nan] * 180,
        'C4': [0.000] * 91 + [0.395] * 30 + [0.440] * 30 + [0.485] * 30 + [0.530] * 30 + [0.575] * 30 + [0.620] * 30 + [0.665] * 30 + [0.710] * 30 + [0.755] * 30 + [0.800] * 30 + [0.845] * 30 + [0.890] * 30 + [0.935] * 30 + [0.980] * 30 + [1.000] * 1 + [np.nan] * 180,
        'C5': [0.000] * 91 + [0.534] * 30 + [0.568] * 30 + [0.602] * 30 + [0.636] * 30 + [0.670] * 30 + [0.704] * 30 + [0.738] * 30 + [0.772] * 30 + [0.806] * 30 + [0.840] * 30 + [0.874] * 30 + [0.908] * 30 + [0.942] * 30 + [0.976] * 30 + [1.000] * 1 + [np.nan] * 180,
        })

    # Filtro da classe
    df_dedutib = df_dedutib[['DiasAtraso', classif]].rename(columns={classif: 'DedutPerc'})

    df_dedutib = df_dedutib.dropna()


    ### ---------------------------------------------------------------------------------
    ### JUROS ---------------------------------------------------------------------------
    ### ---------------------------------------------------------------------------------


    if inad=='N':
        df = df_accruals.copy()
        df.columns=['Data', 'SaldoCont', 'Juros', 'AmortPremio', 'SaldoPremio']
        df_juros = df_juros[['datas_pmt_efetivo', 'vf_pmt']]
        df_juros.columns= ['Data', 'Parcela']
        df = pd.merge(df, df_juros[['Data', 'Parcela']], how='left', on='Data')
        df['Parcela'] = df['Parcela'].fillna(0.0)
        df['DiasAtraso'] = 0
        # Atualizar a primeira linha da coluna 'Parcela', pois se o contrato é adimplente as parcelas atrasadas são pagas
        if not df.empty:
            df.loc[df.index[0], 'Parcela'] += saldo - saldo_aj

    if inad=='S':
        df = pd.DataFrame({'Data': pd.date_range(start=data_base, periods=int(len_atraso - atraso), freq='D')})
        df_accruals.columns=['Data', 'SaldoCont', 'Juros', 'AmortPremio', 'SaldoPremio']
        df = pd.merge(df, df_accruals, how='left', on='Data')
        df['DiasAtraso'] = atraso + pd.Series(range(len(df)))  # Incrementa 1 a cada linha
        df['SaldoCont'] = df['SaldoCont'].ffill()
        df['Juros'] = df['Juros'].fillna(0.0)
        df['Parcela'] = 0.0
        df['SaldoPremio'] = df['SaldoPremio'].ffill()
        df['AmortPremio'] = df['AmortPremio'].fillna(0.0)

    df['Classif'] = classif
    df['Saldo'] = df['SaldoCont'] + df['SaldoPremio']
    df['JurosLiq'] = df['Juros'] - df['AmortPremio']
    df['Contrato'] = contrato

    # Criar um dicionário para mapeamento de DiasAtraso para PercPDD
    map_pdd = df_atraso.set_index('DiasAtraso')['PercPDD'].to_dict()
    map_faixa = df_atraso.set_index('DiasAtraso')['Faixa'].to_dict()
    map_dedutib = df_dedutib.set_index('DiasAtraso')['DedutPerc'].to_dict()

    # Aplicar o mapeamento para atualizar 'PDDPerc' em df
    df['PercPDD'] = df['DiasAtraso'].map(map_pdd).fillna(0.0)
    df['Faixa'] = df['DiasAtraso'].map(map_faixa).fillna(0.0)
    df['DedutPerc'] = df['DiasAtraso'].map(map_dedutib).fillna(0.0)

    df['PercPDD'] = df['PercPDD'].astype(float)

    # Verificar a opção padrao_atraso
    if padrao_atraso is not None:  # Verifica se padrao_atraso não é nulo
        df['PercPDD'] = df['PercPDD'].apply(lambda x: max(x, padrao_atraso) if x < padrao_atraso else x)

    df['PDDAcum'] = df['PercPDD'] * df['SaldoCont']
    df['PDD'] = df['PDDAcum'].diff()
    df['PDD'] = df['PDD'].fillna(0.0)
    df['DespPDD'] = np.where(df['PDD']>0.0, -df['PDD'], 0.0)
    df['RevPDD'] = np.where(df['PDD']<0.0, -df['PDD'], 0.0)

    if not df.empty:
        df.loc[df.index[0], 'DespPDD'] = -df.loc[df.index[0], 'PDDAcum']

    # Regras aplicadas para cessao não vazia
    if cessao and not pd.isna(cessao).all():  # Se a lista 'cessao' não for vazia e não tiver todos os valores como NA
        cessao_max = pd.to_datetime(max(cessao))  # Encontrar a maior data
        # Remover as observações acima da data cessao
        df = df[df['Data'] <= cessao_max]

        # Criar a coluna 'Cessao' com o saldo da última observação
        df['Cessao'] = np.where(df['Data'] == cessao_max, df['Saldo'].iloc[-1], 0.0)

        # Transformar a última observação de 'RevPDD' em -1 * 'PDDAcum'
        df.loc[df.index[-1], 'RevPDD'] = df.loc[df.index[-1], 'PDDAcum']

        # Zerar as últimas observações das colunas 'SaldoCont', 'SaldoAmort', 'Saldo', 'PDDAcum', e 'DespPDD'
        df.loc[df['Data'] == cessao_max, ['SaldoCont', 'SaldoPremio', 'Saldo', 'PDDAcum', 'PDD']] = 0.0
    else:
        df['Cessao'] = 0.0

    df = df[['Data', 'Parcela', 'Saldo', 'SaldoCont', 'SaldoPremio', 'AmortPremio', 'Juros', 'JurosLiq',
                'Contrato', 'DiasAtraso', 'Classif', 'Faixa', 'PercPDD', 'PDDAcum',
                'PDD', 'DespPDD', 'RevPDD', 'Cessao', 'DedutPerc']]
    df['DedutAcum'] = df['DedutPerc'] * df['SaldoCont']
    df['DedutPeriodo'] = df['DedutAcum'].diff()
    df['DedutPeriodo'] = df['DedutPeriodo'].fillna(0.0)

    df['Mes'] = df['Data'].dt.month
    df['Ano'] = df['Data'].dt.year

    df['Dif_Temp'] = np.where(df['DiasAtraso'] < 90, df['PDDAcum']*0.4, 0.0)

    classifs = ['C1', 'C2', 'C3', 'C4', 'C5']
    for classif in classifs:
        df[f'{classif}'] = df.apply(lambda x: x['SaldoCont'] if x['Classif'] == classif else 0, axis=1)

    ratings = ['Atraso_0_14','Atraso_15_30','Atraso_31_60','Atraso_61_90','Atraso_91_120','Atraso_121_150',
    'Atraso_151_180','Atraso_181_210','Atraso_211_240','Atraso_241_270','Atraso_271_300','Atraso_301_330',
    'Atraso_331_360','Atraso_361_390','Atraso_391_420','Atraso_421_450','Atraso_451_480','Atraso_481_510',
    'Atraso_511_540','Atraso_541_570','Atraso_571_600','Atraso_601_630','Atraso_631_660','Atraso_661_690',
    'Atraso_Acima_691']
    for rating in ratings:
        df[f'{rating}'] = df.apply(lambda x: x['SaldoCont'] if x['Faixa'] == rating else 0, axis=1)

#    df['TC_Receita'] = 0.0
#    df['TC_Fiscal'] = 0.0
#    df['TC_Apropriar'] = tc
#    df['ComissaoFlat'] = 0.0
#    df['ComissaoFlat_Apropriar'] = comiss_flat
#    df['ComissaoDif'] = 0.0
#    df['ComissaoDif_Apropriar'] = comiss_dif

    ### ---------------------------------------------------------------------------------
    ### AGREGAÇÃO -----------------------------------------------------------------------
    ### ---------------------------------------------------------------------------------


    return df
