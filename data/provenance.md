# Corpus provenance — Team 20

## Corpus identity

The Bangla Morphological Analyzer uses two Bangla grammar volumes as page images. The PDFs are link-only and are not committed to the public repository. In Kaggle they are attached through the team's private `bma-corpus` dataset.

| `doc_id` | Work | Year | Pages | Bytes | SHA-256 | Split |
|---|---|---:|---:|---:|---|---|
| `bhasha_prakash_1942` | *Bhasha-prakash Bangala Byakaran*, 2nd ed., Suniti Kumar Chatterji, Calcutta University | 1942 | 565 | 26,715,873 | `2e6a6e08e942d91e0986e2282ddeec9e6b4882ac6f4b89e083bf9bab6e72d39b` | train |
| `nctb_bangla_grammar_2026` | Bangla Grammar, Classes 9–10, National Curriculum and Textbook Board | 2026 | 218 | 143,145,319 | `3cb900fb1ce51bb91e13e41d43c51d98260a29ffffbed5632b0adee130640086` | test |

Combined source size: **169,861,192 bytes (161.99 MiB)**.

Combined raw page count: **783 pages**, above the 300-page requirement.

The executed Phase 6 Kaggle build loaded **775 usable pages**, produced OCR for all
775 of them in 3,428 source regions, and measured **195,803 usable OCR words**.
This exceeds the 60,000-word requirement. The committed `kb_demo.ipynb` records
the tested source commit, verified PDF hashes, full build counts, and PASS gate.

## Sources and usage rights

### 1942 volume

- Catalogue page: <https://archive.org/details/in.ernet.dli.2015.457377>
- Exact original PDF: <https://archive.org/download/in.ernet.dli.2015.457377/2015.457377.Bhasha-prakash-Bangala.pdf>
- Internet Archive/DLI identifier: `in.ernet.dli.2015.457377`
- The catalogue has historically described the scan as public-domain, but the author died in 1977 and the underlying-text copyright term may conflict with that label.
- Policy: **link only; non-commercial educational/research use; do not redistribute from this repository**.

### 2026 NCTB volume

- Official 2026 classes 9–10 book-list page: <https://nctb.gov.bd/pages/static-pages/695b99afc4774958d7b70612>
- The official page lists *বাংলা ভাষার ব্যাকরণ ও নির্মিতি* and provides these mirrors:
  - Google Drive: <https://drive.google.com/file/d/1yqoG73PYj6F8xlB-WTNfGSUk9Yf1z_tR/view?usp=drive_link>
  - Government eGovCloud: <https://drive.egovcloud.gov.bd/index.php/s/z7CNJUJAw9UuPv5>
  - Direct eGovCloud download used by the recreation script: <https://drive.egovcloud.gov.bd/index.php/s/z7CNJUJAw9UuPv5/download>
- Team source filename before renaming: `Secondary (BV)-2026_Class 9-10_Bangla Grammar_compressed.pdf`
- Kaggle private-dataset filename: `nctb_bangla_grammar.pdf`
- The direct download reports the same original filename and **143,145,319-byte** content length as the team's verified file.
- Free educational distribution is not the same as an open redistribution licence.
- Policy: **link only; educational use; do not redistribute from this repository**.

## Declared corpus revision from A1

A1 named the 2019 NCTB edition. The A2 implementation uses the team's available **2026, 218-page edition** instead. This is a corpus-version change, not a change to the domain, data speciality, NFR, or answer-F1 target. It must be disclosed in A2 Section 1 and confirmed with the instructor; hiding it would make A1/A2 provenance inconsistent.

## Data contract and stable identifiers

- Source PDFs are treated as images. Embedded/native PDF text is never used as the pipeline's OCR output.
- Rasterized images live under `data/raw/<doc_id>/page_<pdf-index>.png` and are gitignored.
- Page numbering in filenames is one-based and zero-padded, for example `page_0042.png`.
- Stable page ID format: `<doc_id>_p<four-digit-pdf-index>`.
- Store the PDF index and printed folio separately once printed-page offsets are verified for the 2026 edition.
- Original PDFs remain outside the repository, normally under the private Kaggle input directory.
- Generated/intermediate inventory lives under `data/interim/` and is gitignored.

## Split and leakage policy

- Train: all eligible pages from `bhasha_prakash_1942` except the validation chapter block and held-out labelled pages.
- Validation: one contiguous, whole-chapter block from the 1942 volume; exact chapter boundaries are selected after layout/OCR inspection.
- Test: `nctb_bangla_grammar_2026`.
- No document may appear in more than one document-level split.
- Because only two books exist, validation shares the train volume's author/era/typography and is used only for threshold/chunk tuning, not as the main generalization result.
- Repeated canonical grammar examples may occur in both books. Later evaluation must require the cited chunk to belong to the intended split/document.

## Exclusion policy

Drop covers, blank versos, scan targets/barcodes, accession-only pages, and imprint/credits pages when they contain no grammar content. Keep exercise pages but label them as exercises so distractor options cannot become sole evidence for a definition. Record the exact raw-to-usable page difference after ingest.

The Phase 4 loader automatically removes only near-blank pages using the conservative
thresholds recorded in `configs/config.yaml`. Non-blank exclusions are explicit stable
page IDs in `ingest.exclude_page_ids`; this prevents an image heuristic from silently
discarding grammar content. Small mode applies its page limit per document after these
exclusions.

The explicitly inspected non-content exclusions are:

- `bhasha_prakash_1942_p0001` — title/cover page;
- `bhasha_prakash_1942_p0003` — dedication/publication front matter;
- `nctb_bangla_grammar_2026_p0001` — front cover;
- `nctb_bangla_grammar_2026_p0002` — title page;
- `nctb_bangla_grammar_2026_p0003` — publication/credits page;
- `nctb_bangla_grammar_2026_p0218` — back cover.

Blank PDF pages such as the early blank versos are not duplicated in this list because
the recorded blank-page rule handles them. Contents, prefaces, grammar text, examples,
and exercises remain available to the pipeline.

## Scan and script difficulty

- Bangla conjuncts such as `দ্ব`, `ক্ষ`, `ঞ্চ`, `ষ্ঠ`, and `স্ক`.
- Dependent vowel signs, hasanta, reph, nukta, Bengali digits, দাঁড়ি, plus/equality signs, and rule notation.
- The 1942 scan adds letterpress variation, skew, ink bleed/show-through, stamps, and older orthography.
- The 2026 volume is cleaner but uses rule lists and exercise layouts whose reading order must be preserved.
- Errors are semantic: losing a matra or hasanta can change the rule itself, not merely its appearance.
