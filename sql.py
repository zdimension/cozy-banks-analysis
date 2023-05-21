# coding: utf-8

import pandas as pd
from pandasql import sqldf, PandaSQL, PandaSQLException

from banks.client import get_operations, get_accounts, parser, parse_args

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.sql import SqlLexer

pysqldf = lambda q: sqldf(q, globals())

parser.add_argument("query", help="Query to search for", nargs="?")
args = parse_args()

accs = get_accounts()
ops = get_operations()

accounts = pd.DataFrame(accs)
accounts.drop([
    "cozyMetadata",
    "metadata",
    "relationships"
], axis=1, inplace=True)
accounts["display"] = accounts["__displayLabel"]

operations = pd.DataFrame(ops)
operations.drop([
    "bills",
    "cozyMetadata",
    "currency",
    "metadata",
    "reimbursements",
    "relationships",
], axis=1, inplace=True)
operations["category"] = operations["__categoryId"]

if not args.query:
    tables = [accounts, operations]
    columns = [*{col for table in tables for col in table.columns}]
    sql = PandaSQL()
    sql_completer = WordCompleter(
        [
            'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
            'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
            'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
            'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
            'current_time', 'current_timestamp', 'database', 'default',
            'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
            'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
            'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
            'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
            'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
            'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
            'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
            'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
            'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
            'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
            'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
            'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
            'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
            'without'] + ["accounts", "operations"] + columns, ignore_case=True)
    history = InMemoryHistory()
    session = PromptSession(lexer=PygmentsLexer(SqlLexer), completer=sql_completer, history=history)
    query = []
    print("^D to exit")
    while True:
        try:
            query.append(session.prompt("...  " if query else "SQL> "))
            result = sql("\n".join(query))
            print(result.to_string())
        except PandaSQLException as o:
            if "incomplete input" in o.args[0].args[0]:
                continue
            else:
                print(o)
                query.clear()
        except KeyboardInterrupt:
            query.clear()
        except EOFError:
            break
        else:
            del history._loaded_strings[-len(query):]
            history.append_string(" ".join(query))
            query.clear()
else:
    result = pysqldf(args.query).head()

    print(result.to_string())
