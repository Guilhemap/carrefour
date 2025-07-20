# .\env\Scripts\Activate.ps1
#streamlit run c:/Users/guilhem/Desktop/streamlit_dashboard_starter/streamlit_app.py

import altair as alt
import streamlit as st
import pandas as pd
import plotly.express as px
import locale
import matplotlib.pyplot as plt
import numpy as np
from plotly_calplot import calplot
import plotly.graph_objects as go
from babel.dates import format_datetime


# locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
jours_ordre = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

st.set_page_config(page_title="Courses Reviews Dashboard", layout="wide")

# --- Chargement des données ---
@st.cache_data
def load_data():
    df = pd.read_csv("donnees/factures_processed/factures_enrichies.csv")
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")  # conversion date
    df["qte"] = pd.to_numeric(df["qte"], errors="coerce").fillna(1)
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce")
    df["prix_unitaire"] = df["montant"] / df["qte"]

    # 🔁 Remplacement des id_ticket par ticket_1, ticket_2, ...
    if "id_ticket" in df.columns:
        unique_ids = df["id_ticket"].dropna().unique()
        id_map = {old_id: f"ticket_{i+1}" for i, old_id in enumerate(unique_ids)}
        df["id_ticket"] = df["id_ticket"].map(id_map)

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


# --- Application des filtres ---
df_filtré = df[
    df["magasin"].isin(magasin_sel) &
    df["date"].between(start_dt, end_dt)
]



#onglets
tab1, tab2, tab3 = st.tabs(["📊 Statistiques générales", "🛒 Produits", "📈 Inflation"])

# --- Statistiques générales ---
with tab1:
    # --- Données filtrées ---
    st.subheader("📄 Derniers achats")
    # st.dataframe(df_filtré)
    df_affichage = df_filtré.copy()
    df_affichage["date"] = df_affichage["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(df_affichage.reset_index(drop=True))

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
    # Affichage des statistiques + graphique horloge
    col1, col2, col3 = st.columns([1, 1, 0.8])  # largeur personnalisée

    with col1:
        st.metric("Total dépensé", f"{total_depense:.2f} €")
        st.metric("Dépense / course ", f"{moy_depense_par_ticket:.2f} €")

    with col2:
        st.metric("Nombre de courses", nb_tickets)
        st.metric("Délai moyen entre 2 courses", f"{frequence_moyenne} jours")

    with col3:
        
        tickets = df_filtré.drop_duplicates("id_ticket").copy()
        tickets["heure"] = pd.to_datetime(tickets["heure"], format="%Hh%M", errors="coerce").dt.hour

        heure_counts = tickets["heure"].value_counts().sort_index()
        heures = np.arange(24)
        valeurs = np.array([heure_counts.get(h, 0) for h in heures])

        theta = np.linspace(0.0, 2 * np.pi, 24, endpoint=False)
        width = 2 * np.pi / 24

        offsetval = 0.5  # rayon intérieur
        hauteur_visuelle = 1.0  # hauteur de l'anneau visible

        # 🔵 Normalisation proportionnelle dans l’espace alloué
        valeurs_scaled = (valeurs / valeurs.max()) * hauteur_visuelle if valeurs.max() > 0 else valeurs

        fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))

        # --- Halo fond bleu clair ---
        ax.bar(
            theta,
            [hauteur_visuelle]*24,
            width=width,
            bottom=offsetval,
            color="#E6F2FF",
            edgecolor="white",
            linewidth=1,
            zorder=1
        )

        # --- Barres principales proportionnelles ---
        ax.bar(
            theta,
            valeurs_scaled,
            width=width,
            bottom=offsetval,
            color="royalblue",
            edgecolor="white",
            linewidth=1,
            zorder=2
        )

        # --- Esthétique ---
        ax.set_theta_direction(-1)
        ax.set_theta_offset(np.pi / 2)
        ax.set_xticks(np.linspace(0, 2 * np.pi, 8, endpoint=False))  # 24 / 3 = 8 segments
        ax.set_xticklabels([f"{h:2}h" for h in range(0, 24, 3)], fontsize=10)
        ax.set_yticks([])
        ax.grid(False)
        ax.spines['polar'].set_visible(False)
        ax.set_ylim(0, offsetval + hauteur_visuelle * 1.05)

        # --- Cercle central ---
        circle = plt.Circle((0, 0), offsetval, transform=ax.transData._b, color="white", zorder=3)
        ax.add_artist(circle)
        ax.text(
            0, 0, "Heure\ndes courses",
            ha='center', va='center',
            fontsize=10, color="black"
        )
        st.pyplot(fig)

    st.markdown("---")









    # ************** Dépenses dans le temps **************
    st.subheader("📆 Historique des courses")



    # --- Historique des courses et montants---

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
    # df_filtré["jour"] = df_filtré["date"].dt.day_name(locale='fr_FR').str.lower()
    df_filtré["jour"] = df_filtré["date"].apply(lambda d: format_datetime(d, "EEEE", locale="fr_FR").lower())

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
        color=alt.Color("moyenne_depense:Q", scale=alt.Scale(scheme="blues"), legend=alt.Legend(title="Dépense moyenne(€)")),
        tooltip=["jour", "nombre", "moyenne_depense"]
    ).properties(
        title="📊 Jours de course"
    )

    st.altair_chart(chart_total_courses, use_container_width=True)


    st.markdown("---")
    # --- Top catégories achetées ---
    st.subheader("🛒 Top produits achetés")

    # Agrégation par catégorie
    top_categories = (
        df_filtré.groupby("categorie", as_index=False)
        .agg({"qte": "sum", "montant": "sum"})
        .sort_values("qte", ascending=False)
        .head(60)
    )

    # Altair chart combiné
    chart_top_categories = alt.Chart(top_categories).mark_bar().encode(
        x=alt.X("qte:Q", title="Quantité achetée"),
        y=alt.Y("categorie:N", sort="-x", title=""),
        color=alt.Color("montant:Q", scale=alt.Scale(scheme="greens"), legend=alt.Legend(title="Dépense (€)")),
        tooltip=["categorie", "qte", "montant"]
    ).properties()
    st.altair_chart(chart_top_categories, use_container_width=True)
    
    
    
    st.markdown("---")
    
    
    #------  Timeline des achats ----
    
    st.markdown(f"### 🕒 Timeline des achats")
    
    
    # Trouver la catégorie avec le plus de quantité totale
    top_categorie = (
        df_filtré.groupby("categorie", as_index=False)
        .agg({"qte": "sum"})
        .sort_values("qte", ascending=False)
        .head(1)["categorie"]
        .values[0]
        if not df_filtré.empty else None
    )
    options = df_filtré["categorie"].dropna().unique()
    default_index = list(options).index(top_categorie) if top_categorie in options else 0

    produit_cible = st.selectbox("Choix du produit", options, index=default_index)


    df_prod = df_filtré[df_filtré["categorie"] == produit_cible]


    
    if df_prod.empty:
        st.info("Aucune donnée pour ce produit.")
    else:
        # st.markdown(f"### 🕒 Timeline des achats de : **{produit_cible}**")

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


# --- Onglet Produits ---
with tab2:

    st.subheader("🍩 Dépenses par catégorie")

    # Liste des groupes
    groupes_ordre = df_filtré["groupe"].dropna().unique().tolist()

    # Mapping manuel des couleurs par groupe
    mapping_couleurs = {
        "légumes": "#2ca02c",
        "fruits": "#ffa15a",
        "graines et noix": "#5c4033",
        "viande": "#c0392b",
        "poisson": "#1f77b4",
        "condiments": "#bc6c25",
        "boisson": "#17becf",
        "hygiene et entretien": "#e377c2",
        "produits laitiers": "#f4d03f",
        "céréales et féculents": "#e1ad01",
        "oeufs": "#f5deb3",
        "grinottage": "#8e44ad",
        "autres": "#7f8c8d"
    }


    # Si des groupes ne sont pas définis dans le mapping, les gérer par défaut
    groupes_restants = [g for g in groupes_ordre if g not in mapping_couleurs]
    couleurs_restantes = ['#FF6692', '#1F77B4']  # par ex. les couleurs restantes de Bold
    mapping_couleurs.update(dict(zip(groupes_restants, couleurs_restantes)))



    # Données pour le donut
    dep_par_cat = (
        df_filtré.groupby("groupe")["montant"]
        .sum()
        .reset_index()
        .sort_values("montant", ascending=False)
    )
    fig_donut = px.pie(
        dep_par_cat,
        names="groupe",
        values="montant",
        hole=0.5,
        color="groupe",
        color_discrete_map=mapping_couleurs,
    )
    fig_donut.update_layout(
        showlegend=True,
        margin=dict(t=10, b=10, l=10, r=10),
        height=350
    )
    st.plotly_chart(fig_donut, use_container_width=True)


    st.subheader("📂 Dépenses par sous-catégorie")
    fig_tree = px.treemap(
        df_filtré,
        path=["groupe", "categorie"],
        values="montant",
        color="groupe",
        color_discrete_map=mapping_couleurs,
    )
    fig_tree.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=500)
    st.plotly_chart(fig_tree, use_container_width=True)





    st.markdown("---")

    st.subheader("🌿 Répartition des dépenses BIO / non BIO (en % tous les 4 mois)")

    # Créer une période glissante de 4 mois
    df_filtré["quadri_glissant"] = (
        df_filtré["date"].dt.to_period("M")
        .apply(lambda p: f"{p.year}-{(p.month - 1) // 4 * 4 + 1:02d}")
    )

    # Remplir les valeurs manquantes dans BIO si nécessaire
    df_filtré["BIO"] = df_filtré["BIO"].fillna(False)

    # Agréger les montants par période et valeur de BIO
    df_bio = (
        df_filtré.groupby(["quadri_glissant", "BIO"])["montant"]
        .sum()
        .reset_index()
    )

    # Calcul des pourcentages par période
    totaux = df_bio.groupby("quadri_glissant")["montant"].transform("sum")
    df_bio["pourcent"] = df_bio["montant"] / totaux * 100

    # Pivot pour tableau période x BIO
    df_pivot = df_bio.pivot_table(
        index="quadri_glissant",
        columns="BIO",  # True / False
        values="pourcent",
        fill_value=0
    ).reset_index()

    # Définir l’ordre d’empilement : True (BIO) en bas
    ordre_bio = [True, False]
    ordre_bio = [col for col in ordre_bio if col in df_pivot.columns]

    # Couleurs
    couleurs_bio = {
        True: "#4CAF50",   # vert BIO
        False: "#B0B0B0"   # gris non BIO
    }

    # Tracer le graphique
    fig = go.Figure()
    for bio in ordre_bio:
        fig.add_trace(go.Scatter(
            x=df_pivot["quadri_glissant"],
            y=df_pivot[bio],
            name="BIO" if bio else "Non BIO",
            stackgroup='one',
            mode='none',
            line_shape='spline',
            fillcolor=couleurs_bio[bio]
        ))

    fig.update_layout(
        yaxis=dict(title="Pourcentage", ticksuffix="%"),
        xaxis_title="Période (4 mois)",
        height=450,
        showlegend=True,
        margin=dict(t=30, b=40, l=10, r=10)
    )

    st.plotly_chart(fig, use_container_width=True)








# --- Onglet Inflation ---
with tab3:
    # --- Variations de prix ---
    st.subheader("📈 Produits avec plus forte hausse de prix")

    # On filtre les produits "au poids"
    df_variation = df_filtré[
        (df_filtré["poids"].isna()) &
        (~df_filtré["groupe"].str.lower().isin(["légumes", "fruits", "céréales et féculents"]))
    ]

    variation_prix = df_variation.groupby("produit")["prix_unitaire"].agg(['min', 'max'])
    variation_prix["variation_%"] = ((variation_prix["max"] - variation_prix["min"]) / variation_prix["min"]) * 100
    variation_prix = variation_prix.sort_values("variation_%", ascending=False)
    top_variations = variation_prix[variation_prix["variation_%"] > 0].head(10)

    st.dataframe(
        top_variations.style.format({
            "min": "{:.2f} €", "max": "{:.2f} €", "variation_%": "{:.1f} %"
        })
    )