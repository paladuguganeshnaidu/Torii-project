import importlib,traceback,sys,os
# Ensure project root is on sys.path so 'Backend' package can be imported when running this script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    m=importlib.import_module('Backend.tools.web_vuln_scanner')
    print('module ok')
    print([n for n in dir(m) if not n.startswith('_')])
except Exception:
    traceback.print_exc()
