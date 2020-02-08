import os
import sys

if len(sys.argv) < 2:
    print("Missing argument. Usage " + os.path.basename(argv[0]) + " <function_name>")
    exit(1)

fun_name = sys.argv[1]

import get_quotes.main as fun

class Struct:
    def __init__(self, entries):
        self.__dict__.update(entries)

context = Struct({'function_name':fun_name})

fun.lambda_handler({},context)

