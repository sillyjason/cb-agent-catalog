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
        embedding = create_embeddings(issue['description'])
        issue_id = f"issue_{index}"
        issue['issue_id'] = issue_id
        issue['description_embedding'] = embedding
        issue['image_path'] = f"dataset/defect_images/{index}"

        updated_issues.append(issue)

    with open(file_path, 'w') as file:
        json.dump(updated_issues, file, indent=4)

# Update the products.json file
file_path = '/Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/dataset/defects.json'
update_products_json(file_path)