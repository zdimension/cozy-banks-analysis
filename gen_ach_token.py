# coding: utf-8

from banks.client import *

with open("token.js", "w") as fp:
    fp.write(
        f'module.exports = {{ token: "{dotenv.get_key(dotenv_file, "TOKEN")}" }}'
    )

print("Test by doing:")
print(f"ach -t token.js --url {os.environ.get('BASE_URL', '<your cozy URL>')} export io.cozy.bank.accounts")