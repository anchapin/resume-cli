with open('cli/integrations/job_parser.py', 'r') as f:
    content = f.read()

content = content.replace("from typing import Any, Dict, List, Optional, Tuple, Union, Union", "from typing import Any, Dict, List, Optional, Tuple, Union")

# We can fix this by removing the second set of duplicate patterns that black formatted.
# Find the string "_SALARY_PATTERNS = ["

parts = content.split("_SALARY_PATTERNS = [")
if len(parts) == 3:
    # Reassemble up to the start of the second _SALARY_PATTERNS
    new_content = parts[0] + "_SALARY_PATTERNS = [" + parts[1]

    # We still have the rest of the second duplicated block to remove.
    # Let's find "class JobParser:" and just append that.
    class_parts = parts[2].split("class JobParser:")
    if len(class_parts) == 2:
        new_content += "class JobParser:" + class_parts[1]
        with open('cli/integrations/job_parser.py', 'w') as f:
            f.write(new_content)
        print("Fixed duplicates")
