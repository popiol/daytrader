import os
import sys

if len(sys.argv) < 2:
    print("Missing argument. Usage " + os.path.basename(argv[0]) + " <function_name>")
    exit(1)

params = {'app_id':''}
fname = "../../config.ini"
if os.path.isfile(fname):
    with open(fname) as f:
        for line in f:
            key, val = line.partition("=")[::2]
            params[key.strip()] = val.strip().strip('"')

app_id = params['app_id']
fun_name = sys.argv[1]
full_name = app_id + '_' + fun_name

import get_quotes.main as fun

class Struct:
    def __init__(self, entries):
        self.__dict__.update(entries)

context = Struct({'function_name':full_name})

res = fun.lambda_handler({},context)

print(res)

