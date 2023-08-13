# coding: utf-8
from IPython import embed

from banks.client import parse_args, get_accounts, get_operations

parse_args()

accounts = get_accounts()
operations = get_operations()

embed()