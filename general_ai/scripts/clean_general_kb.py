import os
import sys
import re
import shutil
from pathlib import Path
from typing import List, TextIO

# Dynamically add the project root to sys.path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

from tqdm import tqdm
from shared_utils import setup_logging

# ========================= CONFIGURATION =========================

SOURCE_DIR = PROJECT_ROOT / "general_ai" / "knowledge_base"
CLEANED_DIR = SOURCE_DIR / "CLEANED"
LOG_FILE = PROJECT_ROOT / "general_deleted_log.txt"

# Regex Patterns
# 1. HTML Tags (Simple inline tags)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# 2. CSS/Code Lines: Starts with . or # or @, contains {, and doesn't look like a sentence
CSS_CODE_PATTERN = re.compile(r"^\s*[.#@][^{]*?{.*}")

# 3. Navigation/Web Noise
NAV_KEYWORDS_PATTERN = re.compile(
    r"\b(Login|Sign Up|Sign In|Register|Skip to content|Toggle navigation|Main Menu|Footer menu)\b", 
    re.IGNORECASE
)

# 4. Strict Legal Disclaimers (Only remove legal blocks, keep "In 1999...")
# Looks for "Copyright (c) Year" followed by "All rights reserved" or similar legal jargon
LEGAL_DISCLAIMER_PATTERN = re.compile(
    r"(Copyright|©).*?(All rights reserved|Terms of Use|Privacy Policy)", 
    re.IGNORECASE
)

# 5. Gutenberg Headers (Standard)
GUTENBERG_MARKERS = [
    re.compile(r"^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG", re.IGNORECASE),
    re.compile(r"^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG", re.IGNORECASE)
]

logger = setup_logging("CleanGeneralKB")

# ========================= FUNCTIONS =========================

def clean_file(file_path: Path, output_path: Path, log: TextIO) -> bool:
    """
    Cleans a single file using line-by-line processing to avoid regex freezing.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        cleaned_lines = []
        
        # State flags for block removal
        in_script = False
        in_style = False
        gutenberg_header_found = False
        gutenberg_footer_found = False

        # Pre-scan for Gutenberg range (optimization)
        start_idx = 0
        end_idx = len(lines)
        
        for i, line in enumerate(lines):
            if GUTENBERG_MARKERS[0].search(line):
                start_idx = i + 1
                gutenberg_header_found = True
            if GUTENBERG_MARKERS[1].search(line):
                end_idx = i
                gutenberg_footer_found = True
                break # Stop scanning once footer matches header context
        
        # Slice lines if Gutenberg markers existed
        if gutenberg_header_found:
            lines = lines[start_idx:end_idx]

        for line in lines:
            original_line = line
            stripped = line.strip()
            lower_line = stripped.lower()

            # --- 1. Block Detection (Script/Style) ---
            # Safe line-based check, no backtracking regex
            if "<script" in lower_line:
                in_script = True
                log.write(f"[{file_path.name}] REMOVED (Script Start): {stripped[:50]}...\n")
                continue
            if "</script>" in lower_line:
                in_script = False
                log.write(f"[{file_path.name}] REMOVED (Script End): {stripped[:50]}...\n")
                continue
            if "<style" in lower_line:
                in_style = True
                log.write(f"[{file_path.name}] REMOVED (Style Start): {stripped[:50]}...\n")
                continue
            if "</style>" in lower_line:
                in_style = False
                log.write(f"[{file_path.name}] REMOVED (Style End): {stripped[:50]}...\n")
                continue

            if in_script or in_style:
                # We are inside a block, discard line
                continue

            # --- 2. Line-Level Cleaning ---
            
            # Skip empty lines (we will consolidate blanks later)
            if not stripped:
                cleaned_lines.append("\n")
                continue

            # CSS/Code Check
            if CSS_CODE_PATTERN.match(line):
                log.write(f"[{file_path.name}] REMOVED (CSS/Code): {stripped[:50]}...\n")
                continue

            # Navigation Keywords
            if NAV_KEYWORDS_PATTERN.search(line):
                log.write(f"[{file_path.name}] REMOVED (Nav Noise): {stripped[:50]}...\n")
                continue

            # Legal Disclaimers (Strict)
            if LEGAL_DISCLAIMER_PATTERN.search(line):
                log.write(f"[{file_path.name}] REMOVED (Legal): {stripped[:50]}...\n")
                continue

            # --- 3. Content Sanitization (Keep line, but strip inline HTML) ---
            # Remove inline tags like <b>, <a href=\"...\">, </span>
            # BUT keep the text content inside them
            line_content = HTML_TAG_PATTERN.sub("", line)
            
            # If line became empty after stripping tags, skip it
            if not line_content.strip():
                continue

            cleaned_lines.append(line_content)

        # --- 4. Final Formatting ---
        # Join and fix multiple newlines
        full_text = "".join(cleaned_lines)
        full_text = re.sub(r'\n\s*\n', '\n\n', full_text) # Collapse multiple blanks to one

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)

        return True

    except Exception as e:
        logger.error(f"Failed to clean {file_path.name}: {e}")
        return False

def main():
    if not SOURCE_DIR.exists():
        logger.critical(f"Source directory not found: {SOURCE_DIR}")
        return

    logger.info("Starting General KB Cleaning...")
    
    # Prepare Log File
    with open(LOG_FILE, "w", encoding="utf-8") as log:
        log.write("---" + " General KB Deletion Log " + "---" + "\n\n")

        files_processed = 0
        
        # Recursive Walk
        # We must ignore the CLEANED directory itself to prevent infinite recursion
        all_files = []
        for root, dirs, files in os.walk(SOURCE_DIR):
            # Prune CLEANED directory from traversal
            if "CLEANED" in dirs:
                dirs.remove("CLEANED")
            
            for file in files:
                if file.lower().endswith(".txt"):
                    all_files.append(Path(root) / file)

        # Process Files
        for file_path in tqdm(all_files, desc="Cleaning Files"):
            # Calculate output path maintaining structure
            relative_path = file_path.relative_to(SOURCE_DIR)
            output_path = CLEANED_DIR / relative_path
            
            success = clean_file(file_path, output_path, log)
            if success:
                files_processed += 1

    logger.info(f"Cleaning Complete. Processed {files_processed} files.")
    logger.info(f"Cleaned files saved to: {CLEANED_DIR}")
    logger.info(f"Deletion log saved to: {LOG_FILE}")

if __name__ == "__main__":
    main()
