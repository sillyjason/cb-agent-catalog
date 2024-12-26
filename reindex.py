from couchbaseops import insert_doc, flush_collection
import json
from sharedfunctions.print import print_success


### flush all existing collections ###
flush_collection("main", "data", "defects")
flush_collection("main", "data", "message_responses")
flush_collection("main", "data", "messages")
flush_collection("main", "data", "product_faqs")
flush_collection("main", "data", "products")
flush_collection("main", "data", "tickets")



### re-upload products data ###
with open("dataset/products.json") as f:
    data = json.load(f)
    
    for product in data:
        insert_doc("main", "data", "products", product, product["sku"])
    
    print("Inserted all docs for products")
    

### re-upload defects data ###
with open("dataset/defects.json") as f:
    data = json.load(f)
    
    for defect in data:
        insert_doc("main", "data", "defects", defect, defect["issue_id"])
    
    print("Inserted all docs for defects")


### re-upload tickets data ###
with open("dataset/tickets.json") as f:
    data = json.load(f)
    
    for ticket in data:
        insert_doc("main", "data", "tickets", ticket, ticket["ticket_id"])
    
    print("Inserted all docs for tickets")


print_success("Inserted all docs")


