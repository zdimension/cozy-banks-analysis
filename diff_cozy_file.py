import datetime
import json
from banks.client import get_operations, parse_args, parser
import dateutil.parser
import dateutil.relativedelta


def matches(old_op, new_op):
    if old_op["amount"] != new_op["amount"]:
        return False

    # compare date delta
    date1 = old_op["date"]
    date2 = new_op["date"]

    delta = dateutil.relativedelta.relativedelta(date1, date2)
    if delta.days > 5:  # we allow up to 5 days. This is unfortunately necessary because of the way some banks work
        return False

    return True


def str_op(op):
    date = op["date"].strftime("%d/%m/%Y")
    return f"{op['label']} ({op['amount']}) - {date}"


def diff(old_ops, new_ops):
    # we need to sort the operations by amount first, because it is the only trustworthy information
    # then we sort by secondary criteria (date, label) to make sure we have a deterministic order

    sort_pred = lambda x: (x["amount"], x["date"], x["originalBankLabel"])
    old_ops = sorted(old_ops, key=sort_pred)
    new_ops = sorted(new_ops, key=sort_pred)

    missing_from_cozy = []
    missing_from_file = []

    new_idx = 0
    old_idx = 0
    while new_idx < len(new_ops) and old_idx < len(old_ops):
        old_op = old_ops[old_idx]
        new_op = new_ops[new_idx]

        if matches(old_op, new_op):
            old_idx += 1
            new_idx += 1

        elif old_op["amount"] < new_op["amount"]:
            missing_from_file.append(old_op)
            print(f"Cozy operation not in file: {str_op(old_op)}")
            old_idx += 1

        else:
            missing_from_cozy.append(new_op)
            print(f"File operation not in Cozy: {str_op(new_op)}")
            new_idx += 1

    return missing_from_cozy, missing_from_file


def prepare_operations(operations, cutoff=None):
    for op in operations:
        op["date"] = dateutil.parser.parse(op["date"]).replace(tzinfo=None)
        if "amount" in op:
            op["amount"] = float(op["amount"])
        else:
            op["amount"] = 0

    if cutoff is not None:
        cutoff = dateutil.parser.parse(cutoff).replace(tzinfo=None)
        operations = [op for op in operations if op["date"] >= cutoff]

    return operations


def save_operations(operations, filename):
    for op in operations:
        op["date"] = op["date"].isoformat()

    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"io.cozy.bank.operations": operations}, f, indent=4)


def main():
    parser.add_argument(
        "json_file", help="Cozy data in which to remove duplicate operations")

    parser.add_argument("account", help="Cozy Account to use")

    parser.add_argument("--cutoff", help="Cutoff date")

    args = parse_args()

    old_ops = [op for op in get_operations() if op["account"] == args.account]

    new_ops = json.load(open(args.json_file, "r",
                             encoding="utf-8"))["io.cozy.bank.operations"]

    old_ops = prepare_operations(old_ops, args.cutoff)
    new_ops = prepare_operations(new_ops, args.cutoff)

    missing_from_cozy, missing_from_file = diff(old_ops, new_ops)

    print(f"Missing from Cozy: {len(missing_from_cozy)}")
    print(f"Missing from file: {len(missing_from_file)}")

    if len(missing_from_cozy) > 0:
        print(
            f"Most recent missing operation from cozy: {str_op(max(missing_from_cozy, key=lambda x: x['date']))}"
        )

        save_operations(missing_from_cozy,
                        args.json_file + ".missing_from_cozy.json")

    if len(missing_from_file) > 0:
        print(
            f"Most recent missing operation from file: {str_op(max(missing_from_file, key=lambda x: x['date']))}"
        )

        save_operations(missing_from_file,
                        args.json_file + ".missing_from_file.json")

    print("Saved results to files")


if __name__ == "__main__":
    main()
