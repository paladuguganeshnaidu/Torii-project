import sys, traceback, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
try:
    import Backend.api as api
    print('imported Backend.api OK')
    print('has blueprint:', hasattr(api,'api_bp'))
except Exception:
    traceback.print_exc()
