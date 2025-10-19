#!/usr/bin/env python3
"""
Script to remove legacy (non-adaptive) endpoints from main.py
Keeps only /adaptive/* endpoints plus / and /health
"""

import re

# Read the original file
with open('main.py', 'r') as f:
    content = f.read()

# List of legacy endpoint patterns to remove (function name patterns)
legacy_endpoints = [
    r'@app\.get\("/quiz".*?\n(?:@.*?\n)*async def get_quiz_endpoint.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/quiz/submit".*?\n(?:@.*?\n)*async def submit_quiz.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/feedback".*?\n(?:@.*?\n)*async def submit_feedback.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.get\("/content".*?\n(?:@.*?\n)*async def get_content.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.get\("/progress".*?\n(?:@.*?\n)*async def get_progress.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/courses/enroll".*?\n(?:@.*?\n)*async def enroll_in_course.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/courses/access".*?\n(?:@.*?\n)*async def access_course_content.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.get\("/courses/enrollments".*?\n(?:@.*?\n)*async def get_user_enrollments.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/courses/module-progress".*?\n(?:@.*?\n)*async def update_module_progress.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.get\("/courses/\{course_id\}/progress".*?\n(?:@.*?\n)*async def get_course_progress.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.get\("/courses/summary".*?\n(?:@.*?\n)*async def get_courses_summary.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/validate-mermaid".*?\n(?:@.*?\n)*async def validate_mermaid_endpoint.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
    r'@app\.post\("/mermaid-interaction".*?\n(?:@.*?\n)*async def mermaid_interaction_endpoint.*?\n(?:.*?\n)*?(?=\n@app\.|$)',
]

# Remove each legacy endpoint
modified_content = content
for pattern in legacy_endpoints:
    modified_content = re.sub(pattern, '', modified_content, flags=re.DOTALL | re.MULTILINE)

# Clean up multiple blank lines
modified_content = re.sub(r'\n\n\n+', '\n\n', modified_content)

# Write the cleaned file
with open('main.py', 'w') as f:
    f.write(modified_content)

print("✅ Removed 13 legacy endpoints from main.py")
print("✅ Keeping only /adaptive/* endpoints plus / and /health")
