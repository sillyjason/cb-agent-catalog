import os
import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json 
import re
from couchbaseops import run_query
from sharedfunctions.print import print_success, print_error

load_dotenv()

#get the environment variables
CB_CONN_STRING = os.getenv("CB_CONN_STRING")
EVENTING_HOSTNAME = os.getenv("EVENTING_HOSTNAME")
SEARCH_HOSTNAME = os.getenv("SEARCH_HOSTNAME")
CB_USERNAME = os.getenv("CB_USERNAME")
CB_PASSWORD = os.getenv("CB_PASSWORD")
APP_NODE_HOSTNAME= os.getenv("APP_NODE_HOSTNAME")

print("start setting up data structures..")


def create_bucket(bucket_name, ram_quota): 
    url = f"http://{CB_CONN_STRING}:8091/pools/default/buckets"
    
    body = {
        'name': bucket_name,
        'ramQuota': ram_quota,
        'bucketType': 'couchbase',
        'flushEnabled': 1
    }
    
    response = requests.post(url, auth=HTTPBasicAuth(os.getenv("CB_USERNAME"), os.getenv("CB_PASSWORD")), data=body)

    success_code = 202
    if response.status_code == success_code:
        print_success(f"Created bucket '{bucket_name}'")
        return True
    
    else:
        print_error(f"Error creating bucket {bucket_name}: {response.text}")
        return None

def create_scope(scope_name, bucket_name):
    url = f"http://{CB_CONN_STRING}:8091/pools/default/buckets/{bucket_name}/scopes"
    response = requests.post(url, auth=HTTPBasicAuth(os.getenv("CB_USERNAME"), os.getenv("CB_PASSWORD")), data={"name": scope_name})
    success_code = 200
    if response.status_code == success_code:
        print_success(f"Created scope '{bucket_name}.{scope_name}'")
        return True
    else:
        print_error(f"Error creating scope {scope_name}: {response.text}")
        return False

def create_collection(bucket_name, scope_name, collection_name):
    url = f"http://{CB_CONN_STRING}:8091/pools/default/buckets/{bucket_name}/scopes/{scope_name}/collections"
    response = requests.post(url, auth=HTTPBasicAuth(os.getenv("CB_USERNAME"), os.getenv("CB_PASSWORD")), data={"name": collection_name})
 
    success_code = 200
    if response.status_code == success_code:
        print_success(f"Created collection '{bucket_name}.{scope_name}.{collection_name}'")
        return True
    else:
        print_error(f"Error creating colletion {collection_name}: {response.text}")
        return False


#create bucket main 
BUCKET_MAIN_ID = create_bucket("main", 1500)

#create bucket meta & audits
create_bucket("meta", 400)
create_bucket("audits", 500)


if BUCKET_MAIN_ID is not None:
    scope_data_created = create_scope("data", "main") 
    
    if scope_data_created:
        create_collection("main", "data", "messages")
        create_collection("main", "data", "message_responses")
        create_collection("main", "data", "products")
        create_collection("main", "data", "tickets")
        create_collection("main", "data", "product_faqs")
        create_collection("main", "data", "defects")
    
print_success("Done setting up data structures..")



#updating the endpoint in templates/index.html 
index_file = "./templates/index.html"

try:
    with open(index_file, 'r') as file:
        content = file.read()
        updated_content = content.replace("http://localhost:5001", f"http://{APP_NODE_HOSTNAME}:5001")
    
    with open(index_file, 'w') as file:
        file.write(updated_content)
    
    print_success("Endpoint updated successfully in index.html")
    
except Exception as e:
    print_error(f"Error updating endpoint in index.html: {str(e)}")


# setup Eventing functions 
def import_function(function_name):
     
    print(f"Importing function {function_name}...")
    
    try:
        url = f"http://{EVENTING_HOSTNAME}:8096/api/v1/functions/{function_name}"

        with open(f'./static/eventing/{function_name}.json', 'r') as file:
            data = json.load(file)
            data_str = json.dumps(data)
            data_str = re.sub("YOUR_IP_ADDRESS", APP_NODE_HOSTNAME, data_str)
            data = json.loads(data_str)
                    
        response = requests.post(url, json=data, auth=(CB_USERNAME, CB_PASSWORD))
        response.raise_for_status()

        print_success(f"Function {function_name} imported successfully")
    
    except Exception as e:
        print_error(f"Error importing function {function_name}: {str(e)}")


# setup fts index
def import_fts_index(index_name):
    print(f"Importing fts index...")
    
    try:
        url = f"http://{SEARCH_HOSTNAME}:8094/api/bucket/main/scope/data/index/defect_fts"
        with open(f'./static/fts/{index_name}.json', 'r') as file:
            data = json.load(file)
            requests.put(url, auth=(CB_USERNAME, CB_PASSWORD), json=data)
            print_success(f'fts index {index_name} imported successfully') 

    except Exception as e:
        print_error(f"Error importing fts index: {str(e)}")

import_fts_index("defects_fts")



# create indexes 
run_query("CREATE INDEX `ticket_product_id` on `main`.`data`.`tickets`(`related_product`)")
run_query("CREATE INDEX `product_sku` on `main`.`data`.`products`(`sku`)")

print_success("setup complete.")