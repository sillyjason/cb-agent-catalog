from agentc import tool
from pydantic import BaseModel
import requests


class Sku(BaseModel):
    sku_id: str


@tool
def get_sku_cad(sku_obj: Sku) -> dict:
    """For general support agents - fetch CAD file in PLM system for a given SKU"""
    
    # sku_value = sku.sku  # Extract SKU from the model
    
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

