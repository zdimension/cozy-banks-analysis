import json
import os
from typing import Optional

import pandas as pd

from banks.client import parser, parse_args


def read_csv(csv_file: str, cutoff: Optional[str] = None) -> pd.DataFrame:
    df = pd.read_csv(csv_file,
                     sep=";",
                     encoding="utf-8",
                     decimal=",",
                     thousands=' ')

    if cutoff:
        df = df[df["dateOp"] < args.cutoff]

    return df


def convert(csv: pd.DataFrame, account: str, vendor: str):

    def fixlbl(l: str):
        REMOVE = [
            "VIR SEPA",
            "VIR",
            "PRLV",
            "CARTE",
            "RETRAIT",
            "AVOIR",
        ]

        for r in REMOVE:
            l = l.replace(r, "").strip()

        return l

    jobj = pd.DataFrame()
    # float
    jobj["amount"] = csv["amount"]
    jobj["account"] = account
    jobj["vendorAccountId"] = vendor
    jobj["rawDate"] = csv["dateOp"]
    jobj["originalBankLabel"] = csv["label"]
    jobj["label"] = csv["label"].apply(fixlbl)
    jobj["toCategorize"] = True
    jobj["isActive"] = True
    jobj["currency"] = "EUR"
    jobj["date"] = csv["dateOp"] + "T12:00:00.000Z"
    jobj["realisationDate"] = jobj["date"]

    return jobj.to_dict(orient="records")


def main():
    parser.add_argument("csv_file", help="CSV file to import")
    parser.add_argument("--cutoff",
                        help="Cutoff date (inclusive) in YYYY-MM-DD format")
    parser.add_argument("--vendor", help="Account vendor ID", required=True)
    parser.add_argument("--account", help="Account ID", required=True)
    args = parse_args()

    csv = read_csv(args.csv_file, args.cutoff)
    recs = convert(csv, args.account, args.vendor)

    print(len(recs), "operations")
    res_obj = {
        "io.cozy.bank.operations":
        [{k: v
          for k, v in rec.items() if v is not None} for rec in recs]
    }

    with open("bourso_to_cozy.json", "w", encoding="utf-8") as f:
        json.dump(res_obj, f, indent=2)

    print("You can now run:")
    print(
        f"ach -t token.js --url {os.environ.get('BASE_URL', '<your cozy URL>')} import bourso_to_cozy.json"
    )


if __name__ == "__main__":
    main()
