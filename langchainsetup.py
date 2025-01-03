from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from agentic.prompts import general_support_prompt, content_finalizer_prompt
from langchain_core.output_parsers import JsonOutputParser
from agentic.parser import parse_message
import time 
from langchain import callbacks
from sharedfunctions.print import print_success, print_bold, print_error
import agentc.langchain
import agentc
import langchain_core.tools
import uuid
import os 
from langchain_core.runnables import RunnableConfig
import json 


# load the environment variables
load_dotenv()

# model initialization
parser = JsonOutputParser()

# initiate the chat model
model = ChatOpenAI(temperature=0, model="gpt-4o-2024-05-13")

# agentc setup
session = uuid.uuid4().hex
provider = agentc.Provider(
    decorator=lambda t: langchain_core.tools.tool(t.func),
    secrets={
        "CB_CONN_STRING": os.getenv("CB_CONN_STRING"),
        "CB_USERNAME": os.getenv("CB_USERNAME"),
        "CB_PASSWORD": os.getenv("CB_PASSWORD")
    }
)


# noinspection SpellCheckingInspection
auditor = agentc.Auditor(agent_name="jc-agent-with-tanvi", conn_string=os.getenv("AGENT_CATALOG_CONN_STRING"), username=os.getenv("AGENT_CATALOG_USERNAME"), password=os.getenv("AGENT_CATALOG_PASSWORD"), bucket=os.getenv("AGENT_CATALOG_BUCKET"))    
agentc_model = agentc.langchain.audit(model, auditor=auditor, session=session)

# generate a unique thread id by getting current time in unix
thread_id = str(int(time.time()))


# agent state and agent 
class AgentState(TypedDict):
    message: str
    messages: Annotated[list[AnyMessage], operator.add]
    
    products: list
    defects: list
    
    tools_invocations: dict 
    cad: dict
    
    none_of_tools_invoked: bool
    
    tickets: list    
    final_response: str 
    
    engineer_mode: bool 
    admin_mode: bool 
    
class Agent:
    def __init__(self, model, tools, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        
        # initiate the tool message results
        message_results = []
        
        # initiate the updated state dict 
        res = {}
        
        for t in tool_calls:
            print_success(f"\n\nBot is calling function: {t}\n\n")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                # invoke the tool function
                tool_name = t['name']
                print(f"tool_name: {tool_name}")
                function_args = t["args"]
                result = self.tools[tool_name].invoke(function_args)
                print(f"result: {result}")
                
                # update the state dict with the result
                if tool_name == "defect_search":
                    res['defects'] = result 
                
                if tool_name == "get_products_details":
                    res['products'] = result
                
                if tool_name == "get_tickets_by_sku":
                    res['tickets'] = result
                
                if tool_name == "get_sku_cad":
                    res['cad'] = result
                
                if tool_name == "summarize_tool_invocations":
                    res['tools_invocations'] = result 
                    
                print_success(f"Function call completed with {tool_name}. Result: {result}")
            
            message_results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        
        res['messages'] = message_results
        
        print_success("Function call completed. Bot proceeding to the next step...")
        return res


# general support node 
def general_support_node(state: AgentState):
    
    print_bold("\n\nGeneral support agent bot is running...\n\n")
    
    # get the engineer mode from the state, and use it to determine what tools to use
    engineer_mode = state.get("engineer_mode", True)
    admin_mode = state.get("admin_mode", False)
    
    role = "ADMIN" if admin_mode else "ENGINEER" if engineer_mode else "FINANCE"
    print_bold(f"engineer_mode: {engineer_mode}, admin_mode: {admin_mode}; role: {role}")
  
    # define annotation based on modes 
    annotations = 'admin="true"' if admin_mode else 'engineer="true"' if engineer_mode else 'finance="true"' 
    
    # get tools from agentc provider 
    tools = provider.get_tools_for(query="For general support agents", limit=10, annotations=annotations)
    
    # print the tools information 
    print_bold(f"Found {len(tools)} tools:")
    for tool in tools:
        print(f"{tool.name}")
 
    # define general support bot 
    general_support_bot = Agent(agentc_model, tools, system=general_support_prompt)

    # define messages passed into the bot 
    messages = [
        SystemMessage(content=general_support_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    # get response from langgraph
    response = general_support_bot.graph.invoke({"messages": messages})
    
    
    # update states from response 
    state_to_update = {}
    
    print("initiating state update...")
    
    # if 'defects' in response:
    #     state_to_update['defects'] = response['defects']
    
    # if 'products' in response:
    #     state_to_update['products'] = response['products']
        
    # if 'tickets' in response:
    #     state_to_update['tickets'] = response['tickets']
    
    # if 'cad' in response:
    #     state_to_update['cad'] = response['cad']
        
    # if 'tools_invocations' in response: 
    #     state_to_update['tools_invocations'] = response['tools_invocations']
        
        
    # update the state with the response
    found_info = False 
    for field in ['defects', 'products', 'tickets', 'cad', 'tools_invocations']:
        if field in response: 
            found_info = True 
            print(f"updating state with {field}...")
            state_to_update[field] = response[field]
    
    if not found_info:
        state_to_update['none_of_tools_invoked'] = True
        
    
    return state_to_update



# final reflection node
def content_finalizer_node(state: AgentState):
    print_bold("\n\nFinalization agent is consolidating and working on final response...\n\n")
    
    print(f"final agent state: {state}")
    
    tools = provider.get_tools_for(name="get_products_details")
    finalizer_bot = Agent(agentc_model, tools)
      
    message = state.get("message") or ""
      
    information_passed_down = json.dumps(state)
    
    messages = [
        SystemMessage(
            content=content_finalizer_prompt.format(information_passed_down=information_passed_down)
        ),
        HumanMessage(content=message)
    ]
    
    response = finalizer_bot.graph.invoke({"messages": messages})
    content = response['messages'][-1].content
    
    return {
        "final_response": content
    }
    
    
# build the graph and add nodes 
builder = StateGraph(AgentState)
builder.add_node("general_support", general_support_node)
builder.add_node("finalizer", content_finalizer_node)
builder.set_entry_point("general_support")

# parallel connections
builder.add_edge("general_support", "finalizer")

# add memory and complie graph
memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(checkpointer=memory)


# run the agent
def run_agent_langgraph(message, engineer_mode, admin_mode): 
    try: 
        with callbacks.collect_runs() as cb:
            response = graph.invoke(
                {
                    "message": message,
                    "engineer_mode": engineer_mode,
                    "admin_mode": admin_mode
                },
                config={
                    "configurable": {"thread_id": thread_id}
                }
            )
            
            return response
    except Exception as e:
        print_error(f"An error occurred running langgraph: {e}")
        return {
            'final_response': 'Oops an error occured. Ask Jason to work on his agentic development skills.'
        }



# function to transform the query based on message history
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

query_transform_prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="messages"),
        (
            "user",
            "Given the above conversation, rewrite the user question to be specific and clear.",
        ),
    ]
)
 
query_transformation_chain = query_transform_prompt | model

def generate_query_transform_prompt(messages):
    return query_transformation_chain.invoke({"messages": messages}).content 