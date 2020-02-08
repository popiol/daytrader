import glob
import re
import os

no_tag_resources = [
    'aws_iam_role_policy',
    'aws_iam_role_policy_attachment',
    'aws_cloudwatch_event_target'
]

for fname in glob.glob('*tf'):
    foutname = fname + '.new';
    with open(fname,'r') as f, open(foutname,'w') as fout:
        empty = False
        depth = 0
        depth2 = 0
        state = 0
        state_depth = 0
        state_depth2 = 0
        for line in f:
            outline = line
            depth_prev = depth
            depth2_prev = depth2
            depth = max(0, depth + line.count('{') - line.count('}'))
            depth2 = max(0, depth2 + line.count('(') - line.count(')'))
            if state == 0 and line.startswith('resource '):
                line = re.sub(r"\s+"," ",line).replace('"','')
                if line.split(' ')[1] not in no_tag_resources:
                    state = 1
                    terr_id = ".".join(line.split(' ')[1:3])
            elif state > 0 and depth == 0:
                state = 0
                outline = "{0}tags = {{\n{0}{1}App = var.app\n{0}{1}AppVer = var.app_ver\n{0}{1}AppStage = var.app_stage\n{0}{1}TerraformID = \"{2}\"\n{0}}}\n}}\n"
                outline = outline.format('  ','  ',terr_id)
                if not empty:
                    outline = "\n" + outline
            elif state > 0 and re.sub(r"\s","",line).startswith('tags='):
                outline = ''
                if depth > depth_prev or depth2 > depth2_prev:
                    state = 2
                    state_depth = depth_prev
                    state_depth2 = depth2_prev
            elif state == 2:
                outline = ''
                if state_depth == depth and state_depth2 == depth2:
                    state = 1

            if outline != '':
                if outline.strip() == '':
                    if empty:
                        outline = ''
                    empty = True
                else:
                    empty = False
                
                fout.write(outline)

        os.rename(foutname, fname)
