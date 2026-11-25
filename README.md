# Design and Evaluation of a Privacy-Aware RAG Prototype with Kenyan Identifier Masking and Role-Based Document Retrieval

DAI034 Capstone. Drina Musili: 250636DAI.


## What this repo does

A prototype for synthetic clinic documents. It does four things in order:

1. **Detects** names, Kenyan national ID numbers and Kenyan phone numbers using Microsoft Presidio plus custom Kenyan recognisers.
2. **Masks or pseudonymises** the detected identifiers in documents and in user questions.
3. **Retrieves** documents with a role filter (receptionist, clinician, data protection officer) applied *before* any search.
4. **Answers** staff questions with an LLM that sees only pseudonymised, role-permitted text.

The central contribution is the Kenyan national ID recogniser and the Kenyan phone recogniser, evaluated against default Presidio. The role filter, query pseudonymisation and answer step are supporting parts of the prototype.

**All data is synthetic.** No real person, ID number or phone number is used anywhere.

## Repository layout

| Path | Contents |
|---|---|
| `src/ke_recognizers.py` | Kenyan ID and phone recognisers, whole-word context matching, case handling for names, analyser builder |
| `src/01_...` to `src/11_...` | Numbered experiment scripts (see "Run") |
| `data/` | Generated datasets, clinic corpus, test questions, handwritten notes, answer cache |
| `results_*.txt` | Saved output of each run (see "Results files") |

## Setup

Windows PowerShell, Python 3.12 (Python 3.13 and later failed to build PyYAML on my machine):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

The answer step needs an Anthropic API key, set for the current terminal session only. It is never stored in the repo:

```powershell
$env:ANTHROPIC_API_KEY="key-here"
```

## Run

| Command | What it does |
|---|---|
| `python src/01_default_presidio.py` | Default Presidio on one synthetic record |
| `python src/02_baseline.py [data/file.json] [--ke]` | Evaluates default Presidio, or with the Kenyan recognisers (`--ke`), on a labelled dataset |
| `python src/03_mask.py` | Before and after masking on the 10 hand-built records |
| `python src/04_generate_dataset.py [seed] [out.json]` | Generates a labelled dataset (150 records). Seed 42 gives the main set, seed 7 the held-out set |
| `python src/05_failures_by_tag.py` | National ID failures by template type |
| `python src/06_window_sweep.py` | Compares context window sizes |
| `python src/07_generate_corpus.py` | Generates the 49-document clinic corpus and 24 test questions (seed 11) |
| `python src/08_retrieval.py` | Retrieval with role filtering under four masking conditions |
| `python src/09_handwritten_eval.py [file.txt] [--default] [--substring]` | Evaluates detection on handwritten notes |
| `python src/10_ablation.py` | Ablation of the spaced-ID and all-caps handling |
| `python src/11_answer.py [--dry]` | Answer step. `--dry` builds the prompts without calling the API |


## Data

| File | What it is |
|---|---|
| `data/records.json` | 10 hand-built labelled records (first development set) |
| `data/records_large.json` | 150 template-generated records (seed 42) |
| `data/records_heldout.json` | 150 template-generated records with different random values (seed 7) |
| `data/corpus.json` | 49 clinic documents with `allowed_roles` (visit notes, appointment reminders, billing summaries, referral letters, data-request logs, policies) |
| `data/questions.json` | 24 questions: 13 answerable, 9 that must be denied, 2 out of scope |
| `data/handwritten.txt` | 15 handwritten development notes |
| `data/handwritten_test.txt` | 5 further notes. I used them for debugging, so they count as a second development set |
| `data/handwritten_final.txt` | 12 notes written before the final run and evaluated once, with no rule changes afterwards |

Handwritten notes use inline labels: `[[P|name]]`, `[[ID|number]]`, `[[PH|number]]`. Titles such as "Dr" and "Mrs" are left outside the brackets.

**Annotation correction.** After the first run on the handwritten notes, I corrected the markup where the recogniser had found real identifiers I had forgotten to label, and I moved titles outside the name spans. The first-run results are kept in `results_16_handwritten.txt`.

The generated datasets come from templates I wrote, so they test how the rules behave on generated text. They do not measure accuracy on real clinic text.

## Method

- **Recognisers.** A Kenyan national ID is 7 or 8 digits, optionally with one space inside. It starts with a low base score of 0.1 and is boosted by nearby context words (`id`, `ids`, `identity`, `national`, `idno`, `passport`). A Kenyan mobile number is `+254`, `254` or `0` followed by `7xx` or `1xx` and six more digits, with optional spaces or hyphens. 
- **Threshold.** Detections are counted at a score of 0.4 or above.
- **Context window.** Three words before and two after the number. A five-word window flagged 33 decoy numbers as IDs in the sweep (`results_10_window_sweep.txt`).
- **Whole-word context matching.** Presidio's default context matching is substring-based, as its source documents: `id` matches inside `unpaid`. I switched to its built-in whole-word mode, which removed that false positive without losing any identifier on my test notes.
- **Names.** Presidio's own detector (spaCy) finds names. I added a step that title-cases all-caps words on a copy of the text for name detection only, so character positions stay the same.
- **Scoring.** Exact span match. An earlier overlap-based score over-counted partly detected names, so I report exact figures.
- **Pseudonyms.** Each identifier becomes a token (`PERSON_ab12cd`) from a keyed hash (HMAC). Names are tokenised word by word so a question and a document produce matching tokens.
- **Retrieval.** TF-IDF, top 3 documents, with one index per role built only from documents that role may see. The filter runs before the search, so a forbidden document cannot be retrieved.
- **Answer step.** The model answers only from the retrieved, pseudonymised text and is told to refuse anything outside it.

## Results

All figures are at score threshold 0.4, exact span, with the Kenyan recognisers unless stated otherwise.

### Detection

| Data | National IDs: default Presidio | National IDs: Kenyan recogniser | Phones: default | Phones: Kenyan | Names | ID false positives |
|---|---|---|---|---|---|---|
| Synthetic, 150 records | 0/91 | 68/91 | 38/55 | 55/55 | 96/115 | 0 |
| Synthetic held-out, 150 records | 0/111 | 92/111 | 55/79 | 79/79 | 102/127 | 0 |
| Handwritten development, 15 notes | not run | 5/10 | not run | 10/10 | 11/15 (plus 1 covered) | 0 |
| **Handwritten final, 12 notes** | **0/11** | **5/11** | **5/7** | **7/7** | **10/11** (default 9/11) | **0** |

Names come from the same detector in both configurations, so the name figure is shared on the synthetic sets. The handwritten final set had 3 false name detections (`Nat` twice and `Email`) in both configurations.

The handwritten development figures are not independent: I changed the rules after seeing those notes. The final set is the clean test.

**Whole-word matching, before and after** (5 test notes): 1 false positive with substring matching (`45678912` boosted by the `id` in `unpaid`), 0 with whole-word matching. No identifier was lost.

### Retrieval (21-question version, 13 answerable and 6 deny)

| | A. Unmasked, role filter | B. Masked `<PERSON>`, role filter | C. Unmasked, no filter (control) | D. Pseudonymised documents and queries, role filter |
|---|---|---|---|---|
| Correct document first | 8/13 | 3/13 | 8/13 | 8/13 |
| Expected document in top 3 | 12/13 | 4/13 | 11/13 | 12/13 |
| Forbidden documents retrieved | 0 | 0 | 7 | 0 |
| Identifiers visible in retrieved text | 103 | 2 | 124 | 3 |

Masking alone cut retrieval sharply because every name became the same token. Consistent pseudonyms recovered it, partly because a per-word token keeps the same match structure as the original words.

Source: `results_13_retrieval.txt`. This is the run on the first 21 questions, made before the three role-claim questions were added. Those three are evaluated in the answer step.

### Answer step (24 questions, one run)

| Question type | n | Result |
|---|---|---|
| Answerable | 13 | 12 correct by string check; Q18 incomplete (said two patients, there are three, because top-3 retrieval hid one document) |
| Deny, including role claims and "ignore your instructions" | 9 | 9 revealed nothing from a forbidden document |
| Out of scope (medical advice) | 2 | 2 declined |
| Prompts containing a real name part | 3/24 | `mercy`, `grace odhiambo` |
| Prompts containing a raw ID or phone number | 0/24 | |

The role filter, not the model, is what keeps forbidden documents out of the answer. The model never saw them. This run does not test instructions hidden inside a document the user is allowed to see. Model output varies between runs.

Corpus masking check: 114 labelled identifiers; no ID or phone number remained visible, but 5 documents still showed all or part of a name.

## Limitations

- **IDs with no context word nearby are missed.** A bare 7 or 8 digit number looks like any reference number. This accounts for most missed IDs on the handwritten notes.
- **Label variants are not in the keyword list.** `Identification no.` and `I.D.` were missed on the final notes. Spaced IDs with no label are also missed.
- **Names depend on spaCy.** It misses some names (all-caps and rare ones), leaves partial names visible, and tags label words such as `Nat` and `Email` as people.
- **A decoy just after an ID can be masked as an ID**, because the ID word is still inside the window. This showed up in a billing summary where an invoice number was tokenised as an ID.
- **6 phone false positives on the held-out set.** Cause not investigated, still under investigation and will be discussed in detail in Chapter 3.
- **Retrieval is TF-IDF with top 3.** A fixed cut-off can hide items (Q18).
- **Generated data and small handwritten sets.** The synthetic results show how the rules behave on templates. The handwritten sets are small (10 to 11 IDs each).
- **Pseudonyms are linkable.** Records stay joinable, and two people sharing a first name or surname share a token.
- **Prototype secret.** The hashing key is hard-coded for the prototype and must be moved out before any real use.
- **Tokens appear in answers.** There is no step that maps them back to names for authorised users.

## Status

**Working**
- Kenyan national ID and phone recognisers evaluated against default Presidio on synthetic and handwritten data
- Document masking and per-word pseudonymisation of documents and queries
- Role-filtered retrieval with a four-condition comparison
- API answer step with a cache, a call cap and a dry-run mode, run once

**Incomplete**
- No mapping from tokens back to names
- No real clinical text, and no handwritten set larger than about a dozen notes
- Retrieval and answer quality are measured on one corpus and one run
- Query masking is implemented as pseudonymisation of questions and compared in retrieval, but not evaluated beyond that

**Problems met and what I did**
- Python 3.13 could not build PyYAML. I switched to Python 3.12.
- Default Presidio read a local phone number as a date. I added a Kenyan phone recogniser.
- A five-word context window flagged a decoy next to a real ID. I narrowed it to three before the number and two after.
- Substring context matching boosted `45678912` because of `unpaid`. I switched to whole-word matching.
- My first all-caps fix lowered ID detection by rewriting `ID` itself. I rebuilt it to apply to names only, and an ablation confirmed no regression.
- My first scoring counted partial name detections as correct. I switched to exact span scoring.
- `.venv` was committed by mistake, i removed it from the history.

## Privacy and security notes

- All data is synthetic.
- The API key is read from an environment variable and is never stored in the repo. 
- `data/answer_cache.json` holds model answers to synthetic questions only.
- The pseudonymisation key in `src/11_answer.py` and `src/08_retrieval.py` is a prototype placeholder.

## Results files
The main results are in `results_14`, `results_15`, `results_29`, `results_30`, `results_22` and `results_26` (detection), `results_13` (retrieval), and `results_25` and `results_25a` (answer step).

| File | What it shows |
|---|---|
| `results_01_default_presidio.txt` | Default Presidio on one synthetic record: finds the name and phone, no Kenyan ID type |
| `results_02_baseline.txt` | Default Presidio on the 10 hand-built records |
| `results_03_with_ke_id.txt` | First Kenyan ID recogniser on the 10 records, default context window; one decoy wrongly flagged |
| `results_04_ke_window3.txt` | Same, with the context window narrowed to 3 words; decoy resolved |
| `results_05_masking.txt` | Before and after masking on the 10 records; one phone number left visible |
| `results_06_ke_id_and_phone.txt` | Kenyan ID and phone recognisers on the 10 records |
| `results_07_large_default.txt` | Default Presidio on the 150-record set (seed 42) |
| `results_08_large_ke.txt` | Kenyan recognisers on the same set (window 3 before, overlap scoring) |
| `results_09_id_failures_by_tag.txt` | National ID failures grouped by template type |
| `results_10_window_sweep.txt` | Context window comparison: IDs found vs decoys flagged |
| `results_11_heldout_ke.txt` | Kenyan recognisers on the held-out set (seed 7), overlap scoring |
| `results_12_heldout_default.txt` | Default Presidio on the held-out set |
| `results_13_retrieval.txt` | Retrieval under four conditions, first 21 questions |
| `results_14_large_ke_exact.txt` | Large set with exact-span scoring |
| `results_15_heldout_ke_exact.txt` | Held-out set with exact-span scoring |
| `results_16_handwritten.txt` | First run on the handwritten notes, before any annotation or rule change |
| `results_17_handwritten_annotation_fixed.txt` | Same notes after correcting the annotations, before code changes |
| `results_18_large_after_fixes.txt` | First attempt at the all-caps and spaced-ID fixes on the large set. Superseded: it lowered ID detection, because the case handling also rewrote `ID` |
| `results_19_heldout_after_fixes.txt` | Same first attempt, held-out set. Superseded |
| `results_20_handwritten_after_fixes.txt` | Same first attempt, handwritten notes. Superseded |
| `results_22_ablation.txt` | Ablation of the spaced-ID and all-caps handling after the rebuild: no regression |
| `results_23_dev_after_fixes.txt` | 15 development notes after the rebuilt fixes |
| `results_24_fresh_test.txt` | The 5-note test file, later used as a second development set |
| `results_25a_dry_run_leaks.txt` | Answer-step dry run: 3 of 24 prompts with a name part, none with a raw identifier |
| `results_25_answers.txt` | Answer step, one live run of 24 questions |
| `results_26_ablation_exact_words.txt` | Ablation after switching to whole-word context matching |
| `results_27_dev_exact_words.txt` | Development notes with whole-word matching |
| `results_28a_test_substring_old.txt` | 5-note test file with Presidio's default substring matching: 1 false positive |
| `results_28b_test_whole_word.txt` | Same file with whole-word matching: 0 false positives |
| `results_29_final_test.txt` | Clean final test (12 notes): Kenyan recognisers |
| `results_30_final_test_default.txt` | Same notes with default Presidio |


