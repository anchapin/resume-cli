import time
from pathlib import Path
from cli.integrations.job_parser import JobParser

parser = JobParser()
content = "This is a sample description with a salary of $100k - $150k for a senior full-time role. We are looking for people with requirements:\n- Python\n- React\n Responsibilities:\n- Code" * 100

start = time.time()
for _ in range(100):
    parser._parse_generic(content)
print("Time:", time.time() - start)
