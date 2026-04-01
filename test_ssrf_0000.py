import os
import sys

# Make sure we can import from the cli package
sys.path.insert(0, os.path.abspath('.'))

from cli.integrations.job_parser import JobParser

parser = JobParser()
try:
    print("Testing JobParser SSRF with 0.0.0.0...")
    parser.parse_from_url("http://0.0.0.0:8000/")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
