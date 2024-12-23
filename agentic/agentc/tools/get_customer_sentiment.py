from agentc import tool
from pydantic import BaseModel, Field


@tool
def get_customer_sentiment(customer_message: str) -> float:
    """get the customer sentiment as a float that counts. It increments when certain positive words are hit, and decrements when certain negative words are hit"""
    
    POSITIVES = ["good", "great", "awesome", "excellent", "couchbase"]
    NEGATIVES = ["bad", "terrible", "horrible", "awful", "mongodb", "mongo"]

    sentiment = 0
    
    # transform words to lower capital letters
    customer_message = customer_message.lower()
    
    for word in customer_message.split():
        if word in POSITIVES:
            sentiment += 1
        elif word in NEGATIVES:
            sentiment -= 1    
    
    return sentiment
