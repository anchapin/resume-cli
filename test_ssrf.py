import os
import sys

# Make sure we can import from the cli package
sys.path.insert(0, os.path.abspath('.'))

from cli.integrations.job_parser import JobParser

parser = JobParser()
try:
    print("Testing JobParser SSRF with metadata endpoint...")
    parser.parse_from_url("http://169.254.169.254/latest/meta-data/")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
