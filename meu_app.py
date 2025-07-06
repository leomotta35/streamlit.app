import streamlit as st
import pandas as pd

st.set_page_config(page_title="Meu Site Streamlit")

with st.container():
    st.subheader("Site com o Streamlit")
    st.title("Dashboard de Contratos")
    st.write("Informações sobre os contratos fechados pela Hash&Co ao longo de maio")
    st.write("Meu Likedin: [Clique aqui](https://www.linkedin.com/in/leonel-mota-a0656122a?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BdGxf96YvR0Ow4bxDtK4GNA%3D%3D)")


@st.cache_data
def carregar_dados():
    tabela = pd.read_csv("resultados.csv")
    return tabela

with st.container():
    st.write("---")
    qtde_dias = st.selectbox("Selecione o período", ["7D", "15D", "21D", "30D"])
    num_dias = int(qtde_dias.replace("D", ""))
    dados = carregar_dados()
    dados = dados[-num_dias:]
    st.area_chart(dados, x="Data", y="Contratos")

