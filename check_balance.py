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

headers = ["Account", "Balance", "Computed balance", "Difference", "Op count"]
table_data = []
for acc in sorted(accounts, key=lambda a: a["__displayLabel"]):
    balance = acc["balance"]
    computed_balance = sum(u["amount"] for u in acc_op.get(acc["id"], ()))
    difference = round(balance - computed_balance + 1e-7, 2)
    op_count = len(acc_op.get(acc["id"], ()))
    table_data.append((acc["__displayLabel"], balance, computed_balance,
                       difference, op_count))

table_data.append(("**** Total ****", sum(a["balance"] for a in accounts),
                   sum(o["amount"] for o in operations)))

print(tabulate(table_data, headers=headers, floatfmt=".2f"))
