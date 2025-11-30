import os
import fitz  # pymupdf
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from shared_utils import setup_logging, BIBLICAL_PDF_PATH, GENERAL_KB_PATH

logger = setup_logging("pdf_to_text")

async def extract_text_from_pdf(pdf_path: Path) -> None:
    """
    Extracts text from a PDF file and saves it to a .txt file with metadata headers.
    
    Args:
        pdf_path (Path): Path to the source PDF file.
    """
    try:
        # Construct output path (same directory, .txt extension)
        txt_path = pdf_path.with_suffix('.txt')
        
        # Skip if txt already exists and is newer than pdf
        if txt_path.exists() and txt_path.stat().st_mtime > pdf_path.stat().st_mtime:
            return

        logger.info(f"Processing: {pdf_path.name}")
        
        # Run CPU-bound PDF processing in a separate thread to be async-friendly
        # standard pymupdf is synchronous
        doc = fitz.open(pdf_path)
        
        full_text = []
        
        # Add File Metadata Header
        full_text.append(f"--- METADATA START ---")
        full_text.append(f"Source: {pdf_path.name}")
        full_text.append(f"Processed: {datetime.now().isoformat()}")
        full_text.append(f"--- METADATA END ---\n")
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                # Add Page Marker for smart chunking later
                full_text.append(f"\n--- Page {page_num + 1} ---\n")
                full_text.append(text)
                
        doc.close()
        
        # Write to file
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("".join(full_text))
            
        logger.info(f"Saved: {txt_path.name}")
        
    except Exception as e:
        logger.error(f"Failed to process {pdf_path.name}: {e}")

async def scan_and_process_directory(directory: Path):
    """
    Recursively scans a directory for .pdf files and processes them.
    """
    if not directory.exists():
        logger.warning(f"Directory not found: {directory}")
        return

    tasks = []
    # Walk through directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = Path(root) / file
                tasks.append(extract_text_from_pdf(pdf_path))
    
    if tasks:
        logger.info(f"Found {len(tasks)} PDF files in {directory.name}. Starting extraction...")
        await asyncio.gather(*tasks)
    else:
        logger.info(f"No new PDF files found in {directory.name}")

async def main():
    parser = argparse.ArgumentParser(description="PDF to Text Extractor for BEACON AI")
    parser.add_argument("--target_dir", type=str, help="Specific directory to process (optional)")
    args = parser.parse_args()

    logger.info("Starting PDF extraction pipeline...")
    
    target_directories = []
    if args.target_dir:
        target_directories = [Path(args.target_dir)]
    else:
        # Default directories
        target_directories = [BIBLICAL_PDF_PATH, GENERAL_KB_PATH]
    
    tasks = [scan_and_process_directory(d) for d in target_directories]
    await asyncio.gather(*tasks)
    
    logger.info("PDF extraction complete.")

if __name__ == "__main__":
    # Ensure paths exist
    BIBLICAL_PDF_PATH.mkdir(parents=True, exist_ok=True)
    GENERAL_KB_PATH.mkdir(parents=True, exist_ok=True)
    
    asyncio.run(main())