import streamlit as st
import psycopg2
from psycopg2 import Error
from datetime import datetime, timedelta

# --- 1. Configuração do Banco de Dados ---
# ATENÇÃO: Substitua 'seu_usuario', 'sua_senha', 'seu_host', 'sua_porta' pelas suas credenciais
DB_CONFIG = {
    "dbname": "db.banco",
    "user": "seu_usuario",
    "password": "sua_senha",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados PostgreSQL."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return None

# --- 2. Funções de Inserção de Dados (mantidas as existentes e aprimorada a financeira) ---

# ... (Funções insert_cliente, insert_produto, insert_vendedor, insert_venda, insert_item_venda inalteradas) ...

# Modificação na função insert_lancamento_financeiro_internal para incluir os novos campos
def insert_lancamento_financeiro_internal(conn, tipo_lancamento, descricao, valor, data_vencimento, data_pagamento, status, valor_multa=0.00, valor_juros=0.00, valor_desconto=0.00):
    """
    Função interna para inserir um novo lançamento na tabela 'financeira'
    com suporte para multa, juros e desconto.
    """
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO financeira (tipo_lancamento, descricao, valor, data_vencimento, data_pagamento, status, valor_multa, valor_juros, valor_desconto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (tipo_lancamento, descricao, valor, data_vencimento, data_pagamento, status, valor_multa, valor_juros, valor_desconto))
            # conn.commit() é feito pela função chamadora (ex: insert_venda) ou na própria interface
    except Error as e:
        st.error(f"Erro interno ao adicionar lançamento financeiro: {e}")
        conn.rollback()

# --- Aprimorando insert_venda para passar os valores de multa/juros/desconto (mesmo que zero) ---
def insert_venda(conn, id_cliente, id_vendedor, valor_total):
    """
    Insere uma nova venda na tabela 'vendas' e cria um lançamento
    de 'contas a receber' na tabela 'financeira'.
    """
    try:
        with conn.cursor() as cur:
            # 1. Inserir a Venda
            cur.execute("""
                INSERT INTO vendas (id_cliente, id_vendedor, valor_total)
                VALUES (%s, %s, %s) RETURNING id_venda
            """, (id_cliente, id_vendedor, valor_total))
            id_venda_gerada = cur.fetchone()[0]
            conn.commit()
            st.success(f"Venda adicionada com sucesso! ID da Venda: {id_venda_gerada}")

            # 2. Criar o Lançamento de Contas a Receber
            descricao_lancamento = f"Recebimento da Venda ID: {id_venda_gerada}"
            data_vencimento_lancamento = datetime.now().date() + timedelta(days=30)

            # Ao chamar a função financeira, passe 0.00 para multa, juros e desconto
            insert_lancamento_financeiro_internal(
                conn,
                'receber',
                descricao_lancamento,
                valor_total,
                data_vencimento_lancamento,
                None,
                'pendente',
                valor_multa=0.00, # Valor padrão para vendas, pode ser ajustado se houver lógica de juros/multa na venda
                valor_juros=0.00,
                valor_desconto=0.00
            )

        return id_venda_gerada
    except Error as e:
        st.error(f"Erro ao adicionar venda e lançamento financeiro: {e}")
        conn.rollback()
        return None

# --- 3. Interface Streamlit ---

st.set_page_config(layout="wide", page_title="Sistema de Gerenciamento - db.banco")
st.title("Sistema de Gerenciamento - db.banco")
st.write("Selecione a tabela para inserir novos dados.")

conn = get_db_connection()

if conn:
    table_choice = st.sidebar.selectbox(
        "Escolha a Tabela para Inserir Dados",
        ("Clientes", "Produtos", "Vendedores", "Vendas", "Lançamentos Financeiros")
    )

    st.header(f"Inserir Dados na Tabela de {table_choice}")

    # ... (Seções para Clientes, Produtos, Vendedores, Vendas inalteradas) ...

elif table_choice == "Lançamentos Financeiros":
        with st.form("form_financeira"):
            st.subheader("Novo Lançamento Financeiro")
            tipo_lancamento = st.selectbox("Tipo de Lançamento", ("receber", "pagar"))
            descricao = st.text_area("Descrição")
            valor = st.number_input("Valor Base", min_value=0.01, format="%.2f")
            data_vencimento = st.date_input("Data de Vencimento", value=datetime.today())
            data_pagamento = st.date_input("Data de Pagamento (opcional)", value=None)
            status = st.selectbox("Status", ("pendente", "pago", "cancelado"))

            st.markdown("---")
            st.subheader("Valores Adicionais/Reduções (Opcional)")
            valor_multa = st.number_input("Valor de Multa", min_value=0.00, value=0.00, format="%.2f")
            valor_juros = st.number_input("Valor de Juros", min_value=0.00, value=0.00, format="%.2f")
            valor_desconto = st.number_input("Valor de Desconto", min_value=0.00, value=0.00, format="%.2f")

            submitted = st.form_submit_button("Adicionar Lançamento")
            if submitted:
                # Chame a função interna, mas exiba a mensagem de sucesso aqui
                insert_lancamento_financeiro_internal(conn, tipo_lancamento, descricao, valor, data_vencimento, data_pagamento, status, valor_multa, valor_juros, valor_desconto)
                conn.commit() # Commit explícito para lançamentos manuais
                st.success("Lançamento financeiro adicionado com sucesso!")
else:
    st.warning("Não foi possível conectar ao banco de dados. Verifique suas configurações e se o PostgreSQL está rodando.")