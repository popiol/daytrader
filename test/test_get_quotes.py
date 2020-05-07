import boto3
import unittest
import re
import importlib
import os
import sys

class TestGetQuotes(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.vars = {}
        with open('config.tfvars','r') as f:
            for line in f:
                if '=' not in line:
                    continue
                key, val = line.split('=')
                key = key.strip()
                val = val.strip()
                if val[0] == '"' and val[-1] == '"':
                    self.vars[key] = val[1:-1]
        self.bucket_name = "{}.{}-quotes".format(self.vars['aws_user'], self.vars['id'].replace('_','-'))


    def test_local(self):
        sys.path.insert(0, os.getcwd())
        get_quotes = importlib.import_module("lambda.get_quotes.main")
        res = get_quotes.lambda_handler({"bucket_name": self.bucket_name}, {})
        assert(res['statusCode'] == 200)
        assert(res['body']['bucket_name'] == self.bucket_name)
        assert(len(res['body']['files']) > 0)
        files = res['body']['files']
        s3 = boto3.resource('s3')
        for key in files:
            print("file =", key)
            obj = s3.Object(self.bucket_name, key)
            html = obj.get()['Body'].read().decode('utf-8')
            assert(re.match("<table.+<th.+Name.*</th>", html, re.MULTILINE))
            assert(re.match("<table.+<th.+Latest Price.*</th>", html, re.MULTILINE))
            assert(re.match("<table.+<th.+Low.*</th>", html, re.MULTILINE))
            assert(re.match("<table.+<th.+High.*</th>", html, re.MULTILINE))
            assert(re.match("<table.+<th.+Time.*</th>", html, re.MULTILINE))
            assert(re.match("<table.+<th.+Date.*</th>", html, re.MULTILINE))


if __name__ == '__main__':
    unittest.main()