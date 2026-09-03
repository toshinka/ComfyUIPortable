# Backward compatibility wrapper
import sys
import os
from test_region_editor_backend_api import test_api_execution

if __name__ == "__main__":
    print("[NOTE] test_workflow_07.py has been renamed to test_region_editor_backend_api.py.")
    sys.exit(test_api_execution())
