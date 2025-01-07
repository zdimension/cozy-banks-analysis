# coding: utf-8
from collections import defaultdict
from datetime import datetime
from itertools import groupby
from bisect import bisect, bisect_left

import numpy as np
import plotly.graph_objects as go

from banks.client import get_accounts, get_operations, parser, parse_args, get_balance_histories

parser.add_argument("--by-op", "-b", help="One point by operation (sensitive to operation time)", action="store_true")
parser.add_argument("--exclude", "-x", help="Exclude accounts", nargs="*", action="append")
parser.add_argument("--exclude-list", help="List accounts for exclusion", action="store_true")
parser.add_argument("--owner", "-o", help="Only show operations for this owner (first word of account name)")
parser.add_argument("--owner-totals", help="Show totals for each owner", action="store_true")
args = parse_args()
accounts = list(get_accounts())
operations = get_operations()

if args.owner:
    args.owner += " "
    accounts = [a for a in accounts if a["__displayLabel"].startswith(args.owner)]

if args.exclude_list:
    for i, a in enumerate(accounts):
        print(f"{i:2d} {a['__displayLabel']}")
    exit()

if args.exclude:
    exclude = {int(i) for l in args.exclude for i in l}
    accounts = [a for i, a in enumerate(accounts) if i not in exclude]

acc_ids = {a["_id"] for a in accounts}
operations = [o for o in operations if o["account"] in acc_ids]

if args.owner_totals:
    owners = defaultdict(list)
    for a in accounts:
        owners[a["__displayLabel"].split()[0]].append(a)

account_dict = {a["_id"]: a for a in accounts}

# group operations by account
ops_by_acc = defaultdict(list)
for o in operations:
    ops_by_acc[o["account"]].append(o)

histories = get_balance_histories()

for account in accounts:
    ops = ops_by_acc[account["_id"]]
    cum = np.cumsum([o["amount"] for o in ops])
    for o, cumulated in zip(ops, cum):
        o["cumulated"] = cumulated
    if account.get("type") == "LongTermSavings" and (acc_hist := histories.get(account["_id"])):
        for date, balance in acc_hist.items():
            date += "T23:59:00"
            inspos = bisect(ops, date, key=lambda o: o["date"])
            bal_bef = (ops[inspos - 1]["cumulated"] if inspos else 0)
            delta = (balance - bal_bef)
            ops.insert(inspos, {"date": date, "amount": delta, "cumulated": balance, "right": balance, "label": "Sync history"})
            for o in ops[inspos + 1:]:
                o["cumulated"] = (o["cumulated"] + delta)

from tabulate import tabulate
oo = ops_by_acc[[a for a in accounts if "CW8" in a["__displayLabel"]][0]["_id"]]
newcum = np.cumsum([o["amount"] for o in oo])
print(tabulate([[o["date"], o["amount"], o["cumulated"], o.get("right", ""), o.get("label", "")] for o in oo], headers=["date", "amount", "cumulated", "right", "label"],
               floatfmt=".2f"))
for noo in zip(oo, newcum):
    assert round(noo[0]["cumulated"], 2) == round(noo[1], 2)

def group_date(k, v):
    # for each operation keep only the date component
    v.sort(key=lambda o: o["date"])
    for o in v:
        o["date"] = o["date"][:10]
    ops_by_acc[k] = [{"date": k, "amount": sum(o["amount"] for o in g)} for k, g in groupby(v, lambda o: o["date"])]

if not args.by_op:
    for k, v in ops_by_acc.items():
        group_date(k, v)

accounts.sort(key=lambda a: a["__displayLabel"])

accounts.append({"_id": None, "__displayLabel": "Total", "balance": sum(a.get("balance", 0) for a in accounts)})

for k, v in list(ops_by_acc.items()):
    for o in v:
        ops_by_acc[account_dict[k]["__displayLabel"].split()[0]].append(o)
        ops_by_acc[None].append(o)

group_date(None, ops_by_acc[None])

if args.owner_totals:
    for owner, accs in owners.items():
        accounts.append({"_id": owner, "__displayLabel": f"{owner} total", "balance": sum(a.get("balance", 0) for a in accs)})
        group_date(owner, ops_by_acc[owner])


fig = go.Figure()
for account in accounts:
    account_operations = ops_by_acc[account["_id"]]

    cum = np.cumsum([o["amount"] for o in account_operations])
    by_date = {o["date"]: cumulated for o, cumulated in zip(account_operations, cum)}

    by_date = dict(sorted(by_date.items(), key=lambda x: x[0]))

    y = list(by_date.values())
    x = [np.datetime64(d) for d in by_date.keys()]

    now = np.datetime64(datetime.now().isoformat())
    if now > x[-1]:
        x.append(now)
        y.append(account["balance"])

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
