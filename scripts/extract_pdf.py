import os
import pdfplumber
import re
import pandas as pd

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    return text

def parse_ticket_text(text):
    lines = text.strip().splitlines()

    magasin = lines[0] if lines else None

    date_match = re.search(r"(\d{2}/\d{2}/\d{4}) à (\d{2}h\d{2})", text)
    if date_match:
        date = date_match.group(1)
        heure = date_match.group(2)
    else:
        date = None
        heure = None

    total_match = re.search(r"Total à payer\s+([0-9]+(?:[.,][0-9]{2})?)€", text)
    total = total_match.group(1) if total_match else None

    produit_section = re.search(r"TVA Produit.*?(?=Total à payer)", text, re.DOTALL)
    produits = []
    if produit_section:
        bloc = produit_section.group(0).splitlines()[1:]

        i = 0
        while i < len(bloc):
            line = bloc[i].strip()
            match = re.match(r"\d{1,2}\.?\d*%?\s+(.*?)\s+(\d+)\s+x\s+([\d,.]+)\s+([\d,.]+)", line)
            if match:
                nom = match.group(1)
                qte = int(match.group(2))
                pu = match.group(3).replace(",", ".")
                montant = match.group(4).replace(",", ".")
                poids, prixkg = "NA", "NA"

                if i + 1 < len(bloc):
                    next_line = bloc[i + 1].strip()
                    poids_match = re.match(r"([\d,.]+)kg x ([\d,.]+)€/kg", next_line)
                    if poids_match:
                        poids = poids_match.group(1).replace(",", ".")
                        prixkg = poids_match.group(2).replace(",", ".")
                        i += 1

                produits.append({
                    "produit": nom,
                    "qte": qte,
                    "prix_unitaire": float(pu),
                    "montant": float(montant),
                    "poids": float(poids) if poids != "NA" else None,
                    "prix_kg": float(prixkg) if prixkg != "NA" else None
                })
            i += 1



    last_line = lines[-1] if lines else ""
    idticket_match = re.match(r"\d{2}\.\d{2}\.\d{2} \d{2}:\d{2} (.+)", last_line)
    idticket = idticket_match.group(1).strip() if idticket_match else None

    df = pd.DataFrame(produits)
    df["magasin"] = magasin
    df["date"] = date
    df["heure"] = heure
    df["total"] = float(total.replace(",", ".")) if total else None
    df["id_ticket"] = idticket

    return df


def process_all_factures(folder_path):
    all_dfs = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(".pdf"):
            full_path = os.path.join(folder_path, filename)
            print(f"Traitement de {filename}...")
            text = extract_text_from_pdf(full_path)
            df = parse_ticket_text(text)
            # print(df)  # Affiche le df pour debug à chaque fichier
            all_dfs.append(df)
    combined_df = pd.concat(all_dfs, ignore_index=True)
    return combined_df



dossier = "donnees/factures_raw"
df_final = process_all_factures(dossier)
print("\n=== Dataframe combiné ===")
print(df_final)

# Optionnel : sauvegarde dans un CSV
os.makedirs("donnees/factures_processed", exist_ok=True)
df_final.to_csv("donnees/factures_processed/factures_combined.csv", index=False)


# #debug
# text = extract_text_from_pdf("donnees/factures_raw/facture_2.pdf")
# print(text)