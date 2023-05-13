# coding: utf-8

from collections import defaultdict

import pyperclip

from banks.client import get_docs
from banks.cozy_data import CAT, CATNAMES

accs = get_docs("io.cozy.bank.accounts")
ops = get_docs("io.cozy.bank.operations")

for acc in accs:
    acc["owner"] = acc["shortLabel"].split(" ")[0]

for op in ops:
    op["category"] = next(filter(
        None, (op.get(name, None) for name in ("manualCategoryId", "cozyCategoryId", "automaticCategoryId"))))

ops = [op for op in ops if CAT[op["category"]] not in {
    "investmentBuySell",
    "friendBorrowing",
    "loanCredit",
    "professionalExpenses",
    "creditCardPayment",
    "savings",
    "internalTransfer",
    "excludeFromBudgetCat",
}]

accs = {acc["_id"]: acc for acc in accs}

mat = defaultdict(lambda: 0)
for op in ops:
    try:
        cat = op["category"]
        mat[(accs[op["account"]]["owner"], cat)] += op["amount"]
    except:
        raise

res = ""
for (user, cat), val in mat.items():
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
pyperclip.copy(res)

exit()
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=["A1", "A2", "B1", "B2", "C1", "C2"],
        color="blue"
    ),
    link=dict(
        # indices correspond to labels, eg A1, A2, A1, B1, ...
        source=[0, 1, 0, 2, 3, 3],
        target=[2, 3, 3, 4, 4, 5],
        value=[8, 4, 2, 8, 4, 2]
    ))])

fig.update_layout(title_text="Basic Sankey Diagram", font_size=10)
fig.show()
