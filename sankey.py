# coding: utf-8

from collections import defaultdict

from utils import copy_to_clipboard

from banks.client import get_operations, get_accounts
from banks.cozy_data import CAT, CATNAMES

accs = get_accounts()
ops = get_operations()

for acc in accs:
    acc["owner"] = acc["__displayLabel"].split(" ")[0]  # TODO: ?

ops = [
    op for op in ops if CAT[op["__categoryId"]] not in {
        "investmentBuySell",
        "friendBorrowing",
        "loanCredit",
        "professionalExpenses",
        "creditCardPayment",
        "savings",
        "internalTransfer",
        "excludeFromBudgetCat",
    }
]

accs = {acc["_id"]: acc for acc in accs}

mat = defaultdict(lambda: 0)
for op in ops:
    try:
        cat = op["__categoryId"]
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
copy_to_clipboard(res)
