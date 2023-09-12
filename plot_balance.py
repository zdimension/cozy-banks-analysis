# coding: utf-8
from collections import defaultdict
from datetime import datetime
from itertools import groupby

import numpy as np
import plotly.graph_objects as go

from banks.client import get_accounts, get_operations, parser, parse_args

parser.add_argument("--by-op", "-o", help="One point by operation (sensitive to operation time)", action="store_true")
parser.add_argument("--exclude", "-x", help="Exclude accounts", nargs="*", action="append")
parser.add_argument("--exclude-list", help="List accounts for exclusion", action="store_true")
args = parse_args()
accounts = get_accounts()
operations = get_operations()

if args.exclude_list:
    for i, a in enumerate(accounts):
        print(f"{i:2d} {a['__displayLabel']}")
    exit()

if args.exclude:
    exclude = {int(i) for l in args.exclude for i in l}
    accounts = [a for i, a in enumerate(accounts) if i not in exclude]

if not args.by_op:
    # for each operation keep only the date component
    for o in operations:
        o["date"] = o["date"][:10]

# group operations by account
ops_by_acc = defaultdict(list)
for o in operations:
    ops_by_acc[o["account"]].append(o)
    ops_by_acc[None].append(o)

if not args.by_op:
    for k, v in ops_by_acc.items():
        ops_by_acc[k] = [{"date": k, "amount": sum(o["amount"] for o in g)} for k, g in groupby(v, lambda o: o["date"])]

accounts = accounts + [{"_id": None, "__displayLabel": "Total", "balance": sum(a.get("balance", 0) for a in accounts)}]

fig = go.Figure()
for account in accounts:
    # get operations for this account
    account_operations = ops_by_acc[account["_id"]]
    # compute cumulative sum of operation amount
    y = np.cumsum([o["amount"] for o in account_operations])
    y = np.append(y, account["balance"])
    # plot
    x = [np.datetime64(o["date"]) for o in account_operations]
    x.append(np.datetime64(datetime.now().isoformat()))
    # step chart
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=account["__displayLabel"],
            line={"shape": "hv"},
        ))

fig.show()
