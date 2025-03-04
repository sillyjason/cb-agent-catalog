# filepath: /Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/agentic/embedding.py
from sentence_transformers import SentenceTransformer

# Load the locally downloaded model
model_path = "/Users/jc/Desktop/OtherTechies/Python_LangChain/agentic_customer_service_with_agentc/models/all-MiniLM-L12-v2"
model = SentenceTransformer(model_path)

# Generate embedding
def create_embeddings(input_message):
    embeddings = model.encode([input_message])[0]
    # Coembenvert embeddings to a list of floats
    embeddings_list = embeddings.tolist()
    return embeddings_list