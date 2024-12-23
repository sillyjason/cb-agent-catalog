from transformers import AutoModel, AutoTokenizer

model_name = "text-embedding-3-large-1536-embedding"

# Download the model and tokenizer
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Save the model and tokenizer locally
model.save_pretrained("./models/text-embedding-3-large-1536-embedding")
tokenizer.save_pretrained("./models/text-embedding-3-large-1536-embedding")