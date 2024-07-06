# coding: utf-8
from banks.client import get_accounts, get_operations, parse_args
import re
from tabulate import tabulate
from datetime import datetime

from scipy.optimize import minimize

stocks = re.compile(r"PEE|PEA CW8") # edit this for your accounts

parse_args()
accs = get_accounts()
ops = get_operations()

accs = [a for a in accs if stocks.search(a["__displayLabel"])]

def get_halfmonth(date):
    y, m, d = map(int, date[:10].split("-"))
    halfmonth = 24 * y + 2 * (m - 1) + (d > 15)
    return halfmonth

HM_NOW = get_halfmonth(datetime.now().isoformat()) + 1

def process():
    for acc in accs:
        acc_ops = [o for o in ops if o["account"] == acc["_id"]]
        acc_ops.sort(key=lambda o: o["date"])
        invested = sum(o["amount"] for o in acc_ops)
        current_gain = acc["balance"] - invested

        def compute_rate_gain(rate):
            balance = 0
            interest = 0
            current = 0
            hm = get_halfmonth(acc_ops[0]["date"])
            current_op = 0
            while hm < HM_NOW:
                while current_op < len(acc_ops) and get_halfmonth(acc_ops[current_op]["date"]) == hm:
                    balance += acc_ops[current_op]["amount"]
                    current_op += 1

                if hm % 24 == 0:
                    balance += interest
                    interest = 0

                if hm != current:
                    interest += balance * rate / 24
                hm += 1

            balance += interest
            return balance - invested

        best_rate = minimize(lambda r: abs(compute_rate_gain(r) - current_gain), 1.1).x[0]

        # sanity check
        assert abs(compute_rate_gain(best_rate) - current_gain) < 1e-2

        yield (acc["__displayLabel"], invested, best_rate, current_gain,
            compute_rate_gain(0.03))

print(tabulate(process(),
               headers=["Account", "Investment", "Equivalent rate", "Actual gain", "Livret A (3%)"],
               floatfmt=("s", ".2f", ".1%", ".2f", ".2f")
               ))

