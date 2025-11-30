import os
import json
import hashlib
import asyncio
import argparse
import logging
import time
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any
import numpy as np

# Third-party imports
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# Local imports
from shared_utils import setup_logging, PROJECT_ROOT, load_faiss_index, FAISS_INDEX_PATH, get_embedding_model, DEFAULT_EMBEDDING_PROVIDER

# ========================= CONFIGURATION =========================

BIBLICAL_KB_DIRS = [
    PROJECT_ROOT / "biblical_ai" / "KB",
    PROJECT_ROOT / "biblical_ai" / "PDFs_Raw_Text"
]
INDEX_NAME = "biblical_index"
METADATA_FILE = FAISS_INDEX_PATH / "biblical_processed_files.json"


# Setup Logging
logger = setup_logging("GenerateBiblicalEmbeddings")



# ========================= FUNCTIONS =========================

def get_file_hash(file_path: Path) -> str:
    """
    Calculates MD5 hash of file content to detect changes.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        MD5 hash string.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return ""

def load_processed_metadata() -> Dict[str, str]:
    """Loads processed file metadata from JSON."""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading metadata file: {e}")
    return {}

def save_processed_metadata(metadata: Dict[str, str]):
    """Saves processed file metadata to JSON."""
    try:
        with open(METADATA_FILE, "w") as f:
            json.dump(metadata, f, indent=2)
    except IOError as e:
        logger.error(f"Error saving metadata file: {e}")

def load_documents(source_dirs: List[Path], processed_files: Dict[str, str]) -> Tuple[List[Document], Dict[str, str]]:
    """
    Loads new or modified documents from the specified directories.
    
    Args:
        source_dirs: List of directories to scan.
        processed_files: Dictionary of already processed files and hashes.
        
    Returns:
        Tuple of (List of new Documents, Updated metadata dictionary).
    """
    documents = []
    new_metadata = processed_files.copy()
    files_to_process = []

    for source_dir in source_dirs:
        if not source_dir.exists():
            logger.warning(f"Source directory not found: {source_dir}")
            continue

        # Scan directory
        for root, _, files in os.walk(source_dir):
            for file in files:
                if file.lower().endswith(".txt"):
                    file_path = Path(root) / file
                    file_hash = get_file_hash(file_path)

                    if file_hash and (file_path.name not in processed_files or processed_files[file_path.name] != file_hash):
                        files_to_process.append((file_path, file_hash))

    if not files_to_process:
        logger.info("No new documents to process.")
        return [], new_metadata

    logger.info(f"Processing {len(files_to_process)} new documents...")
    
    for file_path, file_hash in tqdm(files_to_process, desc="Loading Docs"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            
            doc = Document(
                page_content=text,
                metadata={
                    "source": file_path.name,
                    "path": str(file_path),
                    "type": "biblical",
                    "category": "biblical_text"
                }
            )
            documents.append(doc)
            new_metadata[file_path.name] = file_hash
        except (IOError, UnicodeDecodeError) as e:
            logger.error(f"Failed to read {file_path.name}: {e}")

    return documents, new_metadata

def process_texts_in_batches(
    vector_store: FAISS,
    chunks: List[Document],
    batch_size: int,
    delay: float = 0.0
) -> None:
    """
    Processes text chunks in batches and adds them to the vector store.
    Handles API rate limits via basic retry logic.
    
    Args:
        vector_store: FAISS instance.
        chunks: List of Document objects.
        batch_size: Number of chunks per batch.
        delay: Sleep time in seconds between batches (useful for API rate limits).
    """
    total_chunks = len(chunks)
    logger.info(f"Adding {total_chunks} chunks to index in batches of {batch_size}...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i : i + batch_size]
        try:
            vector_store.add_documents(batch)
            logger.info(f"Processed batch {i // batch_size + 1}/{(total_chunks // batch_size) + 1} ({len(batch)} chunks)")
            if delay > 0:
                time.sleep(delay)
        except Exception as e:
            logger.error(f"Error adding batch at index {i}: {e}")
            # Simple backoff retry strategy
            logger.info("Retrying batch in 10 seconds...")
            time.sleep(10)
            try:
                vector_store.add_documents(batch)
                logger.info(f"Retry successful for batch at index {i}")
            except Exception as retry_e:
                logger.critical(f"Failed to retry batch at index {i}: {retry_e}. Skipping this batch.")

def save_embeddings_to_npy(vector_store: FAISS, output_path: Path):
    """
    Exports the raw embeddings from the FAISS index to a .npy file.
    Note: This only works if the underlying index supports reconstruction.
    """
    try:
        # This is a simplified approach; accessing raw vectors depends on FAISS index type
        # Standard IndexFlatL2 supports this via reconstruct_n
        index = vector_store.index
        ntotal = index.ntotal
        if ntotal > 0:
            # Reconstruct all vectors
            # Note: This might be memory intensive for huge indexes
            vectors = index.reconstruct_n(0, ntotal)
            np.save(output_path, vectors)
            logger.info(f"Saved {ntotal} raw embeddings to {output_path}")
        else:
            logger.info("Index is empty, no embeddings to save.")
    except Exception as e:
        logger.error(f"Failed to export raw embeddings: {e}")

async def main():
    # CLI Argument Parsing
    parser = argparse.ArgumentParser(description="Generate Biblical FAISS Embeddings")
    parser.add_argument("--model_type", choices=["gemini", "huggingface"], default="gemini", help="Embedding model provider")
    parser.add_argument("--model_name", type=str, help="Specific model name (e.g., 'all-MiniLM-L6-v2')")
    parser.add_argument("--batch_size", type=int, default=100, help="Batch size for processing")
    parser.add_argument("--export_npy", action="store_true", help="Export raw embeddings to .npy file")
    parser.add_argument("--force_refresh", action="store_true", help="Ignore metadata and re-index all files")
    
    args = parser.parse_args()

    # 1. Setup Embeddings Model
    embeddings = None
    try:
        if args.model_type == "huggingface":
            batch_delay = 0.0  # No API delay needed for local model
        else:
            batch_delay = 2.0  # Add delay for Gemini API rate limits
        
        embeddings = get_embedding_model(provider=args.model_type, model_name=args.model_name) 
            
    except Exception as e:
        logger.critical(f"Failed to initialize embedding model: {e}")
        return

    # 2. Load Metadata
    processed_files = {} if args.force_refresh else load_processed_metadata()

    # 3. Load Documents
    raw_docs, new_metadata = load_documents(BIBLICAL_KB_DIRS, processed_files)
    if not raw_docs:
        logger.info("Biblical index is up to date.")
        return

    # 4. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        separators=["\n--- Page ", "\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(raw_docs)
    logger.info(f"Created {len(chunks)} chunks from {len(raw_docs)} documents.")

    # 5. Update/Create Index
    index_path_full = FAISS_INDEX_PATH / INDEX_NAME
    
    vector_store = None
    
    # Load existing if available (and compatible)
    if index_path_full.exists() and not args.force_refresh:
        logger.info("Loading existing biblical index...")
        vector_store = load_faiss_index(embeddings, INDEX_NAME)
        # Note: If switching model types, loading might fail or be semantically incompatible.
        # Ideally, different models should use different index names.
    
    # If load failed or creating new
    if vector_store is None:
        logger.info("Creating new biblical index...")
        # Initialize with first batch to create the structure
        first_batch = chunks[:args.batch_size]
        vector_store = FAISS.from_documents(first_batch, embeddings)
        remaining_chunks = chunks[args.batch_size:]
        if batch_delay > 0: time.sleep(batch_delay)
    else:
        remaining_chunks = chunks

    # Process remaining in batches
    if remaining_chunks:
        process_texts_in_batches(vector_store, remaining_chunks, args.batch_size, batch_delay)

    # 6. Save Index
    vector_store.save_local(str(index_path_full))
    save_processed_metadata(new_metadata)
    logger.info(f"Biblical index saved to {index_path_full}")
    
    # 7. Optional Export
    if args.export_npy:
        npy_path = FAISS_INDEX_PATH / "biblical_embeddings.npy"
        save_embeddings_to_npy(vector_store, npy_path)

if __name__ == "__main__":
    asyncio.run(main())