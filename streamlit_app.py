# .\env\Scripts\Activate.ps1

# git add .
# git commit -m "message"

#streamlit run c:/Users/guilhem/Desktop/streamlit_dashboard_starter/streamlit_app.py

import altair as alt
import streamlit as st
import pandas as pd
import plotly.express as px
import locale
locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
jours_ordre = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

st.set_page_config(page_title="Courses Reviews Dashboard", layout="wide")

# --- Chargement des données ---
@st.cache_data
def load_data():
    df = pd.read_csv("donnees/factures_processed/factures_combined.csv")
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")  # conversion date
    df["qte"] = pd.to_numeric(df["qte"], errors="coerce").fillna(1)
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df["prix_unitaire"] = df["montant"] / df["qte"]
    return df

df = load_data()


st.title("📊 Mes courses")


# --- Filtres ---
st.sidebar.header("🔍 Filtres")

# Magasin
magasins = df["magasin"].dropna().unique()
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





#onglets
tab1, tab2 = st.tabs(["📊 Statistiques générales", "🛒 Produits"])

# --- Statistiques générales ---
with tab1:
    # --- Données filtrées ---
    st.subheader("📄 Derniers achats")
    st.dataframe(df_filtré)

    st.markdown("---")
    # --- Statistiques ---
    total_depense = df_filtré["montant"].sum()
    nb_tickets = df_filtré["id_ticket"].nunique()
    nb_produits = df_filtré["qte"].sum()
    moy_depense_par_ticket = df_filtré.groupby("id_ticket")["montant"].sum().mean()

    # Délai moyen entre courses
    tickets_uniques = df_filtré.drop_duplicates("id_ticket")
    dates_uniques = tickets_uniques.sort_values("date")["date"]
    delta = dates_uniques.diff().dropna()
    frequence_moyenne = delta.mean().days if not delta.empty else 0

    # affichage des metrics
    col1, col2 = st.columns(2)
    col1.metric("Total dépensé", f"{total_depense:.2f} €")
    col2.metric("Nombre de courses", nb_tickets)

    col3, col4 = st.columns(2)
    col3.metric("Dépense / course ", f"{moy_depense_par_ticket:.2f} €")
    col4.metric("Délai moyen entre 2 courses", f"{frequence_moyenne} jours")

    st.markdown("---")

    # ************** Dépenses dans le temps **************
    st.subheader("📆 Historique des courses")






    # --- Historique des courses et montants---

    from plotly_calplot import calplot


    # Data : 1 ligne par ticket, regroupée par date
    tickets = df_filtré.drop_duplicates("id_ticket").copy()
    tickets["count"] = 1

    # Création du calendrier interactif
    fig = calplot(
        tickets,
        x="date",
        y="count",
        gap=0.5,
        colorscale="Blues",
        month_lines=True,
        years_title=True,
        dark_theme=False  # ou True si sotie en dark mode
    )

    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)






    st.markdown("---")

    # --- Selon le jour de la semaine ---
    
    #traitement données
    df_filtré["jour"] = df_filtré["date"].dt.day_name(locale='fr_FR').str.lower()

    tickets_uniques = df_filtré.drop_duplicates("id_ticket")
    jours_tickets = (
        tickets_uniques["jour"]
        .value_counts()
        .reindex(jours_ordre, fill_value=0)
        .reset_index()
    )

    # Préparer les données
    jours_tickets.columns = ["jour", "nombre"]
    jours_tickets["jour"] = jours_tickets["jour"].str.capitalize()

    dep_jour_semaine = (
        tickets_uniques.groupby("jour")["total"]
        .mean()
        .reindex(jours_ordre, fill_value=0)
        .reset_index()
    )
    dep_jour_semaine.columns = ["jour", "moyenne_depense"]
    dep_jour_semaine["jour"] = dep_jour_semaine["jour"].str.capitalize()

    df_graph = jours_tickets.merge(dep_jour_semaine, on="jour")

    # Graphique
    chart_total_courses = alt.Chart(df_graph).mark_bar().encode(
        x=alt.X("jour:N", sort=[j.capitalize() for j in jours_ordre]),
        y=alt.Y("nombre:Q"),
        color=alt.Color("moyenne_depense:Q", scale=alt.Scale(scheme="blues"), legend=alt.Legend(title="Dépense moyenne")),
        tooltip=["jour", "nombre", "moyenne_depense"]
    ).properties(
        title="📊 Jours de course"
    )

    st.altair_chart(chart_total_courses, use_container_width=True)



    # --- Top produits achetés ---
    st.subheader("🛒 Top produits achetés")
    top_produits_nb = df_filtré.groupby("produit")["qte"].sum().sort_values(ascending=False).head(10)
    st.write("Par nombre d'achats")
    st.bar_chart(top_produits_nb)

    top_produits_dep = df_filtré.groupby("produit")["montant"].sum().sort_values(ascending=False).head(10)
    st.write("Par montant dépensé")
    st.bar_chart(top_produits_dep)

    # --- Variations de prix ---
    st.subheader("📉 Produits avec plus forte hausse de prix")

    variation_prix = df_filtré.groupby("produit")["prix_unitaire"].agg(['min', 'max'])
    variation_prix["variation_%"] = ((variation_prix["max"] - variation_prix["min"]) / variation_prix["min"]) * 100
    variation_prix = variation_prix.sort_values("variation_%", ascending=False)
    top_variations = variation_prix[variation_prix["variation_%"] > 0].head(10)

    st.dataframe(
        top_variations.style.format({
            "min": "{:.2f} €", "max": "{:.2f} €", "variation_%": "{:.1f} %"
        })
    )


# --- Onglet Produits ---
with tab2:
    st.header("📦 Produits")

    st.markdown("---")

    produit_cible = st.selectbox("Choix du produit", df_filtré["produit"].dropna().unique())

    st.markdown("---")
#--------------

    
    df_prod = df_filtré[df_filtré["produit"] == produit_cible]

    if df_prod.empty:
        st.info("Aucune donnée pour ce produit.")
    else:
        st.markdown(f"### 🕒 Timeline des achats de : **{produit_cible}**")

        # Ajouter une colonne factice pour aligner les points sur un axe Y plat
        df_prod["y_fake"] = 0

        fig = px.scatter(
            df_prod,
            x="date",
            y="y_fake",
            hover_data={
                "date": True,
                "magasin": True,
                "qte": True,
                "montant": True,
                "produit": False,
                "y_fake": False  # cache cette colonne du hover
            },
            labels={"x": "Date", "y_fake": ""}
        )

        fig.update_traces(marker=dict(size=12, color='mediumseagreen'))
        fig.update_yaxes(visible=False)  # cache l’axe Y inutile
        fig.update_layout(height=300)

        st.plotly_chart(fig, use_container_width=True)
