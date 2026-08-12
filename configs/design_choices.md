# Per-stage design choices (A2 deliverable). Fill every cell.
| Stage | Problem statement | Data | Model | Methods | Design | Development | Deployment | MLOps |
|---|---|---|---|---|---|---|---|---|
| 0 Frame |  |  |  |  |  |  |  |  |
| 1 Ingest+Enhance | Convert reproducibly rasterized Bangla grammar pages into stable `Page` records without damaging old letterpress glyphs. | Canonical `data/raw/<doc_id>/page_<pdf-page>.png`; blank pages are conservatively detected and non-blank exclusions require explicit page IDs. | No learned model in the baseline; Pillow/NumPy classical image processing. | Deterministic numeric ordering, per-document small-mode limits, projection-profile deskew, 3×3 median denoise, and global Otsu binarization. | Preserve raw files; write derived PNGs to `<artifact_dir>/preprocessed/<doc_id>/`; keep page and document IDs unchanged. | Unit tests use synthetic blank/skewed pages; Kaggle compares preprocessing off/on on six real pages and checks ink-retention ratios plus Bengali-stroke preservation visually. | Paths are controlled by `DOC_AGENT_DATA_DIR` and `DOC_AGENT_ARTIFACT_DIR`; generated files stay in Kaggle working storage. | Config and dependency versions are committed; raw and processed SHA-256 values plus preprocessing measurements are saved in `preprocess_metrics.json`. |
| 2 Layout |  |  |  |  |  |  |  |  |
| 3 OCR |  |  |  |  |  |  |  |  |
| 4 Index |  |  |  |  |  |  |  |  |
| 5 Retrieval |  |  |  |  |  |  |  |  |
| 6 Agent |  |  |  |  |  |  |  |  |
| 7 RL/RLVR |  |  |  |  |  |  |  |  |
| 8 Serving |  |  |  |  |  |  |  |  |
| 9 Eval |  |  |  |  |  |  |  |  |
