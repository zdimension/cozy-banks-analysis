import os
import subprocess

import requests

from .env import *

BASE_URL = os.environ.get("BASE_URL")
if not BASE_URL:
    print("BASE_URL environment variable must be set")
    exit(1)

if not BASE_URL.endswith("/"):
    BASE_URL += "/"

client = requests.Session()

ACH_PATH = os.environ.get("ACH_PATH", "ACH")


def update_token(force=False):
    if force or not (token := os.environ.get("TOKEN")):
        cmdline = [ACH_PATH, "token", "--url", BASE_URL, "io.cozy.bank.accounts", "io.cozy.bank.operations"]
        token = subprocess.check_output(cmdline, shell=True).decode("utf-8").strip()
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
    print(req_url)
    r = client.get(req_url)
    print(r)

    # check if the request is successful and decode JSON
    if r.status_code != 200:
        if "Expired token" in r.text:
            print("Token expired, getting new one")
            update_token(True)
            return get_docs(doctype)

        print("Error while fetching documents")
        print(r.text)
        exit(1)

    # decode JSON
    return [d["doc"] for d in r.json()["rows"] if "_design" not in d["id"]]


def get_accounts():
    res = get_docs("io.cozy.bank.accounts")
    for acc in res:
        acc["__displayLabel"] = acc.get("shortLabel", acc.get("label", "<NO LABEL>"))
    return res


def get_operations():
    return get_docs("io.cozy.bank.operations")
