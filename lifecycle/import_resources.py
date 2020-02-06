import sys
import os

if len(sys.argv) < 3:
    s = "Missing arguments. Usage: {0} <aws_ids> <terr_ids>"
    print(s.format(os.path.basename(sys.argv[0])))
    exit(1)

aws_ids = sys.argv[1].split('|')
terr_ids = sys.argv[2].split('|')

if len(aws_ids) != len(terr_ids):
    print('Input tables count mismatch')
    exit(1)

varfile = '-var-file="../config.ini" ' if os.path.isfile('../config.ini') else '' 

for aws_id, terr_id in zip(aws_ids, terr_ids):
    if not aws_id or not terr_id: continue
    res = os.system('terraform import {2}{0} {1}'.format(terr_id, aws_id, varfile))
    if res > 0:
        print('Import failed for {0} {1}'.format(terr_id, aws_id))
        exit(1)

print('Import complete')
