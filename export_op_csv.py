import pandas as pd

from banks.client import parser, parse_args, get_accounts, get_operations

parser.add_argument("account", help="Account to export", nargs="?")
args = parse_args()

if args.account is None:
    for i, a in enumerate(get_accounts()):
        print(f"{i:2d} {a['__displayLabel']}")
    exit()

account = get_accounts()[int(args.account)]

ops = (o for o in get_operations() if o["account"] == account["_id"])

df = pd.DataFrame([
    [o["date"], o["label"], o["amount"]] for o in ops
], columns=["date", "label", "amount"])

df["cumsum_xl"] = [f"=SOMME($C$1:$C{i+2})" for i in range(len(df))]
final_balance = sum(df["amount"])
df["cumsumm_th_xl"] = [f"=SOMME($C$1:$C{i+2})-SOMME($C$1:$C${len(df)+1})" for i in range(len(df))]
df.to_csv("export_op_csv.csv", index=False, decimal=",", sep=";", date_format="%Y-%m-%d", encoding="utf-8")
