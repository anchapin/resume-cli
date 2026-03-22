import time
import re
from cli.utils.keyword_density import KeywordDensityGenerator

class MockYAMLHandler:
    def get_summary(self, variant): return "Senior Software Engineer with 10 years of experience in Python, Javascript, and React. Passionate about AI and Machine Learning."
    def get_skills(self, variant): return ["Python", "JavaScript", "TypeScript", "React", "Node.js", "Docker", "AWS", "SQL", "Machine Learning"]
    def get_experience(self, variant): return [{"role": "Software Engineer", "company": "Tech Corp", "description": "Built scalable APIs with Python and FastAPI. Deployed on AWS using Docker and Kubernetes. Improved database performance with SQL indexing."}]
    def get_education(self, variant): return []
    def get_projects(self, variant): return []

class MockConfig:
    ai_provider = "none"

generator = KeywordDensityGenerator()
generator.yaml_handler = MockYAMLHandler()
generator.config = MockConfig()

job_desc = """
Job Title: Senior Backend Engineer
Company: Acme Corp

Requirements:
- Strong experience with Python and Django or FastAPI
- Proficiency in JavaScript and React
- Experience with Docker and Kubernetes for containerization
- Familiarity with AWS cloud services
- Understanding of SQL and database optimization
- Knowledge of Machine Learning is a plus
"""

start_time = time.time()
for _ in range(100):
    generator.generate_report(job_desc)
end_time = time.time()

print(f"Time taken for 100 reports: {end_time - start_time:.4f}s")
