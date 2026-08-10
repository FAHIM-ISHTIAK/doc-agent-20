# A2 Phase Plan — Bangla Morphological Analyzer

> Team coordination document. Work is deliberately divided into phases, not assigned to people. Before starting a phase, the team will record its lead and reviewer. The handbook says submitted work should use pre-named stubs, so remove this extra planning file before the `a2-submit` tag unless the instructor approves it.

## 1. A2 outcome

By the end of A2, the repository must turn the declared scanned Bangla grammar corpus into a searchable knowledge base:

```text
scanned PDFs
    -> raster page images
    -> Page objects
    -> cleaned Page objects
    -> ordered Region objects
    -> OCR Chunk objects
    -> retrieval-sized Chunk objects
    -> embedding vectors
    -> FAISS index + metadata
    -> one verified Bangla retrieval
```

The final A2 tag must include:

- the A1 artifacts carried into the repository;
- implemented ingest, preprocessing, layout, OCR, chunk, embedding, and index stages;
- a reproducible index-building command;
- an executed `notebooks/kb_demo.ipynb` containing OCR quality and a real retrieval;
- exact index statistics and an honest failure case;
- the pipeline diagram and Stages 1–4 design record;
- the filled A2 form;
- one individual AI transcript per member;
- meaningful commits authored by all three members;
- the public GitHub tag `a2-submit`.

No metric goes into the A2 form until it appears in committed Kaggle notebook output.

## 2. Fixed project choices from A1

These must not change in A2:

- **Project:** Bangla Morphological Analyzer (BMA).
- **Domain:** Bangla grammar and morphology for secondary-level teachers and students.
- **Data speciality:** Bangla script, particularly conjuncts, matras, hasanta, reph, Bengali digits, and grammar notation.
- **Primary NFR:** explainable.
- **Headline answer target:** answer-F1 >= 0.70 on the verifiable task subset.
- **Explainability targets for the completed system:** citation coverage 100%, rule attribution >= 0.90, hop-trail completeness 100%, and explanation faithfulness >= 0.85. Most of these are proved in A3 rather than A2.
- **Corpus:** the 565-page 1942 *Bhasha-prakash Bangala Byakaran* and the approximately 170-page NCTB grammar book.
- **Rights:** link-only. Do not commit or publicly redistribute the full source PDFs/page corpus.
- **Split:** 1942 volume as train, NCTB volume as test, with a whole-chapter validation block from the train volume. Record the limitation of having only two documents.
- **Chunking intent:** preserve a grammar rule or definition together with its examples, while retaining a fixed-size overlapping baseline for comparison.

## 3. Current starting point

The repository is still close to the starter state:

- the Git history contains only `A1 start`;
- `configs/task.yaml` still contains the starter `G00` project;
- the configuration uses English/default model choices and an unrelated NFR;
- A1 provenance, manifest, data-fetch script, labels, and EDA notebook are placeholders;
- the full corpus and held-out pages are absent;
- the A2 implementation functions raise `NotImplementedError`;
- A2 tests are skipped;
- both repository notebooks are nearly blank;
- `pytest` is not installed in the current local environment;
- `requirements.lock` is empty while `make setup` expects a frozen environment;
- `scripts/build_index.sh` currently risks running the complete build twice.

Therefore, the first phases recover A1 truth and establish a reproducible Kaggle environment before model development.

## 4. Kaggle-first execution model

### What stays in GitHub

GitHub is the source of truth for:

- all Python and shell source files;
- YAML configuration;
- tests;
- the two required notebooks;
- the permitted held-out sample pages and labels;
- reports, form, and transcripts.

Every permanent code change must be made or copied back into the repository and committed by the member who did the work. Code that exists only in a Kaggle cell or a generated `ocr_helper.py` is not submitted code.

### What runs in Kaggle

Use Kaggle for:

- corpus rasterization and EDA;
- GPU OCR and OCR comparisons;
- full-corpus preprocessing;
- embedding generation;
- FAISS index building;
- CER/WER calculation;
- retrieval demonstrations;
- final top-to-bottom execution of `eda.ipynb` and `kb_demo.ipynb`.

### Recommended Kaggle directory layout

```text
/kaggle/input/bma-corpus/             # attached private dataset; read-only
    bhasha_prakash_1942.pdf
    nctb_bangla_grammar.pdf

/kaggle/working/doc-agent-starter/    # cloned Git repository; writable
/kaggle/working/data/                 # rendered/processed pages; temporary
/kaggle/working/artifacts/            # index, metadata, metrics; exportable output
```

The actual corpus path must be configurable. Do not hard-code a personal Kaggle dataset slug throughout the source.

### Getting the corpus into Kaggle

Preferred method:

1. Create a **private** Kaggle dataset containing the two link-only source PDFs.
2. Attach it to the notebook as input.
3. Never make that dataset public.
4. Keep `scripts/get_data.sh` capable of recreating/fetching the corpus for the grader where licensing permits.

Alternative: enable Kaggle internet and execute the fetch script. Do not depend exclusively on this because Kaggle internet may be disabled in a submitted notebook or model download may fail.

### Starting a Kaggle session

At the beginning of a session:

```bash
!git clone https://github.com/<account>/doc-agent-<team-id>.git
%cd /kaggle/working/doc-agent-<team-id>
```

For later sessions, clone the repository again or pull the exact branch/commit being tested. Record the tested commit hash in notebook output:

```bash
!git rev-parse HEAD
```

### Kaggle dependency rules

- Pin every installed package version in the repository dependency files.
- A notebook installation cell may install those pinned dependencies, but it must not be the only dependency record.
- Record Python, CUDA, GPU, PyTorch, OCR model, embedding model, and FAISS versions.
- Set deterministic seeds before processing.
- Start with one GPU process. Add multi-GPU multiprocessing only after the single-GPU pipeline is correct and measured.
- If internet/model downloads are unavailable, attach model caches as private Kaggle datasets and document their checkpoint identifiers.

### Saving results from Kaggle

Kaggle sessions are temporary. At the end of each evidence run:

1. save a Kaggle notebook version with outputs;
2. download/export the executed `.ipynb`;
3. replace the corresponding repository stub;
4. export required small metrics/index metadata from `/kaggle/working/artifacts/`;
5. do not commit the full corpus, model cache, or oversized temporary images;
6. commit the notebook and source changes under the identity of the person who performed the work.

## 5. Phase allocation board

Fill this table as a team before beginning implementation. No owner is pre-assigned.

| Phase | Lead | Reviewer | Branch | Status |
|---|---|---|---|---|
| 0 — Team Git and allocation | TBD | TBD | TBD | Not started |
| 1 — A1 recovery and corpus contract | TBD | TBD | TBD | Not started |
| 2 — Kaggle environment and reproducibility | TBD | TBD | TBD | Not started |
| 3 — Held-out pages and ground truth | TBD | TBD | TBD | Not started |
| 4 — Ingest and preprocessing | TBD | TBD | TBD | Not started |
| 5 — Layout and reading order | TBD | TBD | TBD | Not started |
| 6 — Bangla OCR and evaluation | TBD | TBD | TBD | Not started |
| 7 — Chunk, embed, and index | TBD | TBD | TBD | Not started |
| 8 — Full Kaggle build and experiments | TBD | TBD | TBD | Not started |
| 9 — Evidence and A2 artifacts | TBD | TBD | TBD | Not started |
| 10 — Verification and submission | TBD | TBD | TBD | Not started |

Allocation rules:

- A phase may have one lead and one reviewer; large phases can be split into explicit subphases.
- Every member should own at least one code-and-test work package, not documentation alone.
- Every member should also own at least one evidence or design artifact connected to their code.
- Each member commits only work they actually performed, using their own Git identity.
- Record the allocation in the A2 form's `Worked sections` only after the work is actually completed.
- Do not squash all branches into one person's single commit; preserve the original authorship.

## 6. Dependency-ordered phase plan

### Phase 0 — Team Git, environment decisions, and allocation

**Owner:** TBD  
**Can start:** immediately

Tasks:

1. Confirm the official team ID, public repository URL, and deadline.
2. Confirm all three members are GitHub collaborators.
3. Each member checks their Git name/email before committing.
4. Agree on branch names and the pull-request/review process.
5. Fill the phase allocation board.
6. Decide how the private corpus and any model caches will be attached to Kaggle.
7. Resolve the starter's dependency-lock inconsistency and document the approved procedure.
8. Create the first Kaggle notebook session and verify repository cloning/imports.

Exit gate:

- all three members can push under their own identity;
- Kaggle can import `doc_agent` from the cloned repository;
- the team has assigned only the next few phases, with later phases allowed to remain TBD.

Possible commits:

```text
chore(config): establish reproducible project environment
docs(workflow): document Kaggle execution paths
```

### Phase 1 — Recover A1 truth and define the corpus contract

**Owner:** TBD  
**Depends on:** Phase 0

Files:

```text
configs/task.yaml
configs/config.yaml
scripts/get_data.sh
data/provenance.md
grading_kit/manifest.yaml
notebooks/eda.ipynb
```

Tasks:

1. Replace all starter project values with the submitted BMA choices.
2. Implement a reproducible two-book fetch/preparation script.
3. Rasterize every PDF page as an image; do not use embedded PDF text as the system OCR result.
4. Create stable document IDs and page IDs, including PDF-page and printed-page mapping.
5. Record exact source URLs, rights, hashes, page counts, disk sizes, exclusions, and document splits.
6. Run EDA in Kaggle and save output showing page counts, scan quality, fonts, script difficulty, and real example pages.
7. Replace projected A1 word counts with measured usable counts once OCR exists; clearly mark interim values until then.

Exit gate:

- Kaggle can access/rasterize both books;
- `task.yaml` and the manifest agree with A1;
- no A1 placeholder remains in the phase's files;
- document/page IDs remain stable across reruns.

Possible commits:

```text
chore(a1): declare BMA task and grading manifest
feat(data): add reproducible two-book corpus preparation
docs(data): record corpus provenance hashes and split
notebook(eda): analyze Bangla grammar corpus in Kaggle
```

### Phase 2 — Establish the reproducible Kaggle runtime

**Owner:** TBD  
**Depends on:** Phase 0; may run alongside Phase 1

Tasks:

1. Make paths configurable for `/kaggle/input` and `/kaggle/working`.
2. Add a notebook setup section that prints the repository commit hash and environment versions.
3. Install only declared/pinned dependencies.
4. Set random seeds.
5. Verify CPU and GPU detection.
6. Verify that generated artifacts are written to the writable working directory rather than `/kaggle/input`.
7. Define a small-mode configuration for 10–20 pages and a full-mode configuration for the complete corpus.

Exit gate:

- a fresh Kaggle session can clone the repository, install dependencies, import it, find the private inputs, and write a small artifact;
- no personal absolute path is required.

Possible commits:

```text
build: pin Kaggle OCR and indexing dependencies
feat(config): support Kaggle input and artifact paths
test(config): verify portable data path resolution
```

### Phase 3 — Create held-out pages and ground-truth labels

**Owner:** TBD  
**Depends on:** Phase 1

Files:

```text
grading_kit/heldout_pages/
grading_kit/labels.jsonl
```

Tasks:

1. Select approximately 12–20 representative held-out pages.
2. Include clean text, conjunct-heavy rules, old letterpress, numbered rule lists, exercises, and at least one poor scan.
3. Split manual transcription across the group and record who checked each page.
4. Transcribe the printed text exactly; do not copy the OCR output as ground truth.
5. Validate JSONL formatting and page-ID correspondence.
6. Keep these pages out of OCR training/fine-tuning and final parameter selection.

Exit gate:

- every label maps to a committed permitted page sample;
- a second person has reviewed each transcription;
- the metric code can read the labels without manual correction.

Possible commits:

```text
data(eval): add held-out Bangla rule pages
data(eval): add reviewed ground-truth transcriptions
test(data): validate held-out labels and page IDs
```

### Phase 4 — Implement page ingest and classical preprocessing

**Owner:** TBD  
**Depends on:** Phases 1–2

Files:

```text
src/doc_agent/ingest/loader.py
src/doc_agent/ingest/preprocess.py
tests/test_ingest.py
```

Data flow:

```text
page-image files -> loader.load_pages() -> list[Page]
list[Page] -> preprocess.run() -> cleaned list[Page]
```

Tasks:

1. Load supported page images in deterministic order.
2. Assign stable `Page.id`, `doc_id`, and `image_path` values.
3. Exclude blank/non-content pages according to the documented policy.
4. Implement conservative deskew, denoise, and binarization.
5. Preserve originals and write derived files only to the Kaggle working directory.
6. Compare preprocessing off/on on a small page sample.
7. Replace skipped ingest tests with real tests.

Exit gate:

- the same inputs produce the same ordered `Page` objects;
- preprocessing does not destroy matras/conjunct strokes on the checked sample;
- small-mode execution works in Kaggle;
- ingest tests pass.

Possible commits:

```text
feat(ingest): load raster pages with stable identifiers
feat(preprocess): add deterministic scan cleanup
test(ingest): cover filtering ordering and page IDs
```

### Phase 5 — Implement layout detection and reading order

**Owner:** TBD  
**Depends on:** Phase 4

Files:

```text
src/doc_agent/vision/layout.py
tests/test_ocr.py or the appropriate existing A2 test home
```

Data flow:

```text
clean list[Page] -> layout.detect() -> ordered list[Region]
```

Tasks:

1. Begin with the simplest corpus-appropriate baseline.
2. Identify text, headings, numbered rules, exercises, tables/figures where present.
3. Preserve reading order for short `সূত্র-N` lines and `X + Y = Z` examples.
4. Avoid a global y/x ordering rule that can mix columns.
5. Visualize region boxes on several real pages in Kaggle.
6. Test that every region retains the correct page ID and valid bounding box.

Exit gate:

- visual samples show correct region coverage and reading order;
- layout output conforms to the fixed `Region` contract;
- the next OCR stage can crop every region without special-case notebook code.

Possible commits:

```text
feat(layout): detect Bangla grammar page regions
feat(layout): preserve numbered-rule reading order
test(layout): validate region bounds and page linkage
```

### Phase 6 — Reproduce, compare, and adapt Bangla OCR

**Owner:** TBD  
**Depends on:** Phases 3 and 5

Files:

```text
src/doc_agent/vision/ocr.py
tests/test_ocr.py
configs/config.yaml
notebooks/kb_demo.ipynb  # OCR section
```

Data flow:

```text
ordered list[Region] -> OCR -> raw Bangla text -> conservative normalization -> list[Chunk]
```

Tasks:

1. Adapt the supplied EasyOCR Bangla experiment into the repository `Reader` and `transcribe()` interfaces.
2. Reproduce at least one published/pretrained method; compare at least two methods/configurations on identical held-out pages.
3. Do not use the PDF native text layer as the system output.
4. Use NFC, not the supplied notebook's NFKC, unless a measured and documented reason proves otherwise.
5. Preserve stable chunk IDs and page/document linkage.
6. Keep raw and normalized metrics separate.
7. Compute CER/WER or F1 and sample size in Kaggle.
8. Record errors involving conjuncts, matras, hasanta, reph, digits, punctuation, and rule symbols.
9. Add a VLM fallback only if its measured gain justifies runtime and dependency cost.
10. Replace skipped OCR tests.

Exit gate:

- the OCR stage returns valid `Chunk` objects from real regions;
- raw and normalized OCR metrics are reproducible from held-out labels;
- the selected reader has a measured justification;
- the worst failure is saved for Section 5.

Possible commits:

```text
feat(ocr): integrate pretrained Bangla OCR baseline
feat(ocr): add conservative NFC normalization
test(ocr): cover Unicode and region transcription
notebook(a2): measure raw and normalized OCR error
```

### Phase 7 — Implement chunking, embeddings, and vector index

**Owner:** TBD  
**Depends on:** Phase 2; develop with artificial chunks while Phase 6 runs, then integrate real OCR

Files:

```text
src/doc_agent/index/chunk.py
src/doc_agent/index/embed.py
src/doc_agent/index/store.py
scripts/build_index.sh
tests/test_retrieval.py
configs/config.yaml
notebooks/kb_demo.ipynb  # index/retrieval section
```

Data flow:

```text
OCR list[Chunk]
    -> fixed or rule-aware list[Chunk]
    -> embedding matrix
    -> FAISS index + persisted chunk metadata
```

Tasks:

1. Implement a fixed-size overlapping chunk baseline, initially around 256 tokens with 32-token overlap.
2. Preserve stable IDs, `doc_id`, and all source `page_ids`.
3. Add rule-plus-example boundaries with fallback to the fixed baseline.
4. Compare rule-aware chunks with the fixed baseline on the same queries.
5. Compare the A1 BGE-M3-class candidate with one lighter multilingual embedding candidate.
6. Record checkpoint, dimension, normalization, batch size, device, and similarity metric.
7. Begin with normalized embeddings and FAISS FlatIP for the small corpus.
8. Persist enough metadata to reconstruct returned `Chunk` objects after reloading the index.
9. Fix `scripts/build_index.sh` so it builds once.
10. Replace skipped index/retrieval tests.

Exit gate:

- `build -> restart/load -> query -> Chunk` works;
- Bengali text and provenance survive the round trip;
- one vector exists for every indexed chunk;
- a real verified Bangla query returns the correct page/chunk;
- index tests pass.

Possible commits:

```text
feat(index): add fixed overlapping chunk baseline
feat(index): preserve Bangla rule and example units
feat(embed): encode chunks with multilingual model
feat(index): persist and load FAISS metadata
fix(scripts): build the knowledge base once
test(index): verify round-trip search and page linkage
```

### Phase 8 — Run the full Kaggle pipeline and controlled experiments

**Owner:** TBD  
**Depends on:** Phases 4–7

Run small mode first, then full mode.

Required comparisons:

1. preprocessing off vs. on;
2. OCR candidate A vs. candidate B;
3. raw OCR vs. conservative normalization;
4. fixed chunks vs. rule-aware chunks;
5. embedding candidate A vs. candidate B.

For each comparison, keep the held-out pages/queries fixed and record:

- quality metric;
- sample size;
- runtime;
- device/GPU;
- peak memory if available;
- failure examples;
- selected option and reason.

Then run the selected full pipeline over both books and record:

- raw and usable pages;
- raw and usable words;
- excluded pages;
- chunks indexed;
- embedding dimension;
- index type and size;
- build time;
- corpus coverage;
- successful retrieval;
- worst OCR/retrieval failure.

Exit gate:

- the full build finishes in Kaggle without manual cell intervention;
- selected choices are backed by measurements;
- metrics and index artifacts are saved from `/kaggle/working`;
- the exact Git commit and environment are printed in the run.

Possible commits:

```text
experiment(a2): compare OCR preprocessing configurations
experiment(a2): compare chunk and embedding strategies
docs(metrics): record full knowledge-base build statistics
```

### Phase 9 — Produce the A2 evidence and documentation

**Owner:** TBD; sub-artifacts may have different leads  
**Depends on:** Phase 8

Required artifacts:

```text
notebooks/kb_demo.ipynb
reports/pipeline_diagram.md
configs/design_choices.md
forms/A2_form.docx
transcripts/<student number>.txt x3
```

Tasks:

1. Save and download the executed Kaggle `kb_demo.ipynb` with outputs.
2. Ensure the notebook runs top-to-bottom and shows:

   - environment/commit information;
   - OCR metric and sample size;
   - raw vs. normalized result;
   - index statistics;
   - query, ranked result, score, document/page/chunk;
   - manual correctness judgment;
   - worst failure.

3. Diagram the real pipeline and fixed contracts.
4. Fill the eight design facets for Stages 1–4, including fit, cost, and what would change each choice.
5. Fill the A2 form from measured outputs.
6. Copy A1 choices and answer-F1 target exactly.
7. Write the A3 plan: retrieval/reranking, agent loop/tools, grounding, evidence-gated re-search, abstention at `k_max`, explainability metrics, and domain task suite.
8. Each member commits their own complete transcript with header, unedited conversation, and reflection.

Exit gate:

- every form claim can be traced to code, configuration, Kaggle notebook output, or labelled evidence;
- `Worked sections` matches actual commits/transcripts;
- no projected or invented number appears as a result.

Possible commits:

```text
notebook(a2): add reproducible OCR and retrieval evidence
docs(a2): document knowledge-base pipeline and choices
form(a2): complete measured A2 results
docs(transcript): add individual A2 work record
```

### Phase 10 — Clean verification and submission

**Owner:** TBD  
**Depends on:** Phase 9

Verification checklist:

1. Start a fresh Kaggle session from the final candidate commit.
2. Attach the private corpus input.
3. Install pinned dependencies.
4. Run the required notebooks top-to-bottom.
5. Run the test, lint, format, and type-check commands in Kaggle.
6. Remove all A2 placeholder skips.
7. Confirm fixed contracts, pipeline order, hook seams, and tool names were not changed.
8. Confirm the full corpus, secrets, Kaggle credentials, model caches, and temporary files are not tracked.
9. Confirm all form numbers match the final executed notebook.
10. Inspect authorship using `git shortlog -sne --all` and the commit graph.
11. Confirm three transcripts and the filled form exist.
12. Remove this planning file unless extra files are approved.

Submission commands:

```bash
git add -A
git commit -m "A2 submission"
git tag a2-submit
git push origin main --tags
```

Exit gate:

- the public `a2-submit` tag points to the verified commit and is visible on GitHub before the deadline.

## 7. Parallel work without breaking phase order

The data flow is sequential, but implementation does not need to be completely sequential:

```text
Phase 1 corpus ──> Phase 4 ingest ──> Phase 5 layout ──> Phase 6 real OCR ──┐
                                                                           ├─> Phase 8 full build
Phase 2 Kaggle ─────────────────────────────────────────────────────────────┤
Phase 3 labels ────────────────────────────────> Phase 6 metrics ───────────┤
Phase 7 index can start with artificial Chunk objects ─────────────────────┘
```

Safe parallelization:

- Phase 2 can run while Phase 1 prepares the corpus.
- Phase 3 can begin as soon as stable page IDs exist.
- Phase 7 can be implemented/tested using manually constructed `Chunk` objects before OCR is ready.
- Documentation structure can be drafted early, but all result cells stay blank until Phase 8.

Hard dependencies:

- real OCR evidence requires real regions and reviewed labels;
- the final real index requires selected OCR output;
- the full notebook evidence requires the final index;
- the form must be completed after notebook results, not before.

## 8. Core versus optional work

Finish these first:

1. reproducible corpus preparation;
2. stable ingest;
3. baseline preprocessing;
4. layout and reading order;
5. measured pretrained Bangla OCR;
6. fixed overlapping chunks;
7. multilingual embeddings;
8. exact FAISS index;
9. OCR metric and one correct retrieval.

Only then consider:

- rule-aware/semantic chunking improvement;
- VLM OCR fallback;
- generative scan enhancement;
- HNSW/IVF index;
- hybrid retrieval and reranking;
- agent, multi-hop behavior, HITL, or RL/RLVR.

Hybrid retrieval, reranking, the agent loop, evidence-gated re-search, grounding, and most explainability evaluation belong primarily to A3. Do not let them prevent completion of A2.

## 9. Commit and contribution policy

Because evaluation uses Git history:

- decide the phase lead before work begins;
- use a separate feature branch for each phase or bounded subphase;
- make small commits for independently reviewable results;
- include code, tests, and evidence rather than commits containing only prose;
- the person who performed the Kaggle experiment commits the resulting notebook/evidence;
- never use one shared Git identity;
- preserve individual commits when merging;
- do not create artificial empty commits;
- do not rewrite or squash away authorship near the deadline;
- each member commits their own transcript.

A good allocation should leave each member with:

- at least one implementation commit;
- at least one test or experiment commit;
- at least one evidence/design/form contribution;
- a transcript consistent with those commits.

## 10. Definition of done by A2 form section

| A2 section | Must exist before writing it |
|---|---|
| 1 — A1 recap | Exact match with A1 project, axes, corpus, and answer-F1 target |
| 2 — Structure | Corpus-specific visual/text structure and invariances |
| 3 — Options | Real comparisons for each stage and at least one reproduced pretrained method |
| 4 — Built KB | Exact checkpoints, parameters, and an end-to-end run |
| 5 — Evidence | OCR metric/sample size, index statistics/coverage, correct retrieval, worst failure |
| 6 — A3 plan | Retrieval/rerank, agent/tools, grounding, re-search, abstention, task suite |
| 7 — Design | Eight facets for Stages 1–4 with fit, cost, and change condition |
| 8 — AI work | Three correctly named transcripts matching actual work and commits |

## 11. Important cautions

- The form contains stale ZIP wording. The handbook and repository instructions specify submission through the public `a2-submit` Git tag, not a ZIP.
- Keep the filled form at `forms/A2_form.docx`.
- Do not modify `contracts.py`, fixed pipeline order, hook seams, or fixed tool names to fit Kaggle notebook code.
- The supplied OCR notebook is an experiment only. It processes unrelated books, optionally trusts native PDF text, discards metadata/confidence, uses NFKC, and provides no CER/WER evidence. Adapt ideas into the repository modules rather than copying it unchanged.
- Do not make the private link-only corpus or private Kaggle dataset public.
- Never store Kaggle API tokens, GitHub tokens, or secrets in notebook cells or commits.
- Do not write artifacts under `/kaggle/input`; that directory is read-only.
- Do not report A1's projected word count as an A2 measurement.
- Do not silently repair uncertain Bangla OCR into clean-looking but false grammar rules.
- Do not let Kaggle's temporary files become the only copy of code or evidence.

## 12. First team session

Complete these in order:

1. confirm team ID and deadline;
2. confirm all collaborators and Git identities;
3. fill the phase allocation board for Phases 0–3 only;
4. create/attach the private Kaggle corpus dataset;
5. clone the repository in Kaggle and print the commit hash/environment;
6. resolve dependency pinning and verify imports;
7. transfer A1 settings into `task.yaml` and the manifest;
8. rasterize a small representative page batch;
9. choose held-out pages and divide manual transcription;
10. open the first small pull requests so all contributions begin under the correct accounts.
