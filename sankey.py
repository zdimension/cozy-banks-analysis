# coding: utf-8
import argparse
from collections import defaultdict

from utils import copy_to_clipboard

from banks.client import get_operations, get_accounts, parser, parse_args
from banks.cozy_data import CAT, CATNAMES

parser.add_argument("--balance", "-b", help="Show balance", action="store_true")
parser.add_argument("--owner", help="Assume account names are in the form 'Bob Checkings' and group by 'Bob'",
                    action="store_true")
parser.add_argument("--from", "-f", help="Filter operations from this date")
parser.add_argument("--to", "-t", help="Filter operations to this date")
args = parse_args()

accs = get_accounts()
ops = get_operations()

if getattr(args, "from"):
    ops = [op for op in ops if op["date"] >= getattr(args, "from")]

if args.to:
    ops = [op for op in ops if op["date"] <= args.to]

if args.owner:
    for acc in accs:
        acc["owner"] = acc["__displayLabel"].split(" ")[0]
else:
    for acc in accs:
        acc["owner"] = "Bank"

accs = {acc["_id"]: acc for acc in accs}

mat = defaultdict(lambda: defaultdict(lambda: 0))
for op in ops:
    try:
        cat = op["__categoryId"]
        mat[accs[op["account"]]["owner"]][cat] += op["amount"]
    except:
        raise


res = ""
for user, cats in mat.items():
    if args.balance:
        total = round(sum(cats.values()), 2)
        if total > 0:
            res += f"{user} [{total}] Balance {user}\n"
        elif total < 0:
            res += f"Balance (-) {user} [{-total}] {user}\n"
    for cat, val in cats.items():
        val = round(val, 2)
        if val == 0:
            continue
        dst, src = user, CATNAMES[CAT[cat]]
        if val < 0:
            src = "-" + src
            src, dst = dst, src
            val = -val
        else:
            src = "+" + src
        res += f"{src} [{round(val, 2)}] {dst}\n"
copy_to_clipboard(res)
