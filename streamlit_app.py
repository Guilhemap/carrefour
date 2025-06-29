# .\env\Scripts\Activate.ps1
import streamlit as st
import pandas as pd
import numpy as np
import datetime

st.set_page_config(page_title="Dashboard Starter", layout="centered")

st.title("📊 Mon Premier Dashboard Streamlit")

# Chargement des données
df = pd.read_csv("donnees.csv")

# Widgets d'interaction
st.sidebar.header("Filtres")
selected_date = st.sidebar.date_input("Date minimale", datetime.date(2023, 1, 1))
min_value = st.sidebar.slider("Valeur minimale", int(df["valeur"].min()), int(df["valeur"].max()), 50)

# Filtrage des données
filtered_df = df[(pd.to_datetime(df["date"]) >= pd.to_datetime(selected_date)) & (df["valeur"] >= min_value)]

# Affichage
st.subheader("Aperçu des données filtrées")
st.write(filtered_df.head())

# Graph
st.subheader("Évolution dans le temps")
st.line_chart(filtered_df.set_index("date")["valeur"])




# git add .
# git commit -m "first commit"
