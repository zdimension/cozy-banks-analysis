# coding: utf-8
from banks.client import get_accounts, get_operations, parse_args
import re
from tabulate import tabulate, SEPARATING_LINE
from datetime import datetime

from scipy.optimize import minimize

stocks = re.compile(r"PEE|PEA (?!Esp)") # edit this for your accounts

parse_args()
accs = get_accounts()
ops = get_operations()

rates = {
    "Livret A": {"2023-02-01": 0.03},
    "Livret Jeune": {"2023-02-01": 0.04},
    "LEP": {"2023-08-01": 0.06, "2024-02-01": 0.05, "2024-08-01": 0.04},
}

accs_std = [(a, v) for a in accs for k, v in rates.items() if k in a["__displayLabel"]]
accs = [a for a in accs if stocks.search(a["__displayLabel"])]

def get_halfmonth(date):
    y, m, d = map(int, date[:10].split("-"))
    halfmonth = 24 * y + 2 * (m - 1) + (d > 15) + 1
    return halfmonth

HM_NOW = get_halfmonth(datetime.now().isoformat()) + 1


def compute_final_balance(rates, acc_ops, until=HM_NOW):
    balance = 0
    interest = 0
    hm = get_halfmonth(acc_ops[0]["date"])
    current_op = 0
    total_interest = 0
    if type(rates) == dict:
        entries = [(get_halfmonth(d), r) for d, r in reversed(rates.items())]
        def getrate(hm):
            for d, r in entries:
                if hm >= d:
                    return r
    else:
        def getrate(hm):
            return rates
    while hm < until:
        rate = getrate(hm)
        min_balance = balance
        while (current_op < len(acc_ops) and
               (get_halfmonth(acc_ops[current_op]["date"])) == hm):
            balance += acc_ops[current_op]["amount"]
            if balance < min_balance:
                min_balance = balance
            current_op += 1

        generated = min_balance * rate / 24
        interest += generated
        total_interest += generated

        if (hm + 0) % 24 == 0:
            balance += interest
            interest = 0

        hm += 1

    balance += interest
    return total_interest

def process():
    for acc in accs + [a for a, _ in accs_std]:
        acc_ops = [o for o in ops if o["account"] == acc["_id"]]
        acc_ops.sort(key=lambda o: (o["date"], o["amount"]))
        acc["_ops"] = acc_ops
        acc["_invested"] = sum(o["amount"] for o in acc_ops)

    for acc in accs:
        acc_ops = acc["_ops"]
        current_gain = acc["balance"] - acc["_invested"]

        best_rate = minimize(lambda r: abs(compute_final_balance(r[0], acc_ops) - current_gain), 1).x[0]
        #best_rate=1
        # sanity check
        assert abs(compute_final_balance(best_rate, acc_ops) - current_gain) < 1e-2

        yield (acc["__displayLabel"], acc["_invested"], best_rate, current_gain,
            compute_final_balance(0.03, acc_ops))

    yield SEPARATING_LINE

    cur_year = datetime.now().year
    until = HM_NOW
    #cur_year = 2024
    #until = get_halfmonth(f"{cur_year}-12-31") + 1
    for acc, ratehist in accs_std:
        year_start = f"{cur_year}-01-01"
        acc_ops = [o for o in acc["_ops"] if year_start <= o["date"] <= f"{cur_year}-12-31" and "INTERETS" not in o["originalBankLabel"]]
        previous = sum(o["amount"] for o in acc["_ops"] if o["date"] < year_start)
        if previous < 0.01:
            continue
        acc_ops.insert(0, {"date": f"{cur_year-1}-12-31", "amount": previous})
        due_gains = compute_final_balance(ratehist, acc_ops, until)
        yield (acc["__displayLabel"], acc["balance"], list(ratehist.values())[-1], due_gains,
            compute_final_balance(0.03, acc_ops, until))

print(tabulate(process(),
               headers=["Account", "Investment", "Equivalent rate", "Actual gain", "Livret A (3%)"],
               floatfmt=("s", ".2f", ".1%", ".2f", ".2f")
               ))

