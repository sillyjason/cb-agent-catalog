from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from agentic.tools import retrieve_order_info, get_product_details, get_policies, get_category_products, create_refund_ticket, calculate_refund_eligibility
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from agentic.prompts import general_support_prompt, product_fix_prompt, refund_policy_prompt, product_recommendation_prompt, content_finalizer_prompt, prep_prompt
from langchain_core.output_parsers import JsonOutputParser
from agentic.parser import parse_message
import time 
from langchain import callbacks
from sharedfunctions.print import print_success, print_bold
from langsmith import traceable, Client 
import agentc.langchain
import agentc
import langchain_core.tools
import uuid
import os 
from langchain_core.runnables import RunnableConfig

# load the environment variables
load_dotenv()

# model initialization
parser = JsonOutputParser()

# initiate langsmith client
langsmith_client = Client()

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
    sentiment: float
    message: str
    policy: str
    product_recommendation: str 
    product_fix: str 
    draft: str 
    messages: Annotated[list[AnyMessage], operator.add]
    
    refund_eligibility: str 
    refund_digest: dict
    
    order_id: str 
    order_data: dict 
    order_date: str
    product_id: str 
    
    final_response: str 
    
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
        results = []
        for t in tool_calls:
            print_success(f"\n\nBot is calling function: {t}\n\n")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                tool_name = t['name']
                
                function_args = t["args"]
                
                if tool_name == "calculate_refund_eligibility":
                    current_states = graph.get_state(config={"configurable": {"thread_id": thread_id}}).values 
                    
                    if "order_date" in current_states and current_states["order_date"]:
                        function_args["order_date"] = current_states["order_date"]
                
                result = self.tools[tool_name].invoke(function_args)
                print_success(f"Function call completed with {tool_name}. Result: {result}")
            
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print_success("Function call completed. Bot proceeding to the next step...")
        return {'messages': results }   



# prep node 
def prep_node(state: AgentState):
    
    tools = provider.get_tools_for(query="get customer previous messages", limit=2)
    print(f"tools: {tools}")
    # t = provider.get_tools_for(query="reasoning about a customer's happiness")
    
    # print(f"prompt: {p.prompt}")
    # system_prompt = SystemMessage(content=p.prompt.render(message=state['message']))
    # print(f"system prompt: {system_prompt.content}")
    # prep_agent_bot = Agent(agentc_model, p.tools, system=system_prompt.content)
    
    prep_agent_bot = Agent(agentc_model, tools)
    # print(f"prep agent bot: {prep_agent_bot}")
    # with_tools = chat_model.bind_tools(tools=p.tools)
    # print(f"with tools: {with_tools}")
    
    messages = [
        SystemMessage(content=prep_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    response = prep_agent_bot.graph.invoke({"messages": messages})
    print(f"response from prep_agent_bot: {response}")
    content = response['messages'][-1].content
    print(f"content of prep_agent_bot: {content}")
    
    return {
        "sentiment": content
    }


# general support node 
# general_tools = [retrieve_order_info, get_product_details]
# general_support_bot = Agent(model, general_tools, system=general_support_prompt)

def general_support_node(state: AgentState):
    print_bold("\n\nGeneral support agent bot is running...\n\n")
    
    print("this is where we start")
    tools = provider.get_tools_for(query="For general support agents to identify information relevant for further processing", limit=4)
    print("hopefully we see this!")
    # p = provider.get_prompt_for(query="Gather general information relevant to this message to pass down for further processing")
    # system_prompt = langchain_core.messages.SystemMessage(content=p.prompt)

    general_support_bot = Agent(agentc_model, tools, system=general_support_prompt)

    # messages = [
    #     SystemMessage(content=general_support_prompt), 
    #     HumanMessage(content=state['message'])
    # ]
    
    messages = [
        SystemMessage(content=general_support_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    # response = model.with_structured_output(GeneralSupportOutput).invoke(messages)
    response = general_support_bot.graph.invoke({"messages": messages})
    content = response['messages'][-1].content
    
    messages_dict = [message.pretty_repr() for message in response['messages']]
    
    state_to_update = { "draft": content }
    
    for pretty_msg in messages_dict:
        is_tool_message, function_name, json_data = parse_message(pretty_msg)
        
        if is_tool_message:
            if function_name == "retrieve_order_info":
                state_to_update['order_id'] = json_data['order_id'] if json_data else None
                state_to_update['order_data'] = json_data
                state_to_update['order_date'] = json_data['order_date'] if json_data else None
    
    
    return state_to_update


# product recommendation node 
product_recommendation_tools = [get_category_products]
product_recommendation_bot = Agent(agentc_model, product_recommendation_tools, system=product_recommendation_prompt)

def product_recommendation_node(state: AgentState): 
    print_bold("\n\nProduct recommendation agent bot is running...\n\n")
    
    messages = [
        SystemMessage(content=general_support_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    # response = model.with_structured_output(GeneralSupportOutput).invoke(messages)
    response = product_recommendation_bot.graph.invoke({"messages": messages})
    content = response['messages'][-1].content
    
    return {
        "product_recommendation": content
    }


# product fix prompt 
product_fix_tools = [get_policies]
product_fix_bot = Agent(agentc_model, product_fix_tools, system=product_fix_prompt)

def product_fix_node(state: AgentState): 
    print_bold("\n\nProduct fix agent bot is running...\n\n")
    
    messages = [
        SystemMessage(content=product_fix_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    # response = model.with_structured_output(GeneralSupportOutput).invoke(messages)
    response = product_fix_bot.graph.invoke({"messages": messages})
    content = response['messages'][-1].content
    
    return {
        "product_fix": content
    }


# refund node 
refund_tools = [get_policies, calculate_refund_eligibility]
refund_bot = Agent(agentc_model, refund_tools, system=refund_policy_prompt)

def refund_node(state: AgentState): 
    print_bold("\n\nRefund agent bot is running...\n\n")
    
    messages = [
        SystemMessage(content=refund_policy_prompt), 
        HumanMessage(content=state['message'])
    ]
    
    # response = model.with_structured_output(GeneralSupportOutput).invoke(messages)
    response = refund_bot.graph.invoke({"messages": messages})
    content = response['messages'][-1].content
    
    messages_dict = [message.pretty_repr() for message in response['messages']]
    
    state_to_update = { "refund_eligibility": content }
    
    for pretty_msg in messages_dict:
        # parse the message
        is_tool_message, function_name, json_data = parse_message(pretty_msg)
        
        if is_tool_message:
            if function_name == "calculate_refund_eligibility":
                state_to_update['refund_digest'] = json_data
    
    return state_to_update



# final reflection node
finalizer_tools = [create_refund_ticket]
finalizer_bot = Agent(agentc_model, finalizer_tools, system=content_finalizer_prompt)

def content_finalizer_node(state: AgentState):
    print_bold("\n\nFinalization agent is consolidating and working on final response...\n\n")
    
    print(f"final agent state: {state}")
      
    draft = state.get("") or ""
    message = state.get("message") or ""
    product_recommendation = state.get("product_recommendation") or ""
    product_fix = state.get("product_fix") or ""
    refund_eligibility = state.get("refund_eligibility") or ""
      
    assembled_information = "\n\n".join([product_recommendation, product_fix, refund_eligibility])
    
    messages = [
        SystemMessage(
            content=content_finalizer_prompt.format(assembled_information=assembled_information, draft=draft)
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
# builder.add_node("prep", prep_node)
builder.add_node("general_support", general_support_node)
# builder.add_node("recommendation", product_recommendation_node)
# builder.add_node("product_fixes", product_fix_node)
builder.add_node("refund", refund_node)
builder.add_node("finalizer", content_finalizer_node)
builder.set_entry_point("general_support")


# parallel connections
# builder.add_edge("prep", "general_support")
# builder.add_edge("general_support", "recommendation")
# builder.add_edge("general_support", "product_fixes")
builder.add_edge("general_support", "refund")
# builder.add_edge("recommendation", "finalizer")
# builder.add_edge("product_fixes", "finalizer")
builder.add_edge("refund", "finalizer")


# add memory and complie graph
memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(checkpointer=memory)


# run the agent
def run_agent_langgraph(message): 
    current_time_millis = time.time() * 1000.0
    
    with callbacks.collect_runs() as cb:
        response = graph.invoke(
            {"message": message},
            config={
                "configurable": {"thread_id": thread_id}
            }
        )
 
        # get langsmith run id       
        run_id = cb.traced_runs[0].id

        # get the run and url 
        run = langsmith_client.read_run(run_id)
        
        return response, run_id, run.url