import argparse
import os
import pathlib
import subprocess
import tempfile

import requests

from .cozy_data import CAT
from .env import *

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    print("BASE_URL environment variable must be set")
    exit(1)

if not BASE_URL.endswith("/"):
    BASE_URL += "/"

client = requests.Session()

ACH_PATH = os.environ.get("ACH_PATH", "ACH")

USE_SHELL = os.name == "nt"


def update_token(force=False):
    if force or not (token := os.environ.get("TOKEN")):
        try:
            tmp_dir = pathlib.Path(tempfile.gettempdir())
            for f in tmp_dir.glob(".ach-token*.json"):
                print("Deleting old token file", f, "...")
                f.unlink()
        except:
            print("Unable to delete ACH token file")
        cmdline = [
            ACH_PATH, "token", "--url", BASE_URL, "io.cozy.bank.accounts",
            "io.cozy.bank.operations"
        ]
        try:
            token = subprocess.check_output(
                cmdline, shell=USE_SHELL).decode("utf-8").strip()
        except FileNotFoundError:
            print("ACH not found, please install it")
            exit(1)
        os.environ["TOKEN"] = token
    dotenv.set_key(dotenv_file, "TOKEN", token)
    client.headers.update({"Authorization": "Bearer " + token})
    return token


update_token()


def get_docs(doctype):
    """
    Get all documents of a given doctype
    """
    req_url = BASE_URL + "data/" + doctype + "/_all_docs?include_docs=true"
    log(req_url)
    r = client.get(req_url)
    log(r)

    # check if the request is successful and decode JSON
    if r.status_code != 200:
        if "Expired token" in r.text:
            log("Token expired, getting new one")
            update_token(True)
            return get_docs(doctype)

        print("Error while fetching documents")
        print(r.text)
        exit(1)

    # decode JSON
    return [d["doc"] for d in r.json()["rows"] if "_design" not in d["id"]]


def cozyize(doc):
    return {k: v for k, v in doc.items() if not k.startswith("__")}


def delete_many(doctype, docs):
    """
    Delete documents
    """
    req_url = BASE_URL + "data/" + doctype + "/_bulk_docs"
    log(req_url)
    docs = [{**cozyize(doc), "_deleted": True} for doc in docs]
    r = client.post(req_url, json={"docs": docs})
    log(r)

    if r.status_code != 201:
        print("Error while deleting documents")
        print(r.text)
        exit(1)

def update_many(doctype, docs):
    """
    Update documents
    """
    req_url = BASE_URL + "data/" + doctype + "/_bulk_docs"
    log(req_url)
    docs = [cozyize(doc) for doc in docs]
    r = client.post(req_url, json={"docs": docs})
    log(r)

    if r.status_code != 201:
        print("Error while updating documents")
        print(r.text)
        exit(1)


def get_accounts():
    res = get_docs("io.cozy.bank.accounts")
    for acc in res:
        acc["__displayLabel"] = acc.get("shortLabel",
                                        acc.get("label", "<NO LABEL>"))
    return res


def get_category(op):
    if manual := op.get("manualCategoryId"):
        return manual

    # same logic and constants as in Banks
    # from https://github.com/cozy/cozy-libs/blob/master/packages/cozy-doctypes/src/banking/BankTransaction.js
    LOCAL_MODEL_USAGE_THRESHOLD = 0.8
    GLOBAL_MODEL_USAGE_THRESHOLD = 0.15

    if (local := op.get("localCategoryId")) and op.get(
            "localCategoryProba", -1) > LOCAL_MODEL_USAGE_THRESHOLD:
        return local

    if (cozy := op.get("cozyCategoryId")) and op.get(
            "cozyCategoryProba", -1) > GLOBAL_MODEL_USAGE_THRESHOLD:
        return cozy

    if local is None and cozy is None:
        return "0"

    return op.get("automaticCategoryId", "0")


def id_to_dict(l):
    return {acc["_id"]: acc for acc in l}

def op_sort_key(o):
    rawDate = o["date"]
    updateDate = "0"
    if "cozyMetadata" in o:
        updateDate = o["cozyMetadata"]["updatedAt"][:13]  # only get dd/mm/yyyy and hh
    opAmount = -o["amount"]  # larger operations before smaller ones in case of internal transfer
    return rawDate, opAmount, updateDate


def get_operations():
    res = get_docs("io.cozy.bank.operations")
    if no_amount := [op for op in res if op.get("amount") is None]:
        log("Some operations have no `amount` field:")
        for op in no_amount:
            log(op["_id"], op["date"], op["label"])
            op["amount"] = 0
        log("The script will assume the amount is zero.")
    for op in res:
        op["__categoryId"] = get_category(op)
        op["__categoryName"] = CAT[op["__categoryId"]]
    res.sort(key=op_sort_key)
    return res


parser = argparse.ArgumentParser()
# --silent / -s
parser.add_argument("--silent",
                    "-s",
                    help="Don't print warnings",
                    action="store_true")

args: argparse.Namespace


def parse_args():
    global args
    args = parser.parse_args()
    return args


def log(*c):
    if args and not args.silent:
        print(*c)
