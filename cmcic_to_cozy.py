import argparse
import json
import os

import pandas as pd

from banks.cozy_data import CAT

parser = argparse.ArgumentParser()
parser.add_argument("csv_file", help="CSV file to import")
parser.add_argument("--cutoff", help="Cutoff date (inclusive) in YYYY-MM-DD format")
parser.add_argument("--vendor", help="Account vendor ID", required=True)
parser.add_argument("--account", help="Account ID", required=True)
args = parser.parse_args()

df = pd.read_csv(args.csv_file, sep=";", encoding="utf-8", decimal=",")


def dmy_to_ymd(a):
    """
    dd/mm/yyyy to yyyy-mm-dd
    """
    d, m, y = tuple(map(int, a.split("/")))
    return f"{y:04d}-{m:02d}-{d:02d}"


df["Date opération"] = df["Date opération"].apply(dmy_to_ymd)

if args.cutoff:
    df = df[df["Date opération"] < args.cutoff]


def cat_cmut_to_cozy(cmut):
    dic = {
        "Vie quotidienne @ Shopping": "shoppingECommerce",
        "Alimentation @ Snacks / repas au travail": "snaksAndworkMeals",
        "Loisirs @ Passion": "hobbyAndPassion",
        "Alimentation @ Grande surface": "supermarket",
        "Alimentation @ Petit commerçant": None,
        "Epargne @ Bourse / titres": "allocations",
        "Vie quotidienne @ Habillement": "dressing",
        "Loisirs @ Sorties / restaurant": "restaurantsAndBars",
        "Véhicule @ Entretien": None,
        "Hors budget @ Virements internes": None,
        "Autres revenus @ Autres revenus, divers": None,
        "Autres dépenses @ Autres dépenses, divers": None,
        "Vacances / weekend @ Transport": None,
        "Revenus de placement @ Revenu foncier": None,
        "Vie quotidienne @ Transport / taxi / location": None,
        "Véhicule @ Parking / péage": None,
        "Véhicule @ Véhicule, divers": None,
        "Logement / maison @ Energies / eau": "power",
        "Vie quotidienne @ Retrait d'argent": "atm",
        "Loisirs @ Sport": "activityEquipments",
        "Autres dépenses @ Frais bancaires": "bankFees",
        "Vie quotidienne @ Soin du corps / coiffeur / cosmétique": "personalCare",
        "Logement / maison @ Loyer / charges": "rent",
        "Santé @ Pharmacie": "healthExpenses",
        "Logement / maison @ Assurance": "homeInsurance",
        "Famille @ Don / cadeaux": "donationsReceived",
        "Famille @ Allocations": "allocations",
        "Autres dépenses @ Cartes crédit / crédits Conso": None,
        "A catégoriser @ A catégoriser, divers": None,
        "Numérique @ Internet (ou triple play)": "telecom",
        "Revenus professionnels @ Salaire / prime": "activityIncome",
        "Autres dépenses @ Frais professionnels": None,
        "Loisirs @ Culture": None,
        "Autres dépenses @ Assurances / prévoyance / dépendance": None,
        "Loisirs @ Loisirs, divers": None,
        "Vacances / weekend @ Hébergement / restauration": None,
        "Logement / maison @ Equipement / ameublement": "homeHardware",
        "Numérique @ Achats high tech": "electronicsAndMultimedia",
        "Autres revenus @ Revenus exceptionnels": None,
        "Autres revenus @ Vente": "additionalIncome",
        "Autres revenus @ Remboursements Santé": "healthExpenses",
        "Numérique @ Numérique, divers": None,
        "Numérique @ Téléphonie mobile": "telecom",
        "Santé @ Médecin": "healthExpenses",
        "Santé @ Prestations médicales / hospitalisation": "healthExpenses",
        "Logement / maison @ Entretien / bricolage": "homeImprovement",
        "A catégoriser @ Remise de chèque": None,
        "Enfants & Scolarité @ Habillement / équipement": None,
        "Impôts / taxes @ Impôt sur le revenu": "incomeTax",
        "Epargne @ Epargne, divers": None,
        "Autres dépenses @ Cadeaux": "giftsOffered",
        "A catégoriser @ Virements": None,
        "Revenus de placement @ Revenus de placement, divers": None,
        "Logement / maison @ Travaux": "homeImprovement",
        "A catégoriser @ Virements reçus": None,
        "A catégoriser @ Chèques": None,
        "Autres dépenses @ Dons caritatifs": None,
        "Hors budget @ Hors budget, divers": None,
        "Numérique @ Téléphonie fixe": "telecom",
        "Santé @ Lunettes / appareillages": None,
        "Famille @ Famille, divers": None,
        "Enfants & Scolarité @ Frais de scolarité et accessoires": "tuition",
        "Vie quotidienne @ Café / jeux / tabac": None,
        "Enfants & Scolarité @ Jeux et divertissements": None,
        "Impôts / taxes @ Impôt / taxes, divers": None,
        "Véhicule @ Carburant": None,
        "Alimentation @ Alimentation, divers": None,
        "Epargne @ Epargne disponible": None,
        "Revenus de placement @ Intérêts": "interests"
    }
    if cmut not in dic:
        raise ValueError(f"Unknown category {cmut}")
    if dic[cmut] is None:
        return None
    try:
        cozy_id = [k for k, v in CAT.items() if v == dic[cmut]][0]
    except:
        print("should not happen", cmut)
        raise
    return cozy_id


def fixlbl(l):
    l = l.replace("VIR ", "")
    return l


jobj = pd.DataFrame()
jobj["amount"] = df["Montant"]
jobj["account"] = args.account
jobj["vendorAccountId"] = args.vendor
jobj["rawDate"] = df["Date opération"]
jobj["originalBankLabel"] = df["Libellé opération"]
jobj["label"] = df["Libellé opération"].apply(fixlbl)
catNames = (df["Catégorie"] + " @ " + df["Sous-catégorie"]).apply(cat_cmut_to_cozy)
jobj["manualCategoryId"] = catNames
jobj["toCategorize"] = catNames.isnull()
jobj["isActive"] = True
jobj["currency"] = "EUR"
jobj["date"] = df["Date opération"] + "T12:00:00.000Z"
jobj["realisationDate"] = jobj["date"]

recs = jobj.to_dict(orient="records")
print(len(recs), "operations")
res_obj = {"io.cozy.bank.operations": [{k: v for k, v in rec.items() if v is not None} for rec in recs]}
with open("cmcic_to_cozy.json", "w", encoding="utf-8") as f:
    json.dump(res_obj, f, indent=2)

print("You can now run:")
print(f"ach -t token.js --url {os.environ.get('BASE_URL', '<your cozy URL>')} import cmcic_to_cozy.json")
