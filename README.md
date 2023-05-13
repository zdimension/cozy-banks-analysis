# cozy-banks-analysis

This repository contains various scripts to analyze the data exported
from [Cozy Banks](https://cozy.io/fr/features/#bank).

The web interface is really nice but still lacks some advanced features (which doesn't mean it's not a great tool!).

## Usage

`pip install -r requirements.txt` and run one of the scripts below.

**Note:** for all the features to work properly (e.g. automatic token generation), you need to have
[`ach`](https://github.com/cozy/ACH) installed and in your `PATH`.

## Scripts

### `check_balance`

Computes the balance of each account (cumulated sum of transactions) and compares it to the balance given by the bank
connectors. This is useful to make sure your transaction history is complete.

### `cmcic_to_cozy`

Converts a CSV file exported from CIC / Crédit Mutuel "Gestion de Budget" service. This is a trick that allows getting
your transaction history since your account has been opened (normally, the bank only gives you one month of history for
free). Once you get that CSV file, you can convert it to JSON using this script, and import it in Cozy. Thus, you get
your full history.

### `gen_ach_token`

For reasons unknown to me, the `ach token` subcommand only gives you the raw token, but `ach` expects a token file with
a very specific format for the other subcommands (`import`, `export`, ...). In fact, it expects the following:

```js
module.exports = {token: "..."};
```

This script calls `ach token` and generates a file in the correct format, that you can then use
with `ach`: `ach -t token.js ...`.

### `manual_insert`

This script allows batch manual insertion of transaction in a Cozy Banks account. This is useful if, like me, you're
trying to get old operations in your history from paper trails or things like that.

TODO: document this better

### `plot_balance`

This plots the balance of your accounts over time using Plotly.

### `sankey`

This script generates a Sankey diagram of your transactions. They're grouped by their Cozy category.

The output is in your clipboard, by default. The format is the one used
by [Sankeymatic](https://sankeymatic.com/build/).

## License

This project is licensed under the terms of the [MIT license](LICENSE).