# coding: utf-8
import datetime
from itertools import groupby

from tabulate import tabulate

from banks.client import get_operations, get_accounts, parse_args, parser

import currency_converter

parser.add_argument("--until",
                    "-u",
                    help="Only show operations until this date")

parser.add_argument(
    "--curconv",
    "-C",
    help=
    "Convert currencies to EUR. Note that this will not be completely acurate.",
    action="store_true")

args = parse_args()
accounts = get_accounts()
operations = get_operations()
if args.until:
    operations = [op for op in operations if op["date"] <= args.until]
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

print(
    tabulate([(acc["__displayLabel"], b := acc["balance"], cb := sum(
        u["amount"]
        for u in acc_op.get(acc["id"], ())), round(b - cb + 1e-7, 2))
              for acc in accounts],
             headers=["Account", "Balance", "Computed balance", "Difference"],
             floatfmt=".2f"))
