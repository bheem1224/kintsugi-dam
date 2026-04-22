import os
from app.core.security import validate_plugin_ast, SecurityViolationError

# Create a malicious plugin
plugin_code = """
import os as o
import sys
import builtins
import importlib

# Attempt 1: Alias
try:
    o.remove("dummy.txt")
except:
    pass

# Attempt 2: getattr
try:
    f = getattr(o, "rem" + "ove")
    f("dummy.txt")
except:
    pass

# Attempt 3: importlib
try:
    sh = importlib.import_module("shutil")
    getattr(sh, "rmtree")("dummy_dir")
except:
    pass

# Attempt 4: __import__
try:
    __import__("os").system("echo hacked")
except:
    pass

# Attempt 5: exec
try:
    exec("import os; os.unlink('dummy.txt')")
except:
    pass
"""

with open("malicious_plugin_test.py", "w") as f:
    f.write(plugin_code)

try:
    validate_plugin_ast("malicious_plugin_test.py")
    print("VULNERABLE: Malicious plugin passed AST validation!")
except SecurityViolationError as e:
    print(f"SECURE: Caught by AST validation - {e}")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    if os.path.exists("malicious_plugin_test.py"):
        os.remove("malicious_plugin_test.py")
