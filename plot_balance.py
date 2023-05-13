# coding: utf-8
from collections import defaultdict
from datetime import datetime

import numpy as np
import plotly.graph_objects as go

from banks.client import get_accounts, get_operations

accounts = get_accounts()
operations = get_operations()


def get_date(o):
    first = o["date"]
    if "cozyMetadata" in o:
        return first, o["cozyMetadata"]["updatedAt"]
    else:
        return first, "0"


operations.sort(key=get_date)

# plot account balance through time (cumulative sum of operation amount)

# group operations by account
ops_by_acc = defaultdict(list)
for o in operations:
    ops_by_acc[o["account"]].append(o)

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
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        mode="lines",
        name=account["label"],
        line={"shape": "hv"},
    ))

fig.show()
