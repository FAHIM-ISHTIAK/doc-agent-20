# Phase 3 held-out pages

The Phase 3 notebook selects 12 stable PDF pages: six from the 1942
letterpress volume and six from the 2026 NCTB volume. It renders 300-DPI
grayscale PNGs, generates an EasyOCR typing draft, and packages them with a
JSONL transcription template at:

```text
/kaggle/working/artifacts/phase3_labeling_bundle.zip
```

## Manual labeling protocol

1. Divide the 12 records among the three team members. Record the responsible
   student's ID in `transcriber`; do not use names or change the stable
   `page_id`.
2. Use `ocr_draft` only as a typing aid. Compare every line with the PNG and
   place the corrected text in `text`; never treat the unreviewed draft as
   ground truth. Preserve printed spelling, Bengali digits, punctuation,
   examples, and table reading order. Use `\n` for visible line breaks.
   The historical pages include `easyocr_draft`, `qwen3_vl_8b_draft`, and the
   compatibility alias `qwen3_vl_draft`; `qwen3_vl_4b_draft` is retained when
   an earlier 4B result is present.
   `ocr_draft` records the candidate pre-filled into `text`. Check the image,
   not agreement between the models, when deciding the correct character.
3. Record the visible folio in `printed_page`. It is separate from `pdf_page`.
4. A different member compares every character against the PNG, records their
   student ID in `reviewer`, and changes `review_status` to `reviewed`.
5. Unresolved characters go in `notes`; the record stays `pending` until the
   team resolves them. Do not silently guess.
6. Keep every selected page out of OCR fine-tuning, OCR model selection, and
   threshold tuning. These pages are evaluation data only.

Allowed contribution IDs are `2105004` (Fahim), `2105001` (Nahid), and
`2105006` (Junaid). The notebook rejects names and any other identifier.

## Rights and review status

Both source PDFs remain link-only in `data/provenance.md`; the full PDFs and
full rendered corpora are not redistributed. The instructor approved committing
these 12 selected evaluation-page PNGs and their transcriptions to the public
course repository for grading. That approval is limited to this held-out course
evidence and does not change the corpus-wide link-only policy.

Phase 3 is complete: all 12 records in `../labels.jsonl` were manually
transcribed, independently reviewed by a member other than the transcriber,
matched to their approved page images, and accepted by the notebook's strict
`PHASE 3 HELD-OUT LABELS: PASS` gate.
