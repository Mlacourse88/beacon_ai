import asyncio
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

from shared_utils import setup_logging, FAISS_INDEX_PATH, PROJECT_ROOT, GENERAL_KB_PATH

logger = setup_logging("HealthCheck")

BIBLICAL_KB_PATH = PROJECT_ROOT / "biblical_ai" / "KB"

async def health_check_dashboard():
    print("\n=== BEACON AI SYSTEM HEALTH CHECK ===\n")

    # 1. FAISS Index Status
    print("--- FAISS Index Status ---")
    
    biblical_index_path = FAISS_INDEX_PATH / "biblical_index"
    general_index_path = FAISS_INDEX_PATH / "general_index"
    
    biblical_meta_path = FAISS_INDEX_PATH / "biblical_processed_files.json"
    general_meta_path = FAISS_INDEX_PATH / "general_processed_files.json"

    def get_index_status(name: str, index_path: Path, meta_path: Path):
        status = f"  {name}: ";
        if index_path.exists():
            size_mb = round(sum(f.stat().st_size for f in index_path.glob('*')) / (1024*1024), 2)
            status += f"✅ Exists (Size: {size_mb} MB)"
            
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        metadata = json.load(f)
                    status += f" - Indexed files: {len(metadata)}"
                except Exception: 
                    status += " - Metadata corrupt"
        else:
            status += "❌ Missing"
        print(status)

    get_index_status("Biblical Index", biblical_index_path, biblical_meta_path)
    get_index_status("General Index ", general_index_path, general_meta_path)
    print("")

    # 2. Source Data Status
    print("--- Source Data Status ---")
    def get_source_status(name: str, data_path: Path):
        status = f"  {name}: ";
        if data_path.exists():
            # Use rglob for recursive search
            txt_files = list(data_path.rglob('*.txt'))
            pdf_files = list(data_path.rglob('*.pdf'))
            status += f"Total TXT: {len(txt_files)}, Total PDF: {len(pdf_files)}"
        else:
            status += "❌ Path Missing"
        print(status)
    
    get_source_status("Biblical KB   ", BIBLICAL_KB_PATH) # Checks biblical_ai/KB
    get_source_status("General KB    ", GENERAL_KB_PATH)
    print("")
    
    # 3. Google Integration (Assumes validated)
    print("--- Google Integration ---")
    print("  Authentication: ✅ (Assumed from last run)")
    print("  Calendar Access: ✅ (Assumed from last run)")
    print("  Drive Access: ✅ (Assumed from last run)")
    print("  (Run google_integration/validate_setup.py for live check)")
    print("")
    
    print("--- Next Steps ---")
    print("  If indexes are missing, run: 'python generate_biblical_embeddings.py' and 'python generate_general_embeddings.py'")
    print("  After indexes are generated, test with: 'python beacon_ai/main_agent.py'")

if __name__ == "__main__":
    asyncio.run(health_check_dashboard())
