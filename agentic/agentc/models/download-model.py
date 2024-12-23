from transformers import AutoTokenizer, AutoModelForMaskedLM

model_name = "multi-qa-mpnet-base-cos-v1"

# Download the model and tokenizer
# model = AutoModel.from_pretrained(model_name)
# tokenizer = AutoTokenizer.from_pretrained(model_name)

tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")
model = AutoModelForMaskedLM.from_pretrained("sentence-transformers/multi-qa-mpnet-base-cos-v1")

# Save the model and tokenizer locally
model.save_pretrained("./models/multi-qa-mpnet-base-cos-v1")
tokenizer.save_pretrained("./models/multi-qa-mpnet-base-cos-v1")