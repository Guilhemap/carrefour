# .\env\Scripts\Activate.ps1

# git add .
# git commit -m "message"

#streamlit run c:/Users/guilhem/Desktop/streamlit_dashboard_starter/streamlit_app.py

import streamlit as st
import pandas as pd

# --- Chargement des données ---
@st.cache_data
def load_data():
    df = pd.read_csv("donnees/factures_processed/factures_combined.csv")
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")  # conversion date
    return df

df = load_data()

st.title("📊 Analyse de mes factures Carrefour")

# --- Filtres ---
st.sidebar.header("🔍 Filtres")

# Magasin
magasins = df["magasin"].unique()
magasin_sel = st.sidebar.multiselect("Magasin", magasins, default=magasins)

# Période
st.sidebar.markdown("### 🗓️ Période d'analyse")
min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.sidebar.slider(
    "Sélectionne une période",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="DD/MM/YYYY"
)
start_dt = pd.to_datetime(date_range[0])
end_dt = pd.to_datetime(date_range[1])

# Produits
produits = df["produit"].dropna().unique()
produit_sel = st.sidebar.multiselect("Produit", produits)

# --- Application des filtres ---
df_filtré = df[
    df["magasin"].isin(magasin_sel) &
    df["date"].between(start_dt, end_dt)
]

if produit_sel:
    df_filtré = df_filtré[df_filtré["produit"].isin(produit_sel)]

# --- Affichage ---
st.subheader("📄 Données filtrées")
st.dataframe(df_filtré)

# --- Statistiques ---
st.subheader("📈 Statistiques")
st.metric("Total dépensé", f"{df_filtré['montant'].sum():.2f} €")
st.metric("Nombre de courses", df_filtré["id_ticket"].nunique())
top_produits = df_filtré["produit"].value_counts().head(5)

st.write("🛒 Top produits achetés")
st.bar_chart(top_produits)