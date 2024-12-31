from agentc import tool
from pydantic import BaseModel, Field
import requests


class SkuId(BaseModel):
    """The identifier of the SKU"""
    sku_id: str = Field(description="SKU identifier") 


@tool(annotations={"engineer": "true"})
def get_sku_cad(sku: str) -> dict:
    """For general support agents - fetch CAD file in PLM system for a given SKU"""
    
    # Define the URL for the REST API endpoint
    url = f"http://localhost:5001/product/ca-001"
    
    
    try:
        # Make the HTTP GET request to fetch the CAD file
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the JSON response
        cad_data = response.json()
        
        return cad_data
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

