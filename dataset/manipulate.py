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
        updated_image_path = "./" + issue['image_path'] 
        concatenate = f"{issue['issue_id'] } *** {updated_image_path}  *** {issue['description']}" 
        issue['concatenate'] = concatenate
        issue['image_path'] = updated_image_path
        updated_issues.append(issue)

    with open(file_path, 'w') as file:
        json.dump(updated_issues, file, indent=4)

# Update the products.json file
file_path = '/Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/dataset/defects.json'
update_products_json(file_path)


# # Define the directory containing the images
# directory = './static/images/defects_images/'

# # Loop through the files in the directory
# for i, filename in enumerate(sorted(os.listdir(directory))):
#     # Construct the old and new file paths
#     old_file = os.path.join(directory, filename)
#     new_file = os.path.join(directory, f"{i}.png")
    
#     # Rename the file
#     os.rename(old_file, new_file)
#     print(f"Renamed {old_file} to {new_file}")