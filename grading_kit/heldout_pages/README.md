# Phase 3 held-out pages

The Phase 3 notebook selects 16 stable PDF pages: eight from the 1942
letterpress volume and eight from the 2026 NCTB volume. It renders 300-DPI
grayscale PNGs and packages them with a JSONL transcription template at:

```text
/kaggle/working/artifacts/phase3_labeling_bundle.zip
```

## Manual labeling protocol

1. Divide the 16 records among the three team members. Record the chosen
   person in `transcriber`; do not change the stable `page_id`.
2. Transcribe from the PNG only. Do not copy embedded PDF text, OCR output, or
   an online transcription. Preserve printed spelling, Bengali digits,
   punctuation, examples, and table reading order. Use `\n` for visible line
   breaks.
3. Record the visible folio in `printed_page`. It is separate from `pdf_page`.
4. A different member compares every character against the PNG, records their
   name in `reviewer`, and changes `review_status` to `reviewed`.
5. Unresolved characters go in `notes`; the record stays `pending` until the
   team resolves them. Do not silently guess.
6. Keep every selected page out of OCR fine-tuning, OCR model selection, and
   threshold tuning. These pages are evaluation data only.

## Rights gate

Both source PDFs are currently declared link-only in `data/provenance.md`.
The notebook therefore writes candidate PNGs to Kaggle artifacts, not to this
public repository. Obtain explicit instructor/rightsholder guidance before
committing any page image or full-page transcription. If redistribution is not
approved, keep the bundle private and ask the instructor how the grader should
receive the held-out slice.

Phase 3 is complete only when all 16 records in `../labels.jsonl` are manually
transcribed, independently reviewed, matched to permitted page images, and the
notebook's strict gate reports `PHASE 3 HELD-OUT LABELS: PASS`.
