# GENERAL AI KNOWLEDGE BASE - INGESTION GUIDE

This guide explains how to add new knowledge (Merit Badges, Manuals, Reference Docs) to the **General AI**.

**IMPORTANT:** The General AI knowledge base is strictly separated from the Biblical AI. Do not mix biblical texts here.

## Step 1: Add PDF Files
1.  Locate the new folder containing your PDFs.
2.  **Option A (Recommended):** Move or copy your folder/PDFs into:
    `C:\Users\mwlac\BEACON_AI\general_ai\knowledge_base\`
    *You can create subfolders here to organize them.*

3.  **Option B (External Folder):** If you want to keep the files where they are, just note the full path (e.g., `C:\MyDownloads\New_Merit_Badges`).

## Step 2: Convert PDF to Text
The AI cannot read PDFs directly; they must be converted to text files first.

**Command:**
```powershell
python pdf_to_text.py
```
*(This automatically scans `general_ai/knowledge_base`)*

**If you used Option B (External Folder):**
```powershell
python pdf_to_text.py --target_dir "C:\MyDownloads\New_Merit_Badges"
```
*Note: You will then need to move the generated `.txt` files into `general_ai/knowledge_base` manually if you want them indexed.*

## Step 3: Update the Knowledge Base (Embeddings)
This step reads the text files and adds them to the AI's "brain" (FAISS Index).

**Command:**
```powershell
python generate_general_embeddings.py --model_type huggingface
```

*   **Note:** This script only processes *new* or *modified* files.
*   **Force Refresh:** If something seems wrong, you can force it to re-read everything:
    ```powershell
    python generate_general_embeddings.py --model_type huggingface --force_refresh
    ```

## Step 4: Verification
Run the health check to ensure your new files were counted.

**Command:**
```powershell
python health_check.py
```
Check the **General KB** count and **General Index** file count.
