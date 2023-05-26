# coding: utf-8
from itertools import groupby

from tabulate import tabulate

from banks.client import get_operations, get_accounts, parse_args, parser

parser.add_argument("--until", "-u", help="Only show operations until this date")
args = parse_args()
accounts = get_accounts()
operations = get_operations()
if args.until:
    operations = [op for op in operations if op["date"] <= args.until]
operations.sort(key=lambda o: o["account"])
acc_op = {k: list(v) for k, v in groupby(operations, lambda o: o["account"])}

print(tabulate(
    [
        (
            acc["__displayLabel"],
            b := acc["balance"],
            cb := sum(u["amount"] for u in acc_op.get(acc["id"], ())),
            round(b - cb + 1e-7, 2)
        )
        for acc in accounts
    ],
    headers=["Account", "Balance", "Computed balance", "Difference"],
    floatfmt=".2f"
))
