import sys
import os

# Add the root directory to the PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import json
from agentic.embedding import create_embeddings

def update_products_json(file_path):
    with open(file_path, 'r') as file:
        issues = json.load(file)

    updated_issues = []
    for index, issue in enumerate(issues):
        # Remove the manufacturer and product_id fields
        concatenate = f"{issue['issue_id'] } *** {issue['image_path']}  *** {issue['description']}" 
        issue['concatenate'] = concatenate
        updated_issues.append(issue)

    with open(file_path, 'w') as file:
        json.dump(updated_issues, file, indent=4)

# Update the products.json file
file_path = '/Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/dataset/defects.json'
update_products_json(file_path)