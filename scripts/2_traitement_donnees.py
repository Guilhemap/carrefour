import openai
import pandas as pd
from dotenv import load_dotenv
import os
from tqdm import tqdm

# 🔐 Chargement de la clé API
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 📥 Chargement des données complètes
df_factures = pd.read_csv("donnees/factures_processed/factures_combined.csv")

# 🧼 Liste des produits uniques à classifier
produits_uniques = df_factures["produit"].dropna().drop_duplicates().reset_index(drop=True)

# # 🔎 Limite à 30 pour test (ajuste si besoin)
# if len(produits_uniques) > 30:
#     produits_uniques = produits_uniques.iloc[0:30]

# 📋 Prompt premium
prompt_base = """
Tu es un expert en reconnaissance automatique de libellés produits issus de tickets de caisse.

Ton objectif est d'assigner à chaque libellé une catégorie de produit claire, cohérente et précise.  
Tu dois te comporter comme un humain expert en retail : tu connais les marques, les formats, les conditionnements, les abréviations courantes et les rayons de supermarché.

Tu dois répondre uniquement par le nom de la catégorie, sans aucune phrase autour, sans ponctuation superflue.

Voici quelques exemples :

- Produit : X65G NJ CANARD A L → Catégorie : canard  
- Produit : FENOUIL VRA → Catégorie : fenouil  
- Produit : 120G FOIE MORUE AU → Catégorie : foie morue  
- Produit : 1KG POELEE BRETONN → Catégorie : poellee legumes  
- Produit : ASPERGE BLC/VLT → Catégorie : asperge  
- Produit : EVIAN 6X1.5L PET → Catégorie : eau  
- Produit : 1L NECTAR PRUNE → Catégorie : jus de fruits  
- Produit : SAC KRAFT BLANC GR → Catégorie : sac  
- Produit : 900G COURGET.TOM.C → Catégorie : courgette  
- Produit : BQ 2FT GRENADE A J → Catégorie : grenade  
- Produit : GINGEMBRE BIO → Catégorie : gingembre  
- Produit : 75CL VINAIGRE BALS → Catégorie : vinaigre  
- Produit : BASILIC FRA → Catégorie : basilic  
- Produit : BQ 4FRT POIRE MAP → Catégorie : poire  
- Produit : 3X135G SARD.ENT/HO → Catégorie : sardine  
"""

# 🤖 Classification ligne à ligne
categories = []
for produit in tqdm(produits_uniques, desc="Classification des produits"):
    prompt = prompt_base + f"\nProduit : {produit}\n→ Catégorie :"
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        category = response.choices[0].message.content.strip()
    except Exception:
        category = "erreur"
    categories.append(category)

# 🔁 Mapping produit → catégorie
mapping = dict(zip(produits_uniques, categories))

# 📎 Application du mapping à toutes les lignes du fichier original
df_factures["categorie"] = df_factures["produit"].map(mapping)

# 💾 Sauvegarde
df_factures.to_csv("donnees/factures_processed/factures_enrichies.csv", index=False, encoding='utf-8')
print("✅ Données enrichies exportées dans : factures_enrichies.csv")


# #-------------------------------- ajout de la catégorie englobante
# 
# 

# 📋 Liste fermée de groupes
groupes_autorises = [
    "légumes", "fruits", "graines et noix", "viande", "poisson",
    "condiments", "boisson", "hygiene et entretien", "produits laitiers",
    "céréales et féculents", "oeufs", "grinottage", "autres"
]

# 🧠 Prompt template
prompt_template = f"""
Tu es un expert en classification de produits alimentaires et non alimentaires en grande distribution.

Ton objectif est de regrouper une catégorie spécifique (comme "carotte", "sardine", "yaourt", "échalote", etc.) dans une **famille de produits principale**, telle qu’on les organise dans les rayons d’un supermarché.

Voici la liste **strictement fermée** des groupes possibles :

{chr(10).join('- ' + g for g in groupes_autorises)}

Règles :
- Ne propose **jamais** un groupe en dehors de cette liste.
- Pense comme un **chef de rayon**, pas comme un botaniste ou nutritionniste.
- L’objectif est d’être **pratique, cohérent, et orienté “usage courant”**.
- Si le produit est flou, inconnu ou ambivalent, réponds : autres.

Exemples :
- carotte → legumes  
- échalote → legumes  
- avocat → legumes  
- sardine → poisson  
- chocolat → grinottage  
- vinaigre → condiments  
- lait → produits laitiers  
- riz → céréales et féculents  
- oeuf → oeufs  
- savon → hygiene et entretien  
- amandes → graines et noix  
- ? → autres

Catégorie : {{categorie}}  
→ Groupe :
"""


# 🔍 Récupérer toutes les catégories uniques
categories_uniques = df_factures["categorie"].dropna().drop_duplicates()

# 🔁 Classer chaque catégorie via GPT
mapping_groupe = {}

for cat in tqdm(categories_uniques, desc="Classification des groupes"):
    prompt = prompt_template.replace("{categorie}", cat)
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        groupe = response.choices[0].message.content.strip()
    except Exception:
        groupe = "autres"

    # Nettoyage minimal
    if groupe not in groupes_autorises:
        groupe = "autres"

    mapping_groupe[cat] = groupe

# 🧾 Appliquer à tout le DataFrame
df_factures["groupe"] = df_factures["categorie"].map(mapping_groupe)

# 💾 Ré-export
df_factures.to_csv("donnees/factures_processed/factures_enrichies.csv", index=False, encoding="utf-8")
print("✅ Colonne 'groupe' ajoutée et fichier mis à jour.")





# #--------------------------------ajout de la colonne BIO
df_factures["BIO"] = df_factures["produit"].str.contains("BIO", case=False, na=False)
df_factures.to_csv("donnees/factures_processed/factures_enrichies.csv", index=False, encoding="utf-8")
print("✅ Colonne 'BIO' ajoutée")



# # ----- reorganisation des colonnes -----
colonnes_a_reordonner = ["categorie", "groupe", "BIO", "id_ticket"]
colonnes_avant = [col for col in df_factures.columns if col not in colonnes_a_reordonner]
nouvel_ordre = colonnes_avant + colonnes_a_reordonner
df_factures = df_factures[nouvel_ordre]



# Export enrichi final
df_factures.to_csv("donnees/factures_processed/factures_enrichies.csv", index=False, encoding='utf-8')
print("✅ Données enrichies exportées dans : factures_enrichies.csv")

