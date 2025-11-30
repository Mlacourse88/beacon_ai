import time
import os
import sys
import re
from pathlib import Path
import logging
from typing import Tuple, List, TextIO

# Dynamically add the project root to sys.path for local imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Local imports (assuming shared_utils is at PROJECT_ROOT)
from shared_utils import setup_logging
from tqdm import tqdm

# ========================= CONFIGURATION =========================

SOURCE_KB_DIR = PROJECT_ROOT / "biblical_ai" / "KB"
CLEANED_KB_DIR = SOURCE_KB_DIR / "CLEANED"
DELETED_LINES_LOG_FILE = PROJECT_ROOT / "deleted_lines_log.txt"

# Regex patterns for Gutenberg markers
GUTENBERG_START_MARKER_PATTERN = re.compile(r"^\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)
GUTENBERG_END_MARKER_PATTERN = re.compile(r"^\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)

# Regex patterns for "Modern Junk" lines
MODERN_JUNK_PATTERNS = [
    re.compile(r"http://|www\.", re.IGNORECASE),
    re.compile(r"(?:Copyright|\(c\)).*?\b(?:19\d{2}|20\d{2})\b", re.IGNORECASE), # Year > 1900
    re.compile(r"Distributed Proofreaders|ISBN", re.IGNORECASE),
]

# New Regex patterns for web content cleaning

HTML_TAG_PATTERN = re.compile(r"<[^>]*?>")
CSS_CODE_LINE_PATTERN = re.compile(r"^\\s*[.#@][^{]*?{.*}$")
WEB_NAV_KEYWORDS = re.compile(r"\\b(?:Login|Sign Up|Search|Menu|Home|Skip to content)\\b", re.IGNORECASE)
MULTIPLE_BLANK_LINES_PATTERN = re.compile(r"\\n\\s*\\n(?=\\n)") # Matches 2+ blank lines, leaves one

# Regex pattern for lines to protect (verses/chapters)
# Matches: "1:1", "12", "Chapter 1", "Genesis 1"
VERSE_LINE_PATTERN = re.compile(r"^\\s*(?:\\d+:\\d+|\\d+|Chapter\\s+\\d+|[A-Z]+\\s+\\d+)\\b")

# Setup Logging
logger = setup_logging("CleanTxtFiles")

# ========================= HELPER FUNCTIONS =========================

def is_modern_junk(line: str) -> bool:
    """Checks if a line matches any 'modern junk' criteria."""
    for pattern in MODERN_JUNK_PATTERNS:
        if pattern.search(line):
            return True
    return False

def is_verse_line(line: str) -> bool:
    """Checks if a line starts with a number or Chapter/Book name, indicating it might be a verse or chapter."""
    return VERSE_LINE_PATTERN.match(line.strip()) is not None

def clean_file(file_path: Path, cleaned_dir: Path, deleted_lines_log_file: TextIO) -> Tuple[bool, int, str]:
    """
    Cleans a single text file by stripping Gutenberg markers, removing 'modern junk' lines, and web content.
    Logs removed lines to a file.
    
    Args:
        file_path: The path to the input text file.
        cleaned_dir: The base directory where cleaned files should be saved (maintaining subfolder structure).
        deleted_lines_log_file: An opened file handle to write removed lines to.
        
    Returns:
        Tuple[bool, int, str]: (True if cleaned successfully, number of lines removed, filename).
    """
    raw_content = ""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_content = f.read()
        
        initial_lines_count = len(raw_content.splitlines())
        current_content = raw_content
        lines_removed_count = 0

        # --- New Web Cleaning Steps ---


        # Step 2 (Tags): Remove all remaining HTML tags
        current_content = HTML_TAG_PATTERN.sub("", current_content)

        # Split into lines for line-based cleaning
        processed_lines: List[str] = current_content.splitlines(keepends=True) # Keep ends to count accurately
        cleaned_stage1_lines: List[str] = []
        in_script_block = False
        in_style_block = False

        for line in processed_lines:
            stripped_line = line.strip()

            # Check for verse protection first
            if is_verse_line(stripped_line):
                cleaned_stage1_lines.append(line)
                continue
            
            # Line-based removal for script/style blocks
            if "<script" in stripped_line.lower():
                in_script_block = True
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Script Block Start): {stripped_line}\n")
                continue
            if "</script>" in stripped_line.lower():
                in_script_block = False
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Script Block End): {stripped_line}\n")
                continue
            if "<style" in stripped_line.lower():
                in_style_block = True
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Style Block Start): {stripped_line}\n")
                continue
            if "</style>" in stripped_line.lower():
                in_style_block = False
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Style Block End): {stripped_line}\n")
                continue

            if in_script_block or in_style_block:
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Inside Block): {stripped_line}\n")
                continue
            
            # Step 3 (CSS/Code lines): Remove lines matching CSS/code pattern
            if CSS_CODE_LINE_PATTERN.search(stripped_line):
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (CSS/Code): {stripped_line}\n")
                continue

            # Step 4 (Web UI Noise): Remove lines with web navigation keywords
            if WEB_NAV_KEYWORDS.search(stripped_line):
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Web UI Noise): {stripped_line}\n")
                continue
            
            # Retain original 'modern junk' checks
            if is_modern_junk(stripped_line):
                lines_removed_count += 1
                deleted_lines_log_file.write(f"[{file_path.relative_to(SOURCE_KB_DIR)}] REMOVED (Modern Junk): {stripped_line}\n")
                continue
            
            cleaned_stage1_lines.append(line)

        # Rejoin lines for Gutenberg stripping and final formatting
        current_content = "".join(cleaned_stage1_lines)

        # --- Existing Gutenberg Strip (now on potentially cleaner content) ---
        start_idx = -1
        end_idx = -1
        temp_lines = current_content.splitlines(keepends=True)
        
        for i, line in enumerate(temp_lines):
            if GUTENBERG_START_MARKER_PATTERN.search(line) and start_idx == -1:
                start_idx = i
            if GUTENBERG_END_MARKER_PATTERN.search(line) and end_idx == -1 and start_idx != -1:
                end_idx = i
                break

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            current_content_lines = temp_lines[start_idx + 1: end_idx]
            logger.debug(f"Gutenberg markers stripped for {file_path.name}")
        elif start_idx != -1 and end_idx == -1:
            current_content_lines = temp_lines[start_idx + 1:]
            logger.debug(f"Gutenberg START marker stripped, no END marker found for {file_path.name}")
        elif start_idx == -1 and end_idx != -1:
            current_content_lines = temp_lines[:end_idx]
            logger.debug(f"Gutenberg END marker stripped, no START marker found for {file_path.name}")
        else:
            current_content_lines = temp_lines # Use all lines if no markers or incomplete markers
            logger.debug(f"No complete Gutenberg markers found in {file_path.name}, processing full file.")

        # --- Step 5 (Formatting): Replace multiple blank lines with a single blank line ---
        current_content = "".join(current_content_lines)
        current_content = MULTIPLE_BLANK_LINES_PATTERN.sub("\n\n", current_content)
        current_content = current_content.strip() # Final strip of leading/trailing whitespace

        final_lines_count = len(current_content.splitlines())
        # Adjust lines_removed_count to reflect actual lines removed after all processing
        # This is an approximation as block/tag removal changes line counts in a non-linear way
        lines_removed_count = initial_lines_count - final_lines_count

        # Preserve subfolder structure
        relative_path = file_path.relative_to(SOURCE_KB_DIR)
        output_file_path = CLEANED_KB_DIR / relative_path
        output_file_path.parent.mkdir(parents=True, exist_ok=True) # Create subdirectories if they don't exist
        
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(current_content)
            
        return True, lines_removed_count, str(file_path.relative_to(SOURCE_KB_DIR))

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False, 0, str(file_path.relative_to(SOURCE_KB_DIR))
    except Exception as e:
        logger.error(f"Error cleaning {file_path.name}: {e}")
        return False, 0, str(file_path.relative_to(SOURCE_KB_DIR))

# ========================= MAIN FUNCTION =========================

def main():
    if not SOURCE_KB_DIR.exists():
        logger.critical(f"Source directory not found: {SOURCE_KB_DIR}")
        return
    
    logger.info(f"Starting text file cleaning in {SOURCE_KB_DIR}")
    
    processed_count = 0
    total_removed_lines = 0

    # Open the deleted lines log file once
    with open(DELETED_LINES_LOG_FILE, "w", encoding="utf-8") as deleted_log_file:
        deleted_log_file.write(f"--- Deleted Lines Log for KB Cleaning ({os.path.basename(SOURCE_KB_DIR)}) ---\\n")
        deleted_log_file.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\\n")
        deleted_log_file.write("-" * 50 + "\\n\\n")
        logger.info(f"Deleted lines will be logged to {DELETED_LINES_LOG_FILE}")

        all_txt_files = list(SOURCE_KB_DIR.rglob("*.txt"))
        for file_path in tqdm(all_txt_files, desc="Cleaning files"):
            logger.info(f"Processing: {file_path.name}...")
            success, removed_lines, relative_filename = clean_file(file_path, CLEANED_KB_DIR, deleted_log_file)
            if success:
                processed_count += 1
                total_removed_lines += removed_lines
                logger.info(f"Cleaned {relative_filename} - Removed {removed_lines} lines.")
            else:
                logger.warning(f"Failed to clean {relative_filename}.")
            
    logger.info(f"Finished cleaning. Processed {processed_count} files. Total lines removed: {total_removed_lines}.")

if __name__ == "__main__":
    main()
