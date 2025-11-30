BEACON_AI Project - Detailed README
=====================================

1. Project Overview
-------------------
**Summary:**
BEACON_AI is a comprehensive, dual-agent AI personal assistant system designed to run on a hybrid architecture (Windows Laptop + Raspberry Pi). It separates concerns between a "General AI" for daily productivity, home automation, and family management, and a specialized "Biblical AI" for historical theological study.

**Core Purpose:**
To provide a secure, locally-controlled AI assistant that manages personal tasks, finances, family logistics, and knowledge retrieval while maintaining a strictly curated, historical environment for biblical study free from modern commentary.

**Key Features:**
*   **Dual-Agent Architecture:**
    *   *General AI:* The "Office Manager" and "HomeOS" handling broad queries, merit badge info, personal automation, news, and family logistics.
    *   *Biblical AI:* The "Strict Scholar" restricted to historical texts (Canon, Apocrypha, Church Fathers <1000 AD) with built-in feast day calculations.
*   **RAG (Retrieval-Augmented Generation) Pipeline:** Automated ingestion of PDFs and text files into a vector database (FAISS) using Google Gemini Embeddings.
*   **Hybrid Cloud/Local:** Leverages Google Gemini (Cloud) for heavy reasoning and local Python scripts (Raspberry Pi/PC) for automation and sensors.
*   **Feast Date Calculator:** Algorithmic determination of biblical feast dates based on ancient calendars and lunar phases.

2. Phase 2 Master Plan (15 Core Modules)
----------------------------------------
The General AI module is undergoing a massive expansion to serve as a complete "Family OS":

1.  **Mobile Command Center (`general_ai/dashboard`):** Web dashboard (Streamlit) for iPhone access to daily briefings, budget, and controls.
2.  **Family Operations (`general_ai/scripts/family_tracker.py`):** GPS location tracking dashboard and Vehicle Maintenance Log.
3.  **Kitchen OS (`general_ai/scripts/kitchen_manager.py`):** Recipe search, Pantry vision scanner (object detection), and Auto-shopping (Walmart/Amazon).
4.  **Media Intelligence (`general_ai/scripts/media_agent.py`):** Daily news scraper and YouTube video summarizer.
5.  **CFO (Finance) (`general_ai/scripts/finance_cfo.py`):** Receipt scanning (OCR), Budget forecasting, and "Safe-to-Spend" daily calculator.
6.  **Super Tutor (`general_ai/scripts/tutor_ai.py`):** Homework helper (Math/History) using Vision, and automatic Quiz generation.
7.  **Health Architect (`general_ai/scripts/health_architect.py`):** Allergy scanner, Spinal recovery PT planner, and Diet optimizer.
8.  **The Vault (`general_ai/scripts/the_vault.py`):** 5TB Local Search Engine for photos, docs, and manuals.
9.  **The Sentry (`general_ai/scripts/sentry_mode.py`):** Network security scanner (Nmap) and Energy usage monitor.
10. **Sabbath Automator (`biblical_ai/scripts/sabbath_manager.py`):** Precise sunset calculator that triggers "Commerce Guard" (Blocking shopping/finance apps) while enabling study modes.
11. **Family Achievement System (LifeRPG) (`general_ai/scripts/gamification_engine.py`):** Gamified chores, "Scholar's Quest" (grades), "Guardian Mode" (safety), "Scout Master" (badges), & "The Marketplace" (rewards).
12. **Red Button (`general_ai/scripts/emergency_protocol.py`):** Emergency offline info vault (Medical/Survival) and SOS signaling logic.
13. **Offline Independence (`general_ai/scripts/local_llm_handler.py`):** Capability to switch to a local LLM (Ollama) when internet connectivity is lost.
14. **IoT Nervous System (`general_ai/scripts/mqtt_bridge.py`):** MQTT Bridge to communicate with Smart Home devices (lights, locks) via Home Assistant.
15. **Voice Command Center (`general_ai/scripts/wake_word_engine.py`):** "Hotword" detection (e.g., "Hey Beacon") for hands-free voice control.

3. Current Functionality
------------------------
**General AI:**
*   **Knowledge Base:** Extensive library of Boy Scout Merit Badge pamphlets, survival guides, and general reference.
*   **Productivity:** Google Calendar/Sheets/Docs integration for scheduling and budgeting.
*   **Input:** Natural language queries.
*   **Output:** Context-aware answers, created documents, or updated spreadsheets.

**Biblical AI:**
*   **Feast Calculation:** Precise Gregorian dates for biblical feasts using lunar logic.
*   **Strict Retrieval:** Answers theological questions citing only allowed historical texts.

**Data Pipeline:**
*   `pdf_to_text.py` & `clean_txt_files.py`: Extract and sanitize text.
*   `generate_embeddings.py`: Vectorize knowledge base for FAISS.

4. Technical Stack
------------------
**Languages:**
*   Python 3.x (Primary)

**Frameworks & Libraries:**
*   **AI/ML:** `google-generativeai`, `langchain-google-genai`, `faiss-cpu`, `scikit-learn`, `ollama`.
*   **Vision:** `pillow`, `pytesseract`.
*   **Web/Dashboard:** `streamlit`, `flask`.
*   **Automation:** `selenium` (Shopping), `beautifulsoup4` (Scraping), `youtube-transcript-api`.
*   **System/Network:** `nmap`, `skyfield`/`ephem`, `paho-mqtt`.
*   **Audio/Voice:** `pyaudio`, `pvporcupine`.
*   **Data Processing:** `pymupdf`, `pandas`.

5. Setup & Installation
-----------------------
**Prerequisites:**
*   Python 3.9+ installed.
*   Google Cloud API Key (Gemini) & Service Account (Drive/Sheets).

**Step-by-Step Guide:**
1.  **Clone/Locate Project:** Root at `C:\Users\mwlac\BEACON_AI\`
2.  **Virtual Environment:** `python -m venv venv` -> `.\venv\Scripts\activate`
3.  **Install Dependencies:** `pip install -r requirements.txt`
4.  **Configuration:** Update `.env` and `google_config.json`.
5.  **Build Knowledge Base:** Run `pdf_to_text.py`, `clean_txt_files.py`, then `generate_embeddings.py`.

6. Usage
--------
**CLI:**
*   `python beacon_ai/main_agent.py` - Launches the main interactive chat interface.

**Web Dashboard:**
*   `streamlit run general_ai/dashboard/app.py --server.address 0.0.0.0` - Launches the Mobile Command Center.

7. Testing
----------
*   Run `pytest` from the project root.

8. License
----------
*   **Type:** Private / Proprietary (Personal Use)
*   **Owner:** Micheal LaCourse
