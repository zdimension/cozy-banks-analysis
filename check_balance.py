# coding: utf-8
import datetime
from itertools import groupby
import dateutil.parser

from tabulate import tabulate

from banks.client import get_operations, get_accounts, parse_args, parser

import currency_converter

parser.add_argument("--after",
                    "-a",
                    help="Only show operations after this date")

parser.add_argument("--before",
                    "-b",
                    help="Only show operations before this date")

parser.add_argument(
    "--curconv",
    "-C",
    help=
    "Convert currencies to EUR. Note that this will not be completely acurate.",
    action="store_true")

parser.add_argument(
    "--show-zero",
    help="Show accounts with zero balance",
    action="store_true")

parser.add_argument(
    "--only-different"
    "-d",
    help="Only show accounts with a difference between computed and stored balance",
    action="store_true"
)

args = parse_args()
accounts = get_accounts()
operations = get_operations()

if args.before:
    before = dateutil.parser.parse(args.before).isoformat()
    operations = [op for op in operations if op["date"] <= before]

if args.after:
    after = dateutil.parser.parse(args.after).isoformat()
    operations = [op for op in operations if op["date"] >= after]

operations.sort(key=lambda o: o["account"])


def convert_ops(operations):
    # convert currency to EUR
    for op in operations:
        if op["currency"] == "EUR":
            continue

        cc = currency_converter.CurrencyConverter(
            fallback_on_missing_rate=True, fallback_on_wrong_date=True)

        date = datetime.datetime.fromisoformat(op["date"])
        eur_amount = cc.convert(op["amount"], op["currency"], "EUR", date=date)
        print(f"{op['amount']} {op['currency']} -> {eur_amount} EUR")

        op["amount"] = eur_amount
        op["currency"] = "EUR"


if args.curconv:
    convert_ops(operations)

acc_op = {k: list(v) for k, v in groupby(operations, lambda o: o["account"])}

def round2(x):
    return round(x + 1e-7, 2)

headers = ["Account", "Balance", "Computed balance", "Difference", "Op count"]
table_data = []
for acc in sorted(accounts, key=lambda a: a["__displayLabel"]):
    balance = acc["balance"] + 0.0001
    computed_balance = sum(u["amount"] for u in acc_op.get(acc["id"], ())) + 0.0001
    difference = round2(balance - computed_balance)
    op_count = len(acc_op.get(acc["id"], ()))
    balance = round2(balance)
    computed_balance = round2(balance)
    if (balance == computed_balance == 0) and not args.show_zero:
        continue
    if (balance == computed_balance) and args.only_different_d:
        continue
    table_data.append((acc["__displayLabel"], balance, computed_balance,
                       difference, op_count))

table_data.append(("**** Total ****", sum(a["balance"] for a in accounts),
                   sum(o["amount"] for o in operations)))

print(tabulate(table_data, headers=headers, floatfmt=".2f"))
