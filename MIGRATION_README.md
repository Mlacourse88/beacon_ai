# Migration Guide: Split FAISS Indexes

## Overview
We have separated the single `beacon_index` into two isolated indexes to ensure strict knowledge boundaries:
1. **Biblical Index (`faiss_indexes/biblical_index`)**: Only contains content from `biblical_ai/KB`.
2. **General Index (`faiss_indexes/general_index`)**: Only contains content from `general_ai/knowledge_base`.

## Migration Steps

### 1. Generate Biblical Embeddings
Run the dedicated script to process only biblical texts:
```bash
python generate_biblical_embeddings.py
```
*This will create `faiss_indexes/biblical_index` and `biblical_processed_files.json`.*

### 2. Generate General Embeddings
Run the dedicated script to process general/Scout texts:
```bash
python generate_general_embeddings.py
```
*This will create `faiss_indexes/general_index` and `general_processed_files.json`.*

### 3. Verify Isolation
Run the test scripts to ensure the Biblical AI cannot access Merit Badge info:
```bash
python biblical_ai/test_split_indexes.py
```
*Expect "PASS" for isolation tests.*

Run the General AI test to ensure it still works:
```bash
python general_ai/test_general_ai.py
```

## How to Update Indexes in Future

- **Adding a Bible Book/Apocrypha:**
  1. Place `.txt` file in `biblical_ai/KB/`.
  2. Run `python generate_biblical_embeddings.py`.

- **Adding a Merit Badge/General Doc:**
  1. Place `.txt` file in `general_ai/knowledge_base/`.
  2. Run `python generate_general_embeddings.py`.

*Note: `generate_gemini_embeddings.py` is now deprecated.*
