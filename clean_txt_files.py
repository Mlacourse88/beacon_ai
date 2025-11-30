import os
import re

# -------------------------------
# Folders to clean
# -------------------------------
folders = [
    r"C:\Users\mwlac\BEACON_AI\biblical_ai\PDFs_Raw_Text",
    r"C:\Users\mwlac\BEACON_AI\biblical_ai\KB\Extra_Bible_Resources",
    r"C:\Users\mwlac\BEACON_AI\general_ai\knowledge_base\BoyScouts\merit_badges",
    r"C:\Users\mwlac\BEACON_AI\general_ai\knowledge_base\BoyScouts\worksheets"
]

# -------------------------------
# Cleaning function
# -------------------------------
def clean_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Remove common webpage artifacts and unwanted text
    text = re.sub(r"loading…", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Please\s+login.*?register", "", text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r"\n\s*\n", "\n", text)  # remove multiple blank lines
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # remove non-ASCII junk
    text = text.strip()

    # Overwrite cleaned file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Cleaned: {os.path.basename(file_path)}")

# -------------------------------
# Process all .txt files in folders
# -------------------------------
for folder in folders:
    for file in os.listdir(folder):
        if file.lower().endswith(".txt"):
            file_path = os.path.join(folder, file)
            clean_text_file(file_path)

print("All TXT files cleaned and ready for AI ingestion.")
