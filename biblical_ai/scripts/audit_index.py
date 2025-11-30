import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import csv

# Dynamically add the project root to sys.path for local imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

from tqdm import tqdm
from rich import print as rprint
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.embeddings import Embeddings

# Local imports
from shared_utils import setup_logging, get_api_key, FAISS_INDEX_PATH, get_embedding_model, DEFAULT_EMBEDDING_PROVIDER

# ========================= CONFIGURATION =========================

INDEX_NAME = "biblical_index"
AUDIT_REPORT_FILE = PROJECT_ROOT / "audit_evidence.csv" # Save in the project root, changed to CSV
LLM_MODEL_NAME = "models/gemini-2.0-flash"
LLM_TEMPERATURE = 0.0

PROMPT_TEMPLATE = """Analyze this text for modern commentary, dates post-1000 AD, or copyright notices.
    - If strictly historical scripture, reply 'PASS'.
    - If it contains modern text, reply 'FAIL | [Reason] | [Exact Quote of the bad text]'.

Text:
---
{text_content}
---

Your analysis:"""

# Setup Logging
logger = setup_logging("AuditIndex")

# ========================= FUNCTIONS =========================

def main():
    load_dotenv() # Load environment variables

    # 1. Initialize LLM
    try:
        llm = ChatGoogleGenerativeAI(
            model=LLM_MODEL_NAME,
            google_api_key=get_api_key(),
            temperature=LLM_TEMPERATURE
        )
        logger.info(f"Initialized LLM: {LLM_MODEL_NAME}")
    except Exception as e:
        logger.critical(f"Failed to initialize LLM: {e}")
        return

    # 2. Initialize Embeddings Model (needed for FAISS.load_local)
    try:
        # Use the default provider configured in shared_utils or explicitly 'gemini' for consistency
        embeddings_model = get_embedding_model(provider=DEFAULT_EMBEDDING_PROVIDER)
        logger.info(f"Initialized Embeddings Model using provider: {DEFAULT_EMBEDDING_PROVIDER}")
    except Exception as e:
        logger.critical(f"Failed to initialize embeddings model for FAISS loading: {e}")
        return

    # 3. Load FAISS Index
    index_path_full = FAISS_INDEX_PATH / INDEX_NAME
    vector_store = None
    if not index_path_full.exists():
        logger.critical(f"FAISS index not found at {index_path_full}. Please run generate_biblical_embeddings.py first.")
        return
    
    try:
        vector_store = FAISS.load_local(
            str(index_path_full),
            embeddings_model,
            allow_dangerous_deserialization=True
        )
        logger.info(f"Successfully loaded FAISS index '{INDEX_NAME}' from {index_path_full}")
    except Exception as e:
        logger.critical(f"Failed to load FAISS index '{INDEX_NAME}': {e}")
        return

    # 4. Iterate through documents and audit
    failures = []
    total_docs = len(vector_store.docstore._dict)
    
    # Prepare CSV report file
    try:
        with open(AUDIT_REPORT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Filename", "Status", "Reason", "Evidence"])
        logger.info(f"Audit report will be saved to {AUDIT_REPORT_FILE}")
    except IOError as e:
        logger.critical(f"Could not open audit report file for writing: {e}")
        return

    logger.info(f"Starting audit of {total_docs} documents...")

    kjv_skipped_message_printed = False

    for doc_id, doc in tqdm(vector_store.docstore._dict.items(), desc="Auditing Documents"):
        file_name = doc.metadata.get("source", "UNKNOWN_FILE")
        page_content = doc.page_content

        # New Logic: Skip KJV Bible
        if "KJV" in file_name or file_name == "KJV_Bible.txt":
            if not kjv_skipped_message_printed:
                logger.info("Skipping KJV_Bible.txt (and other KJV-related files) to focus on other texts.")
                kjv_skipped_message_printed = True
            # Optionally write to CSV that it was skipped, or just continue
            try:
                with open(AUDIT_REPORT_FILE, "a", newline="", encoding="utf-8") as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([file_name, "SKIPPED", "Explicitly skipped KJV file", ""])
            except IOError as e:
                logger.critical(f"Error writing skipped KJV status to audit report file: {e}")
            continue

        if not page_content.strip():
            logger.warning(f"Skipping empty document for {file_name} (ID: {doc_id})")
            continue

        prompt_content = PROMPT_TEMPLATE.format(text_content=page_content)
        
        status = "UNKNOWN"
        reason = ""
        evidence = ""

        try:
            response = llm.invoke(prompt_content)
            response_text = response.content.strip()
            time.sleep(4) # Rate limiting

            if response_text.startswith("FAIL |"):
                parts = response_text.split("|", 2)
                if len(parts) == 3:
                    status = "FAIL"
                    reason = parts[1].strip()
                    evidence = parts[2].strip()
                    rprint(f"[red]FAIL: {file_name} - {reason} - Evidence: {evidence}[/red]")
                    failures.append({"file": file_name, "reason": reason, "evidence": evidence, "content_preview": page_content[:200]})
                else:
                    status = "FAIL_PARSE_ERROR"
                    reason = "LLM response format incorrect"
                    evidence = response_text
                    rprint(f"[red]FAIL (Parse Error): {file_name} - {response_text}[/red]")
            elif response_text.startswith("PASS"):
                status = "PASS"
                # rprint(f"[green]PASS: {file_name}[/green]") # Uncomment to see passes
            else:
                status = "UNKNOWN_RESPONSE"
                reason = "LLM returned unexpected response"
                evidence = response_text
                rprint(f"[yellow]UNKNOWN LLM RESPONSE for {file_name}: {response_text}[/yellow]")

        except Exception as e:
            status = "ERROR"
            reason = f"Error during LLM invocation: {e}"
            evidence = ""
            error_msg = f"Error processing {file_name} (ID: {doc_id}): {e}"
            rprint(f"[red]{error_msg}[/red]")
            failures.append({"file": file_name, "reason": reason, "evidence": evidence, "content_preview": page_content[:200]})
        
        # Write to CSV
        try:
            with open(AUDIT_REPORT_FILE, "a", newline="", encoding="utf-8") as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([file_name, status, reason, evidence])
        except IOError as e:
            logger.critical(f"Error writing to audit report file: {e}")

    logger.info("-" * 50)
    logger.info(f"Audit complete. Total documents: {total_docs}, Total failures (including parse/errors): {len(failures)}")
    if failures:
        logger.info(f"Details of failures saved to {AUDIT_REPORT_FILE}")

if __name__ == "__main__":
    main()