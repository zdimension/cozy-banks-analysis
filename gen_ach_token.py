# coding: utf-8

from banks.client import *

with open("token.txt", "w") as fp:
    fp.write(f'module.exports = {{ token: "{dotenv.get_key(dotenv_file, "TOKEN")}" }}')
