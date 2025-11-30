# BIBLICAL AI KNOWLEDGE BASE - INGESTION GUIDE

This guide explains how to add new knowledge (Scripture, Apocrypha, Church Fathers) to the **Biblical AI**.

**CRITICAL RULE:** 
The Biblical AI knowledge base must **ONLY** contain historical texts created **before 1000 AD**.
*   ✅ Allowed: KJV Bible, Book of Enoch, Maccabees, Ignatius, Polycarp.
*   ❌ Banned: Modern commentary, C.S. Lewis, Billy Graham, Reformation texts.

## Step 1: Add PDF Files
1.  Locate the new folder containing your historical PDFs.
2.  Move or copy your folder/PDFs into:
    `C:\Users\mwlac\BEACON_AI\biblical_ai\KB\` 
    *(or `biblical_ai\PDFs_Raw_Text\`)*

## Step 2: Convert PDF to Text
The AI reads `.txt` files. Convert your PDFs using the extraction tool.

**Command:**
```powershell
python pdf_to_text.py
```
*(This scans both Biblical folders automatically)*

## Step 3: Update the Knowledge Base (Embeddings)
This indexes the text into the Biblical AI's isolated memory.

**Command:**
```powershell
python generate_biblical_embeddings.py --model_type huggingface
```

*   **Note:** This script creates/updates `faiss_indexes/biblical_index`.
*   **Isolation:** This index is PHYSICALLY SEPARATE from the General AI index. There is no risk of cross-contamination as long as you put files in the correct folder in Step 1.

## Step 4: Verification
Run the health check to confirm the new files are indexed.

**Command:**
```powershell
python health_check.py
```
Check the **Biblical KB** count.
