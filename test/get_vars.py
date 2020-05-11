def get_vars():
    vars = {}
    with open('config.tfvars','r') as f:
        for line in f:
            if '=' not in line:
                continue
            key, val = line.split('=')
            key = key.strip()
            val = val.strip()
            if val[0] == '"' and val[-1] == '"':
                vars[key] = val[1:-1]
    vars['bucket_name'] = "{}.{}-quotes".format(vars['aws_user'], vars['id'].replace('_','-'))
    return vars