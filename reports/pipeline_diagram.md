# Knowledge-base pipeline diagram

```text
configured page images
        |
        v
load_pages ──> deterministic Page records
        |
        v
preprocess.run ──> cleaned Page records
        |
        v
layout.detect ──> ordered, bounded Region records
        |
        v
ocr.transcribe ──> NFC source Chunk records
        |
        v
chunk.split ──> fixed or rule-aware retrieval Chunks
        |
        v
embed.encode (BAAI/bge-m3, L2-normalized)
        |
        v
store.build (FAISS FlatIP + JSON chunk provenance)
        |
        v
store.load after restart ──> index + reconstructable Chunk records
```

The fixed pipeline order is implemented by `pipeline.build_knowledge_base()`.
`scripts/build_index.sh` invokes that entry point once; all generated index files
are written below the configured artifact directory rather than the source corpus.

The selected embedding model and chunking strategy must still be justified by the
executed Kaggle comparison in `notebooks/kb_demo.ipynb`; no unexecuted local run
is presented as a retrieval-quality result.
