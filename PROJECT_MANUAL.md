# BEACON_AI System Manual

## 1. Project Overview
**BEACON_AI** is a local, privacy-first Personal Assistant ecosystem. It employs a **Dual-Agent Architecture** to separate daily productivity tasks from strict theological study.

*   **Version:** Phase 2.0 (Expansion)
*   **Architecture:** Hybrid (Local Python + Cloud LLM)
*   **Interface:** Streamlit PWA ("Mobile Command Center") + CLI

## 2. Project Structure
```text
BEACON_AI/
├── beacon_ai/                  # Main Orchestration
│   └── main_agent.py           # The "Brain" (Router)
├── biblical_ai/                # The "Strict Scholar"
│   ├── core_ai.py              # Biblical RAG Logic
│   ├── feast_date_calculator.py# Calendar Logic
│   └── scripts/                # Sabbath Management
├── general_ai/                 # The "Office Manager"
│   ├── core_ai.py              # General RAG Logic
│   ├── dashboard/              # Mobile PWA
│   │   └── app.py              # Streamlit Interface
│   └── scripts/                # 15 Expansion Modules
│       ├── gamification_engine.py # LifeRPG Logic
│       ├── family_tracker.py   # GPS/Vehicle
│       ├── youtube_watcher.py  # Video Summarizer
│       └── ... (Vision, Finance, Sentry, etc.)
├── google_integration/         # Workspace Tools
│   ├── auth.py                 # OAuth 2.0 Logic
│   ├── budget_tracker.py       # Sheets API Logic
│   └── google_manager.py       # Integration Facade
├── shared_utils.py             # Logging, Config, Embeddings
└── requirements.txt            # Dependency Manifest
```

## 3. Dependencies
Core libraries required to run the system:
*   **Interface:** `streamlit`, `rich`
*   **AI/LLM:** `google-generativeai`, `langchain-google-genai`, `faiss-cpu`, `sentence-transformers`, `nest_asyncio`
*   **Data:** `pandas`, `pymupdf` (PDF), `pytesseract` (OCR)
*   **Automation:** `selenium`, `beautifulsoup4`, `youtube-transcript-api`
*   **System/IoT:** `paho-mqtt`, `python-nmap`, `pyaudio`, `pvporcupine`, `ephem`

## 4. Architectural Design
The system uses a **Hub-and-Spoke** architecture:
1.  **Hub:** `BeaconAgent` (in `main_agent.py`) is the central controller. It initializes sub-systems and routes queries based on intent (Biblical vs. General vs. Budget).
2.  **Spokes:** Specialized modules (Budget, YouTube, Gamification) operate independently but report back to the Hub.
3.  **Data Layer:**
    *   **Vector DB:** FAISS indexes for RAG (Biblical & General knowledge).
    *   **JSON Stores:** Local state for Gamification (`family_stats.json`) and User Context (`About Me.txt`).
    *   **Cloud:** Google Drive/Sheets for live document collaboration.

## 5. Security Measures
1.  **OAuth 2.0 User Auth:** Replaced Service Accounts to utilize the user's personal 2TB storage quota. Credentials (`geminicli_oauth_credentials.json`) are strictly local.
2.  **Git Protection:** `.gitignore` acts as a firewall, preventing API keys, OAuth tokens, and personal logs from being uploaded to GitHub.
3.  **Local Priority:** Location data and Vision processing occur locally or via ephemeral API calls; no third-party cloud storage for telemetry.

## 6. Build & Deployment
**Local Build:**
```powershell
# 1. Environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install
pip install -r requirements.txt

# 3. Setup
python generate_general_embeddings.py --force_refresh
```

**Deployment (Mobile PWA):**
To access from iPhone on the same Wi-Fi:
```powershell
streamlit run general_ai/dashboard/app.py --server.address 0.0.0.0
```
*Access via:* `http://[YOUR_PC_IP]:8501`

## 7. Configuration
*   **`google_config.json`:** Stores IDs for folders and spreadsheets.
*   **`.env`:** Stores `GOOGLE_API_KEY` for Gemini.
*   **`geminicli_oauth_credentials.json`:** OAuth Client Secret.

## 8. Data Models
*   **LifeRPG (`family_stats.json`):**
    ```json
    "Hunter": { "role": "Guardian", "xp": 1500, "level": 2, "badges": ["Clean Freak"] }
    ```
*   **Budget (`budget_tracker.py`):**
    *   Fixed Income: $2148.00
    *   Calculated: `Income - Sum(Expenses)`

## 9. Error Handling
*   **Async/Loop Conflicts:** Handled via `nest_asyncio` and synchronous wrappers (`respond_to_query_sync`) for Streamlit compatibility.
*   **Quota Limits:** `BudgetTracker` checks for existing files before creating duplicates.
*   **Corrupt Data:** `GamificationEngine` includes `reset_database()` to restore defaults if JSON is invalid.

## 10. License
**Proprietary / Personal Use.** Owned by Micheal LaCourse.
