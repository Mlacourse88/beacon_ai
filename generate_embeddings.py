# -------------------------------
# generate_embeddings.py
# -------------------------------

import os
from openai import OpenAI

# Initialize OpenAI client using your environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------
# Folders to process
# -------------------------------
folders = [
    r"C:\Users\mwlac\BEACON_AI\biblical_ai\PDFs_Raw_Text",
    r"C:\Users\mwlac\BEACON_AI\biblical_ai\KB\Extra_Bible_Resources",
    r"C:\Users\mwlac\BEACON_AI\general_ai\knowledge_base\BoyScouts\merit_badges",
    r"C:\Users\mwlac\BEACON_AI\general_ai\knowledge_base\BoyScouts\worksheets"
]

# Output folder for embeddings
embeddings_folder = r"C:\Users\mwlac\BEACON_AI\embeddings"
os.makedirs(embeddings_folder, exist_ok=True)

# -------------------------------
# Function to embed a single text file
# -------------------------------
def embed_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    response = client.embeddings.create(
        model="text-embedding-3-small",  # or text-embedding-3-large
        input=text
    )

    embedding = response.data[0].embedding
    return embedding

# -------------------------------
# Process all .txt files in folders
# -------------------------------
for folder in folders:
    for file in os.listdir(folder):
        if file.lower().endswith(".txt"):
            file_path = os.path.join(folder, file)
            embedding = embed_text_file(file_path)

            # Save embedding to a .txt file
            base_name = os.path.splitext(file)[0]
            emb_file_path = os.path.join(embeddings_folder, base_name + "_embedding.txt")

            with open(emb_file_path, "w", encoding="utf-8") as ef:
                ef.write(str(embedding))

            print(f"Embedded: {file} -> {emb_file_path}")

print("All embeddings complete.")

