"""End-to-end test for security_ast_refactor.py - all 20 transformers"""
import sys
sys.path.insert(0, '.')
from security_ast_refactor import run_security_refactoring

TESTS = {
    "1-eval": {
        "code": 'expr = "2+3"\nresult = eval(expr)\nprint(result)\nx = 1\ny = 2\n',
        "expect_in": "ast.literal_eval"
    },
    "2-exec": {
        "code": 'cmd = "print(1)"\nexec(cmd)\nprint("done")\nx = 1\ny = 2\n',
        "expect_in": "allowed.get"
    },
    "3-os_system": {
        "code": 'import os\nfile = "test.txt"\nos.system("ls " + file)\nprint("ok")\nx = 1\n',
        "expect_in": "subprocess.run"
    },
    "4-shell_true": {
        "code": 'import subprocess\nsubprocess.run("ls -la", shell=True)\nprint("ok")\nx = 1\ny = 2\n',
        "expect_in": "['ls', '-la']"
    },
    "5-path_traversal": {
        "code": 'name = input("file:")\nf = open(name)\nprint(f.read())\nx = 1\ny = 2\n',
        "expect_in": "os.path.join"
    },
    "6-unsafe_delete": {
        "code": 'import os\nfile = input("del:")\nos.remove(file)\nprint("ok")\nx = 1\n',
        "expect_in": "os.path.join"
    },
    "7-pickle": {
        "code": 'import pickle\nf = open("data.pkl", "rb")\ndata = pickle.load(f)\nprint(data)\nx = 1\n',
        "expect_in": "json.load"
    },
    "8-yaml": {
        "code": 'import yaml\nf = open("c.yaml")\ndata = yaml.load(f, Loader=yaml.Loader)\nprint(data)\nx = 1\n',
        "expect_in": "yaml.safe_load"
    },
    "9-hardcoded_pw": {
        "code": 'password = "admin123"\nuser = "test"\nprint(user)\nx = 1\ny = 2\n',
        "expect_in": "os.getenv"
    },
    "10-sql_injection": {
        "code": 'name = "test"\nquery = "SELECT * FROM users WHERE name=\'"+name+"\'"\nprint(query)\nx = 1\ny = 2\n',
        "expect_in": "?"
    },
    "11-rmtree": {
        "code": 'import shutil\nfolder = input("f:")\nshutil.rmtree(folder)\nprint("ok")\nx = 1\n',
        "expect_in": "os.path.join"
    },
    "12-weak_random": {
        "code": 'import random\ntoken = random.randint(1000, 9999)\nprint(token)\nx = 1\ny = 2\n',
        "expect_in": "secrets.randbelow"
    },
    "13-sensitive_log": {
        "code": 'pwd = input("pw:")\nprint("Password:", pwd)\nprint("ok")\nx = 1\ny = 2\n',
        "expect_in": "received"
    },
    "14-unsafe_input": {
        "code": 'age = int(input("Age:"))\nprint(age)\nx = 1\ny = 2\nz = 3\n',
        "expect_in": "isdigit"
    },
    "15-upload": {
        "code": 'name = input("f:")\nf = open(name, "w")\nf.write("data")\nprint("ok")\nx = 1\n',
        "expect_in": "os.path.join"
    },
    "16-weak_hash": {
        "code": 'import hashlib\nh = hashlib.md5(b"test")\nprint(h.hexdigest())\nx = 1\ny = 2\n',
        "expect_in": "hashlib.sha256"
    },
    "17-mktemp": {
        "code": 'import tempfile\ntmp = tempfile.mktemp()\nprint(tmp)\nx = 1\ny = 2\n',
        "expect_in": "mkstemp"
    },
    "18-assert_security": {
        "code": 'class U:\n    is_admin = True\nu = U()\nassert u.is_admin, "Not authorized"\nprint("ok")\n',
        "expect_in": "PermissionError"
    },
    "19-ftp": {
        "code": 'import ftplib\nftp = ftplib.FTP("server.com")\nprint(ftp)\nx = 1\ny = 2\n',
        "expect_in": "FTP_TLS"
    },
}

passed = 0
failed = 0
for name, tc in TESTS.items():
    result = run_security_refactoring(tc["code"])
    code_out = result["refactored_code"]
    ok = tc["expect_in"] in code_out
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"[{status}] {name}: expected '{tc['expect_in']}' in output")
        print(f"  OUTPUT: {code_out[:120]}")
    if ok:
        print(f"[{status}] {name} (issues={result['total_issues']}, fixes={result['total_fixes']})")

print(f"\n{'='*60}")
print(f"RESULT: {passed}/{passed+failed} security transformers PASS")
if failed:
    print(f"FAILED: {failed}")
print(f"{'='*60}")
