# A2 handover: 2105004 → 2105001

Date: 2026-08-12  
Project: Team 20 — Bangla Morphological Analyzer  
Repository: <https://github.com/FAHIM-ISHTIAK/doc-agent-20>  
Detailed phase plan: [`A2_PLAN.md`](A2_PLAN.md)

## 1. Purpose of this handover

This document records the repository's actual state after Phase 4. It is a
short operational companion to `A2_PLAN.md`, whose allocation table is still a
planning template and contains outdated `TBD`/`Not started` entries.

Work completed so far was performed by `2105004`. The next implementation lead
is `2105001`, beginning with Phase 5 (layout detection and reading order).

## 2. Team identifiers

- `2105004` — Fahim; completed Phases 0–4.
- `2105001` — Redom; next lead.
- `2105006` — Junaid.

Use student IDs in assignment contribution/review fields. Every member must
commit under their own GitHub-linked email and must commit only work they
actually performed.

## 3. Git state at handover

- Completed work branch: `fahim`
- Latest completed Phase 4 commit: `de5f857`
- `fahim` is pushed to `origin/fahim`.
- At the time this file was written, `main` still pointed to the starter
  `A1 start` commit and was 17 commits behind `fahim`.
- `fahim` must therefore be merged into `main` with commit history preserved
  before `2105001` creates a new phase branch from `main`.

Do not squash the Phase 0–4 commits. Use a reviewed GitHub pull request and
**Create a merge commit** so the contribution history remains visible.

Recommended Phase 5 branch after that merge:

```bash
git switch main
git pull origin main
git switch -c 2105001/phase-5-layout
git push -u origin 2105001/phase-5-layout
```

Before committing, `2105001` should configure and confirm their own identity:

```bash
git config user.name "2105001"
git config user.email "EMAIL_LINKED_TO_2105001_GITHUB_ACCOUNT"
git config --get user.name
git config --get user.email
```

## 4. Fixed project decisions

- Domain: Bangla grammar and morphology.
- Data speciality: Bangla script, including conjuncts, matras, hasanta, reph,
  Bengali digits, old spelling, and historical letterpress scans.
- Primary NFR: explainability.
- NFR target: rule-attribution coverage `>= 0.90`.
- Success metric: answer-F1, target `>= 0.70`.
- Runtime: Kaggle; raw PDFs are attached privately, while generated evidence is
  copied back into Git.
- PDF native/embedded text must never be used as the system OCR output.
- Unicode normalization for OCR text is NFC, not NFKC.
- The fixed Pydantic contracts in `src/doc_agent/contracts.py`, pipeline stage
  order, hook seams, and locked tool names must not be changed.

## 5. Corpus currently used

| Document ID | Document | PDF pages | Split |
|---|---|---:|---|
| `bhasha_prakash_1942` | *Bhasha-prakash Bangala Byakaran*, 1942 | 565 | train |
| `nctb_bangla_grammar_2026` | NCTB classes 9–10 Bangla Grammar, 2026 | 218 | test |

Total: 783 PDF pages.

The A1 form named a 2019 NCTB edition, but A2 uses the available 2026,
218-page edition. This corpus revision must be disclosed in the A2 form and
confirmed with the instructor.

The full PDFs are link-only/private and must not be committed. Provenance,
hashes, source URLs, exclusions, and split policy are documented in
`data/provenance.md`. Kaggle currently discovers these renamed input files:

```text
bhasha_prakash_1942.pdf
nctb_bangla_grammar.pdf
```

## 6. What has been completed

### Phase 0 — repository and team setup

- Public GitHub repository created.
- Collaborators added.
- Kaggle used as the execution environment.
- Stable team IDs recorded: `2105004`, `2105001`, `2105006`.
- Initial configuration and repository workflow established.

### Phase 1 — corpus contract and EDA

- Both source PDFs discovered and verified in Kaggle.
- Exact document IDs, page counts, byte sizes, SHA-256 hashes, sources, and
  train/test split recorded.
- Corpus totals and real scan characteristics inspected.
- The A1-to-A2 NCTB edition change documented.
- `scripts/get_data.sh` can inventory or render the corpus into canonical paths:

```text
data/raw/<doc_id>/page_<one-based-pdf-page>.png
```

### Phase 2 — reproducible Kaggle runtime

- Dependency versions pinned in `requirements.lock`/`pyproject.toml`.
- Environment-driven paths and small/full modes implemented.
- Kaggle import, configuration, reproducibility, and configuration tests passed.
- `doc_agent` imports successfully from the cloned repository.

### Phase 3 — held-out pages and human ground truth

- Twelve held-out pages selected: six historical and six NCTB.
- Samples cover clean text, old letterpress, conjunct-heavy rules, numbered
  rules, exercises, tables, morphology, and difficult scans.
- EasyOCR produced the clean NCTB drafts.
- Qwen3-VL 8B produced the improved historical drafts.
- The historical `text` labels were replaced with supplied corrected human
  transcriptions; OCR drafts remain separately preserved for CER/WER analysis.
- Printed folios, student IDs, independent-review fields, and image hashes are
  present in `grading_kit/labels.jsonl`.
- All twelve held-out PNGs are in `grading_kit/heldout_pages/` with matching
  hashes.
- The executed notebook reports:

```text
PHASE 3 HELD-OUT LABELS: PASS
```

Qwen3-VL 8B is not required for Phase 5. Retain its configuration and Phase 3
evidence for the formal OCR comparison in Phase 6.

### Phase 4 — deterministic ingest and preprocessing

Implemented in:

```text
src/doc_agent/ingest/loader.py
src/doc_agent/ingest/preprocess.py
tests/test_ingest.py
configs/config.yaml
data/provenance.md
configs/design_choices.md
notebooks/eda.ipynb
```

Implemented behavior:

- canonical and flat held-out filename loading;
- stable `Page.id`, `doc_id`, and absolute `image_path` values;
- deterministic document/page ordering;
- per-document small-mode limits;
- conservative blank-page detection;
- explicit verified non-content exclusions;
- projection-profile deskew;
- 3×3 median denoising;
- global Otsu binarization;
- preservation of raw inputs;
- derived images written only below the artifact directory.

Phase 4 Kaggle evidence reports:

```text
PHASE 4 INGEST TESTS: PASS
PHASE 4 REAL-PAGE SMALL-MODE INGEST: PASS
PHASE 4 CLASSICAL PREPROCESSING: PASS
PHASE 4 BEFORE/AFTER GALLERY: READY FOR HUMAN CHECK
```

All five ingest tests passed. The six real-page clean/raw ink ratios were about
`1.07–1.14`, and visual inspection retained Bengali matras, conjunct strokes,
digits, and table rules. No OCR/VLM was loaded during this phase.

## 7. Start here: Phase 5 layout and reading order

Primary files:

```text
src/doc_agent/vision/layout.py
tests/test_ocr.py   # or the existing appropriate test home
configs/config.yaml
notebooks/eda.ipynb # add saved real-page visual evidence
configs/design_choices.md
```

The fixed interface is:

```text
clean list[Page] -> layout.detect(pages, cfg) -> ordered list[Region]
```

`Region` is fixed and contains only:

```python
page_id: str
bbox: tuple[int, int, int, int]
kind: str  # text | table | figure | heading
```

Phase 5 implementation order:

1. Read `A2_PLAN.md`, `src/doc_agent/contracts.py`, the implemented loader and
   preprocessor, `src/doc_agent/vision/layout.py`, and the current tests.
2. Start with a simple deterministic baseline appropriate for mostly
   single-column pages; do not introduce a large learned layout model without
   measured need.
3. Detect valid regions for running text, headings, numbered rule blocks,
   exercises, and tables/figures.
4. Preserve reading order. A global `(y, x)` sort can mix table columns or
   multi-column blocks and is not sufficient by itself.
5. Ensure every bounding box remains within its source image and has positive
   area.
6. Ensure every region keeps the exact originating `page_id`.
7. Add real unit tests instead of leaving the skipped placeholder.
8. Visualize bounding boxes and numeric reading order on representative
   historical, clean NCTB, numbered-rule, exercise, and table pages in Kaggle.
9. Save the executed notebook output and document the Stage 2 design choice.

Required exit gate:

- visual samples show acceptable region coverage and reading order;
- output conforms to the fixed `Region` contract;
- every crop is valid without notebook-only special cases;
- deterministic tests pass;
- the next OCR stage can consume the ordered regions directly.

Suggested commits by `2105001`:

```text
feat(layout): detect Bangla grammar page regions
feat(layout): preserve rule and table reading order
test(layout): validate bounds ordering and page linkage
notebook(eda): record Phase 5 layout validation
```

## 8. Kaggle workflow for the next lead

1. Work and commit on `2105001/phase-5-layout`.
2. Push source and tests before the Kaggle evidence run.
3. In the notebook bootstrap, set `REPO_BRANCH` to the Phase 5 branch.
4. Clone/pull that branch in Kaggle.
5. Phase 5 does not require Qwen3-VL and ordinarily does not require a GPU.
6. Run small mode first on representative committed held-out pages.
7. Download the executed notebook and replace the repository copy.
8. Commit the executed notebook under `2105001`'s own identity.
9. Open a PR into `main`; request another member's review and preserve commits.

Do not use **Run All** merely to validate a later lightweight phase: that would
rerun the expensive Phase 3 Qwen cells. Make the new Phase 5 section independently
runnable, as the Phase 4 section is.

## 9. Known pending work and cautions

- `grading_kit/manifest.yaml` still says the held-out labels are pending even
  though Phase 3 passed. Update that status before A2 submission after confirming
  the final review/rights wording.
- The manifest/provenance call the full PDFs link-only. Only the small grading
  samples are committed, as the handbook requests. Confirm the instructor's
  expected public-sample/rights wording rather than silently claiming an open
  licence.
- The corpus word count remains `0`/pending. Phase 6 must replace it with the
  measured usable OCR word count and verify it exceeds 60,000.
- The first six records name `2105001` as reviewer and the last six name
  `2105006`. Those reviews must have genuinely occurred; IDs/flags alone are not
  evidence of review.
- `A2_PLAN.md` still has planning-time `TBD` and `Not started` fields. Update the
  allocation/status record based on actual work before completing the A2 form.
- `configs/design_choices.md` has only Stage 1 completed. Phase leads must fill
  Stages 2–4 as their implementations and evidence become real.
- `tests/test_ocr.py` is still a skipped placeholder. Phase 5/6 must replace it
  with meaningful tests rather than simply removing the skip.
- Never commit the full corpus, Kaggle tokens, GitHub tokens, model caches, or
  generated artifact directories.

## 10. Later phase order

After Phase 5:

1. Phase 6 — integrate/evaluate OCR, compare candidates on the fixed held-out
   labels, compute raw/normalized CER or WER, record the worst failure, and
   measure the full usable word count.
2. Phase 7 — chunk, embed, persist/load the FAISS index, and verify a real Bangla
   retrieval round trip.
3. Phase 8 — run small then full Kaggle builds and controlled ablations.
4. Phase 9 — complete `kb_demo.ipynb`, reports, design table, A2 form, pipeline
   diagram, and per-member evidence.
5. Phase 10 — clean-clone verification, merge all reviewed branches into `main`,
   run the required checks, create `a2-submit` on the verified `main` commit, and
   push `main` plus the tag.

## 11. Personal exit checklist for 2105004

Before stepping away from implementation, `2105004` should:

1. Commit and push this handover document on `fahim`.
2. Open the Phase 0–4 pull request from `fahim` into `main`, request
   `2105001`'s review, and merge without squashing after review.
3. Ask `2105001` to perform the real image-versus-text review for the first six
   held-out labels that already name `2105001` as reviewer.
4. Add an authentic `transcripts/2105004.txt` containing the required header,
   full relevant AI conversation, and personal reflection. The transcript is
   currently missing and must not be fabricated or authored by another member.
5. Ensure the A2 form eventually credits `2105004` only for work actually done
   (Phases 0–4 and their related tests/evidence) and that the transcript agrees
   with the Git history.
6. Make sure the GitHub account recognizes the commit email
   `fahimishtiak2001@gmail.com`; do not rewrite the existing commits merely to
   change the displayed author name.
7. Tell the team about the pending NCTB-edition confirmation, sample-page rights
   wording, stale manifest label status, and pending measured word count.
8. Pull the merged `main` and confirm the working tree is clean before handing
   control to the next phase lead.

Suggested handover commit:

```bash
git add HANDOVER_TO_2105001.md
git commit -m "docs(handover): transfer A2 context to 2105001"
git push origin fahim
```

## 12. Handover acceptance checklist for 2105001

- [ ] Phase 0–4 PR is reviewed and merged into `main` without squashing.
- [ ] `main` contains commit `de5f857` or its merge descendant.
- [ ] `2105001` verifies their Git identity and branches from updated `main`.
- [ ] `2105001` can run the focused Phase 4 tests.
- [ ] `2105001` reads the fixed contracts and Phase 5 exit gate.
- [ ] `2105001` genuinely checks the six historical labels assigned to them for
      independent review and records any corrections through their own commit or
      PR review.
- [ ] Phase 5 ownership and reviewer are agreed before implementation begins.
