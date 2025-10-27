import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Backend.app import create_app
app = create_app()
for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    print(r.rule, sorted(list(r.methods)))
