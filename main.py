import os
from collections import defaultdict
from datetime import datetime

import numpy as np
import plotly.graph_objects as go
import requests
from dotenv import load_dotenv

# Press Maj+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

BASE_URL = "https://zdimension.mycozy.cloud/"

load_dotenv()

token = os.getenv("TOKEN")
if token is None:
    print("Please set the TOKEN environment variable")
    exit(1)
print(token)

client = requests.Session()
client.headers.update({"Authorization": "Bearer " + token})


def get_docs(doctype):
    """
    Get all documents of a given doctype
    """
    req_url = BASE_URL + "data/" + doctype + "/_all_docs?include_docs=true"
    print(req_url)
    r = client.get(req_url)
    print(r)

    # check if the request is successful and decode JSON
    if r.status_code != 200:
        print("Error while fetching operations")
        print(r.text)
        exit(1)

    # decode JSON
    return [d["doc"] for d in r.json()["rows"] if "_design" not in d["id"]]


accounts = get_docs("io.cozy.bank.accounts")
operations = get_docs("io.cozy.bank.operations")


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
