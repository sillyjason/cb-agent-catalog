from couchbase.vector_search import VectorQuery, VectorSearch
import couchbase.search as search
from couchbase.options import SearchOptions
from dotenv import load_dotenv
import uuid
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator
import os 
import couchbase.subdocument as SD
from pydantic import BaseModel, Field
import datetime
from agentc import tool


load_dotenv()

# Couchbase connection
auth = PasswordAuthenticator(os.getenv("CB_USERNAME"), os.getenv("CB_PASSWORD"))
cluster = Cluster(f'couchbase://{os.getenv("CB_CONN_STRING")}', ClusterOptions(auth))
cluster.wait_until_ready(datetime.timedelta(seconds=5))
print("Couchbase setup complete")


# insert doc 
def insert_doc(bucket, scope, collection, doc, doc_id=None): 
    
    cb_collection = cluster.bucket(bucket).scope(scope).collection(collection)
        
    try:
        docid = doc_id if doc_id else str(generate_uuid())
        
        cb_collection.insert(
            docid,
            doc
        )
        
        print(f"Insert {collection} successful: {docid}")
        
        return docid
        
    except Exception as e:
        print("exception:", e)
        
        return None 


# generate uuid
def generate_uuid(): 
    return uuid.uuid4()


# subdocument insert
def subdocument_insert(bucket, scope, collection, doc_id, path, value):
    cb_collection = cluster.bucket(bucket).scope(scope).collection(collection)
    
    try:
        cb_collection.mutate_in(doc_id, [SD.insert(path, value)])
        
        print(f"Subdocument insert successful for {doc_id}, collection {collection}, path {path} and value {value}")
        
    except Exception as e:
        print("exception with subdoc insert:", e)
        
        return None


class RefundIncident(BaseModel):
    """The refund incident created to address customer's refund request"""
    order_id: str = Field(description="the ID of the sales order associated with the refund request")
    message_id: str = Field(description="the ID of the customer message associated with the refund request")
    refund_reason: str = Field(description="the reason for the refund")
    customer_message: str = Field(description="the message sent by the customer")
    
 

@tool
def create_refund_ticket(refund_obj: RefundIncident) -> dict:
    """create a refund ticket in the database to process customer's valid refund request"""
    
    order_id = refund_obj.order_id
    message_id = refund_obj.message_id
    refund_reason = refund_obj.refund_reason
    customer_message = refund_obj.customer_message

    # insert the refund ticket to the database    
    try:
        ticket_id = f"refund_{order_id}"
        
        ticket_data = {
            "order_id": order_id,
            "approved": False,
            "refund_amount": 0,
            "refund_reason": refund_reason,
            "message_id": message_id,
            "customer_message": customer_message,
            "time": datetime.datetime.now().isoformat()
        }
        
        insert_doc("main", "data", "refund_tickets", ticket_data, ticket_id)
        
        subdocument_insert("main", "data", "orders", order_id, "refund_ticket_id", ticket_id)
        subdocument_insert("main", "data", "messages", message_id, "refund_ticket_id", ticket_id)
        
        
    except Exception as e:
        print("exception:", e)
        
    return {
            "refund_ticket_id": ticket_id,
            "refund_ticket_creation_success": True  
        }