import json
from collections import defaultdict
from agentc import tool
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv
import os 

# load the environment variables
load_dotenv()

def analyze_tool_calls(data):
    tool_stats = defaultdict(lambda: {'invoked': 0, 'success': 0, 'failure': 0})

    for entry in data:
        for tool_call in entry['tool_calls']:
            tool_name = tool_call['tool_name']
            tool_stats[tool_name]['invoked'] += 1
            if tool_call['tool_status'] == 'success':
                tool_stats[tool_name]['success'] += 1
            else:
                tool_stats[tool_name]['failure'] += 1

    return tool_stats


@tool(annotations={"admin": "true"})
def summarize_tool_invocations() -> dict: 
    """For agentic app administrators: summarize how many tools has been invoked and their success states."""
    
    url = f"http://localhost:8095/analytics/service"
    
    try:
        url = "http://localhost:8095/analytics/service"
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "statement": "select a.* from `audits`.`agent_activity`.ToolCalls() AS a",
            "pretty": True
        }
        
        auth = (os.getenv('CB_USERNAME'), os.getenv('CB_PASSWORD'))

        response = requests.post(url, headers=headers, data=json.dumps(data), auth=auth)
        
        res = response.json()['results']
             
        tool_stats = analyze_tool_calls(res)
        
        return tool_stats
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

