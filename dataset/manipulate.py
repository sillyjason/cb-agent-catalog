import sys
import os

# Add the root directory to the PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


import json

def update_products_json(file_path):
    with open(file_path, 'r') as file:
        issues = json.load(file)

    updated_issues = []
    for index, issue in enumerate(issues):
        # Remove the manufacturer and product_id fields
        updated_image_path = issue['image_path'] + ".png"
        concatenate = f"{issue['issue_id'] } *** {updated_image_path}  *** {issue['description']}" 
        issue['concatenate'] = concatenate
        issue['image_path'] = updated_image_path
        updated_issues.append(issue)

    with open(file_path, 'w') as file:
        json.dump(updated_issues, file, indent=4)

# Update the products.json file
file_path = '/Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/dataset/defects.json'
update_products_json(file_path)