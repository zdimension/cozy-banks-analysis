# coding: utf-8
from collections import defaultdict
from datetime import datetime

import numpy as np
import plotly.graph_objects as go

from banks.client import get_accounts, get_operations, parse_args

parse_args()
accounts = get_accounts()
operations = get_operations()

# plot account balance through time (cumulative sum of operation amount)

# group operations by account
ops_by_acc = defaultdict(list)
for o in operations:
    ops_by_acc[o["account"]].append(o)
    ops_by_acc[None].append(o)

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
