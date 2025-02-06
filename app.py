import pandas as pd
import streamlit as st
import plotly.express as px

# Carregar os dados
df = pd.read_csv('base_vendas.csv', sep=';', dtype=str, encoding='iso-8859-1')

# Converter colunas para tipos adequados
df["QTD"] = df["QTD"].astype(int)
df["TOTAL DA COMPRA"] = df["TOTAL DA COMPRA"].str.replace(",", ".").astype(float)  # Corrigido

df["DATA_VENDA"] = pd.to_datetime(df["DATA_VENDA"], format="%d/%m/%Y")
df["DATA_PG"] = pd.to_datetime(df["DATA_PG"], format="%d/%m/%Y")

# Criar métricas para os cards
total_vendas = df["QTD"].sum()
pedidos_pagos = df[df["STATUS_PEDIDO"] == "PAGO"]["QTD"].sum()
pendentes = df[df["STATUS_PEDIDO"] == "PENDENTE DE PAGAMENTO"]["QTD"].sum()
saldo_vendas = df[df["STATUS_PEDIDO"] == "PAGO"]["TOTAL DA COMPRA"].sum()
saldo_pendente = df[df["STATUS_PEDIDO"] == "PENDENTE DE PAGAMENTO"]["TOTAL DA COMPRA"].sum()
dias_com_venda = df["DATA_VENDA"].nunique()
ticket_medio = saldo_vendas / pedidos_pagos if pedidos_pagos > 0 else 0
vendas_por_dia = total_vendas / dias_com_venda if dias_com_venda > 0 else 0

# Estilos personalizados
st.markdown("""
    <style>
        .card {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 100%;
        }
        .card h3 {
            margin: 0;
            font-size: 16px;
            color: #333;
        }
        .card .value {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }
        .card .description {
            font-size: 12px;
            color: #666;
        }
    </style>
""", unsafe_allow_html=True)

# Lista de cards com valores reais
cards = [
    ("Vendas", f"{total_vendas}", "Pedidos"),
    ("Pagos", f"{pedidos_pagos}", "Entradas"),
    ("Pendentes", f"{pendentes}", "% Pendente"),
    ("Saldo Venda", f"R$ {saldo_vendas:,.2f}", "Total Vendido"),
    ("Saldo Pendente", f"R$ {saldo_pendente:,.2f}", "Total a Receber"),
    ("Dias com Venda", f"{dias_com_venda}", "Dias Trabalhados"),
    ("Ticket Médio", f"R$ {ticket_medio:,.2f}", "Média por Pedido"),
    ("Vendas/Dia", f"{vendas_por_dia:.1f}", "Média diária"),
]

# Criando colunas para distribuir os cards
cols = st.columns(len(cards))

# Adicionando os cards
for col, (title, value, desc) in zip(cols, cards):
    with col:
        st.markdown(f"""
            <div class="card">
                <h3>{title}</h3>
                <div class="value">{value}</div>
                <div class="description">{desc}</div>
            </div>
        """, unsafe_allow_html=True)

st.write('---')

col_line1, col_line2 = st.columns(2)

with col_line1:
    
    # Criar DataFrame de evolução diária
    df_grouped = df.groupby("DATA_VENDA").agg({
        "QTD": "sum",
        "TOTAL DA COMPRA": "sum"
    }).reset_index()

    df_grouped.rename(columns={"QTD": "Vendidos", "TOTAL DA COMPRA": "Valor Total"}, inplace=True)

    # Criando o gráfico de vendas diárias
    fig = px.line(df_grouped, x="DATA_VENDA", y="Vendidos", 
                markers=True, title="Evolução das Vendas (Quantidade)",
                labels={"Vendidos": "Quantidade de Vendas", "DATAVENDA": "Data"})

    # Exibir no Streamlit
    st.plotly_chart(fig, use_container_width=True)


with col_line2:
    
    # Filtrar apenas os pagamentos confirmados
    df_pagos = df[df["STATUS_PEDIDO"] == "PAGO"]

    # Criar DataFrame de evolução diária dos valores pagos
    df_grouped_pagamentos = df_pagos.groupby("DATA_PG").agg({
        "TOTAL DA COMPRA": "sum"
    }).reset_index()

    df_grouped_pagamentos.rename(columns={"TOTAL DA COMPRA": "Valor Pago"}, inplace=True)

    # Criando o gráfico de valores pagos por data de pagamento
    fig = px.line(df_grouped_pagamentos, x="DATA_PG", y="Valor Pago",
                markers=True, title="Evolução dos Pagamentos Recebidos (R$)",
                labels={"Valor Pago": "Valores Pagos (R$)", "DATA_PG": "Data de Pagamento"})

    # Exibir no Streamlit
    st.plotly_chart(fig, use_container_width=True)
    
st.write('---')


# Comparativo Mensal - Agrupar vendas e pagamentos por mês
df_vendas = df.groupby(df["DATA_VENDA"].dt.to_period("M")).agg({
    "QTD": "sum",
}).rename(columns={"QTD": "Qtd Vendida"})

df_pagamentos = df[df["STATUS_PEDIDO"] == "PAGO"].groupby(df["DATA_PG"].dt.to_period("M")).agg({
    "TOTAL DA COMPRA": "sum"
}).rename(columns={"TOTAL DA COMPRA": "Valor Pago"})

# Juntar os dois DataFrames
df_mes = df_vendas.join(df_pagamentos, how="outer").fillna(0)

# Calcular variação percentual em relação ao mês anterior
df_mes["Variação Vendas"] = df_mes["Qtd Vendida"].pct_change() * 100
df_mes["Variação Pagamento"] = df_mes["Valor Pago"].pct_change() * 100

# Formatar valores
df_mes = df_mes.reset_index()
df_mes["DATA_VENDA"] = df_mes["DATA_VENDA"].astype(str)
df_mes["Variação Vendas"] = df_mes["Variação Vendas"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
df_mes["Variação Pagamento"] = df_mes["Variação Pagamento"].map(lambda x: f"{x:.2f}%" if pd.notna(x) else "-")
df_mes["Valor Pago"] = df_mes["Valor Pago"].map(lambda x: f"R$ {x:,.2f}")

# **Exibir comparativo mensal dentro de um expander**
with st.expander("📊 Comparativo Mensal de Vendas e Pagamentos", expanded=True):
    st.dataframe(df_mes, hide_index=True)

st.write("---")

# **Clientes devedores - Tabela**
# Filtrar apenas pedidos pendentes
df_pendentes = df[df["STATUS_PEDIDO"] == "PENDENTE DE PAGAMENTO"].copy()

# Converter colunas de data para datetime
df_pendentes["DATA_PG"] = pd.to_datetime(df_pendentes["DATA_PG"], dayfirst=True)

# Agrupar por cliente
df_pendentes = df_pendentes.groupby("NOME").agg({
    "TOTAL DA COMPRA": "sum",
    "DATA_PG": "min"
}).reset_index()

# Calcular dias de atraso
df_pendentes["Dias de Atraso"] = (pd.Timestamp.today() - df_pendentes["DATA_PG"]).dt.days
df_pendentes["Dias de Atraso"] = df_pendentes["Dias de Atraso"].apply(lambda x: x if x > 0 else 0)

# Renomear colunas
df_pendentes.rename(columns={"NOME": "Cliente", "TOTAL DA COMPRA": "Valor Devido", "DATA_PG": "Data Prevista"}, inplace=True)

# Formatar valores monetários
df_pendentes["Valor Devido"] = df_pendentes["Valor Devido"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Ordenar por valor devido
df_pendentes = df_pendentes.sort_values(by=["Valor Devido", "Dias de Atraso"], ascending=[False, False])

# **Aplicar destaque vermelho nos maiores devedores**
def highlight_maiores_devedores(val):
    if isinstance(val, str) and "R$" in val:  # Para evitar erro ao formatar os números
        val_float = float(val.replace("R$ ", "").replace(".", "").replace(",", "."))
        if val_float > 5000:  # Se deve mais de R$ 5.000, aplicar destaque
            return "background-color: #ffcccc"
    return ""

# Exibir tabela formatada
with st.expander("⚠️ Clientes com Pagamentos Pendentes", expanded=True):
    st.dataframe(df_pendentes.style.applymap(highlight_maiores_devedores, subset=["Valor Devido"]), hide_index=True)
