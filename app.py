from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from dotenv import load_dotenv
import datetime
from couchbaseops import insert_doc, mutliple_subdoc_upsert, mutliple_subdoc_upsert
from langchainsetup import run_agent_langgraph
from sharedfunctions.print import print_error
from langchain.memory import ChatMessageHistory
from langchainsetup import generate_query_transform_prompt

# load the environment variables
load_dotenv()

# initiate the flask app and socketio
app = Flask(__name__)
socketio = SocketIO(app)

# initiate the chat history in memory
demo_ephemeral_chat_history = ChatMessageHistory()

# render the index.html template
@app.route('/')
def index():
    return render_template('index.html')


# SocketIO event handler for new messages
@socketio.on('message')
def handle_message(msg_to_process):
    print_error(f'\n\nNew customer message! "{msg_to_process}"\n\n')
    
    
    # add user message to chat history
    demo_ephemeral_chat_history.add_user_message(msg_to_process['message'])
    
    # incorporating the chat history together with the new questions to generate an independent prompt
    transformed_query = generate_query_transform_prompt(demo_ephemeral_chat_history.messages)
    print(f"Generated query: {transformed_query}")
    
    # insert into message collection 
    doc_to_insert = msg_to_process
    doc_to_insert["source"] = "web"
    doc_to_insert['transformed_query'] = transformed_query
    doc_to_insert["time"] = datetime.datetime.now().isoformat()
    message_id = insert_doc("main", "data", "messages", doc_to_insert)

    # run agent 
    response, run_id, run_url = run_agent_langgraph(transformed_query)
    final_reply = response['final_response']
    
    # update chat history with the response
    demo_ephemeral_chat_history.add_ai_message(final_reply)
    
    run_id = str(run_id)
    
    # insert into message_response collection
    message_response_doc = {
        "message_id": message_id,
        "response": final_reply,
        "time_iso": datetime.datetime.now().isoformat(),  
        "time": datetime.datetime.now().timestamp(),
        "run_id": run_id,
        "run_url": run_url
    }
    
    message_response_id = insert_doc("main", "data", "message_responses", message_response_doc)
    
    # update message doc
    mutliple_subdoc_upsert("main", "data", "messages", message_id, {
        "responded": True,
        "response_id": message_response_id,
        "run_id": run_id
    })
    
    # emit response to client
    socketio.emit("response", {
        # "message": final_reply,
        "run_id": run_id,
        "run_url": run_url,
        "response": response 
    })


# API endpoint to receive reply from the agent for rendering
@app.route('/receive_reply', methods=['POST'])
def receive_reply():
    data = request.get_json()
    message = data.get('message', '')
    
    socketio.emit("response", {
        "message": message
    })
    
    return { "status": "success" }


# API endpoint to get product details
@app.route('/product/<sku>', methods=['GET'])
def get_product_details(sku):
    try:
        # Fetch product details from Couchbase
        res = { 
            "image_path": "./static/images/cad.png",
            "last_update": "2024-09-01T00:00:00" 
            }
        
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": str(e)}), 404



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001)
