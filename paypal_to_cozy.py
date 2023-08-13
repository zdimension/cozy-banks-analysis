import json
from math import isnan
import os

import pandas as pd
from datetime import datetime
from banks.client import parser, parse_args

parser.add_argument("tsv_file", help="TSV file to import")
parser.add_argument("--cutoff",
                    help="Cutoff date (inclusive) in YYYY-MM-DD format")
parser.add_argument("--vendor", help="Account vendor ID", required=True)
parser.add_argument("--account", help="Account ID", required=True)
args = parse_args()

df = pd.read_csv(args.tsv_file, sep="\t", encoding="utf-8", decimal=",")

# remove all rows where "État" is not "Terminé" or "En attente"
# surprisingly, we have to take in account "En attente"
df = df[df["État"].isin(["Terminé", "En attente"])]

# remove all rows where "Impact sur le solde" is not "Crédit" or "Débit"
df = df[df["Impact sur le solde"].isin(["Crédit", "Débit"])]

# write to csv
df.to_csv("paypal_to_cozy.csv")


def dmy_to_ymd(a):
    """
    dd/mm/yyyy to yyyy-mm-dd
    """
    d, m, y = tuple(map(int, a.split("/")))
    return f"{y:04d}-{m:02d}-{d:02d}"


df["Date"] = df["Date"].apply(dmy_to_ymd)

if args.cutoff:
    df = df[df["Date opération"] < args.cutoff]


def get_date(row):
    ymd = row["Date"]  # 2019-12-31
    hms = row["Heure"]  # 12:34:56
    tz = row["Fuseau horaire"]  # CEST, CET, UTC, etc.

    dt = datetime.strptime(f"{ymd} {hms} {tz}", "%Y-%m-%d %H:%M:%S %Z")
    return dt.isoformat()


def get_label(row):
    nom = row["Nom"]
    typ = row["Type"]
    lbl = row["Titre de l'objet"]

    if type(nom) == float:
        nom = ""
    if type(typ) == float:
        typ = ""
    if type(lbl) == float or lbl == "1":
        lbl = ""

    lbl = lbl.replace("?dition", "Édition")  # damn accents

    # separate with dashes
    return " - ".join(filter(None, [lbl, nom, typ]))


def fix_amount(a):
    if type(a) == float and isnan(a):
        return 0
    return a


jobj = pd.DataFrame()
# Note: maybe use "Avant commission" instead?
jobj["amount"] = df["Net"].apply(fix_amount)
jobj["account"] = args.account
jobj["vendorAccountId"] = args.vendor
jobj["rawDate"] = df["Date"]
jobj["originalBankLabel"] = df.apply(get_label, axis=1)
jobj["label"] = jobj["originalBankLabel"]

jobj["toCategorize"] = True
jobj["isActive"] = True
jobj["currency"] = df["Devise"]
jobj["date"] = df.apply(get_date, axis=1)
jobj["realisationDate"] = jobj["date"]
jobj["vendorId"] = df["Numéro de transaction"]

recs = jobj.to_dict(orient="records")
print(len(recs), "operations")
res_obj = {
    "io.cozy.bank.operations":
    [{k: v
      for k, v in rec.items() if v is not None} for rec in recs]
}
with open("paypal_to_cozy.json", "w", encoding="utf-8") as f:
    json.dump(res_obj, f, indent=2)

print("Total amount:", sum(jobj["amount"]))

print("You can now run:")
print(
    f"ach --url {os.environ.get('BASE_URL', '<your cozy URL>')} import paypal_to_cozy.json"
)
