from agentc import tool
from pydantic import BaseModel, Field

class ProductID(BaseModel):
    """the identifier of the product"""
    product_id: str = Field(..., title="Product ID", description="The product ID to get the sentiment for") 


@tool
def get_customer_sentiment1(product_id: ProductID) -> float:
   """get customer sentiment for a product"""
   productid = product_id.product_id
   return productid