import sys
import os

if len(sys.argv) < 3:
    print("Missing arguments. Usage: {1} <aws_ids> <terr_ids>".format(sys.argv[0]))
    exit(1)

aws_ids = sys.argv[1].split('|')
terr_ids = sys.argv[2].split('|')

if len(aws_ids) != len(terr_ids):
    print('Input tables count mismatch')
    exit(1)

for aws_id, terr_id in zip(aws_ids, terr_ids):
    res = os.system('terraform import {1} {2}'.format(terr_id, aws_id))
    if res > 0:
        print('Import failed for {1} {2}'.format(terr_id, aws_id))
        exit(1)

print('Import complete')
