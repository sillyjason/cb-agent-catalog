# Load model directly
from transformers import AutoTokenizer, AutoModel

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")
model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L12-v2")

# Save the model and tokenizer locally
model.save_pretrained("./models/all-MiniLM-L12-v2")
tokenizer.save_pretrained("./models/all-MiniLM-L12-v2")