# Automated Lease Document Information Extractor

## 1. Executive Summary
This repository implements an automated pipeline designed to capture key contractual attributes from unstructured lease agreements by combining Optical Character Recognition (OCR), Large Language Model (LLM) inference, and deterministic verification logic.

The framework targets six core contractual attributes:
- **Agreement Value**
- **Agreement Start Date**
- **Agreement End Date**
- **Renewal Notice (Days)**
- **Party One**
- **Party Two**

Generated outputs are benchmarked against annotated reference records using strict exact-match recall.

---

## 2. System Workflow
The extraction engine operates through a multi-stage sequential architecture:

    Unstructured Lease Files
               ↓
    Text Digitization (OCR / Parsing)
               ↓
    Text Sanitization & Formatting
               ↓
    LLM-Driven Attribute Capture
               ↓
    Deterministic Standardization
               ↓
    Constraint Verification
               ↓
    Curated Contract Metadata
               ↓
    Benchmarking & Scoring

### Stage 1: Text Digitization (OCR / Parsing)
Raw lease files are digitized into machine-readable text via OCR. Because scanned contracts vary in clarity, the digitized text can exhibit artifacts including:
- garbled or misread symbols
- merged words and missing whitespace
- corrupted numerical digits
- misspelled proper nouns
- broken layout alignment

The pipeline operates strictly on the text recovered from the source file without fabricating or importing external context.

### Stage 2: Text Sanitization & Formatting
Before prompting the language model, the raw character stream is stripped of noise and structurally tidied so the model can parse clauses more reliably.

### Stage 3: LLM-Driven Attribute Capture
The sanitized contract text is passed to the language model alongside field-specific extraction instructions. The model parses the legal prose and emits a single structured JSON payload containing the six target attributes.

### Stage 4: Deterministic Standardization
Raw model outputs undergo programmatic post-processing to enforce uniform data types:
- stripping symbols/text from monthly rent to retain pure numbers
- translating notice timeframes into an integer day count
- reformatting calendar dates into `DD.MM.YYYY`
- preserving the sequence of `Party One` and `Party Two`
- stripping honorifics, lineage tags, and location text from entity names

### Stage 5: Constraint Verification
Standardized fields are checked against strict domain guardrails:
- calendar strings must adhere to `DD.MM.YYYY`
- absent or low-confidence extractions default to `null`
- expiration dates are only derived when backed by explicit start dates and duration clauses
- contracting entities retain their original contractual sequence
- impossible calendar dates found in the raw document are not arbitrarily altered

### Stage 6: Benchmarking & Scoring
Finalized outputs are scored against the reference dataset using **Exact-Match Recall**:

    Exact-Match Recall = (Total Exact Matches / Total Valid Reference Entries) × 100

Scores are computed independently for each of the six attributes.

---

## 3. Directory Layout

    metadata-extraction-main/
    │
    ├── app/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── document_loader.py
    │   ├── evaluator.py
    │   ├── extractor.py
    │   ├── text_preprocessor.py
    │   └── validation.py
    │
    ├── data/
    │   ├── train/
    │   ├── test/
    │   ├── train.csv
    │   └── test.csv
    │
    ├── outputs/
    │   ├── train_predictions.csv
    │   ├── test_predictions.csv
    │   ├── evaluation_summary.csv
    │   └── evaluation_failures.csv
    │
    ├── notebooks/
    │   └── 01_rental_metadata_extraction.ipynb
    │
    ├── tests/
    │   └── test_validation.py
    │
    ├── requirements.txt
    └── README.md

---

## 4. Primary Execution Notebook
The end-to-end execution script is housed in:
`notebooks/01_rental_metadata_extraction.ipynb`

This interactive notebook orchestrates the entire lifecycle:
1. Ingesting raw source files
2. Sanitizing digitized text streams
3. Querying the LLM for attribute extraction
4. Enforcing standardization and verification guardrails
5. Exporting structured prediction tables
6. Computing recall metrics on the training split
7. Compiling a discrepancy log for error analysis
8. Generating final predictions on the unseen test split

---

## 5. Software & Model Dependencies
The codebase is built in Python and relies on core data and HTTP libraries:
- `Python`
- `Pandas`
- `Requests`
- `tqdm`

Inference is powered locally via an **Ollama** instance with zero reliance on paid third-party cloud APIs:
- **Runtime:** Ollama
- **Active Checkpoint:** `llama3:latest`
- **Local URI:** `http://localhost:11434/api/chat`

---

## 6. Environment Configuration
Provision and activate an isolated Conda environment:

    conda create -n metadata-extraction python=3.12
    conda activate metadata-extraction

Install all required Python packages:

    pip install -r requirements.txt

Start the local Ollama server and pull the Llama 3 checkpoint:

    ollama run llama3:latest

---

## 7. Execution Guide
Launch VS Code, open the project folder, and navigate to the main notebook (`notebooks/01_rental_metadata_extraction.ipynb`). Bind the notebook kernel to your `metadata-extraction` Conda environment and execute all cells sequentially:

    Ingest source contracts
              ↓
    Sanitize OCR text
              ↓
    Run LLM inference
              ↓
    Standardize & verify fields
              ↓
    Export training predictions
              ↓
    Score against training reference data
              ↓
    Export discrepancy report
              ↓
    Run inference on test contracts
              ↓
    Export test predictions

The training split is used for quantitative scoring since verified labels exist in `data/train.csv`. The test split is processed purely for inference—predictions are exported without recall scoring so the test set remains an unbiased holdout.

---

## 8. Generated Artifacts
* **`train_predictions.csv`**: Stores extracted attributes for the training corpus, structured with the following columns:
  - `File Name`
  - `Split`
  - `Agreement Value`
  - `Agreement Start Date`
  - `Agreement End Date`
  - `Renewal Notice (Days)`
  - `Party One`
  - `Party Two`
  - `Extraction Status`
* **`test_predictions.csv`**: Stores final extracted metadata for the four holdout contracts in the test split.
* **`evaluation_summary.csv`**: Tabulates field-by-field accuracy metrics:

      Field                  Correct    Eligible    Exact-match recall (%)
      Agreement Value           7          10               70.00
      Agreement Start Date      3          10               30.00
      Agreement End Date        2          10               20.00
      Renewal Notice (Days)     5           9               55.56
      Party One                 5          10               50.00
      Party Two                 6          10               60.00

* **`evaluation_failures.csv`**: Logs every instance where a model prediction diverged from the reference label, enabling targeted debugging.

---

## 9. Field-Specific Extraction Guidelines

### Agreement Value
Captures strictly the recurring monthly lease payment. It explicitly ignores:
- refundable security deposits
- upfront advances
- property maintenance fees
- utility and electricity bills

### Agreement Start Date
Pinpoints the date the lease officially takes effect (ignoring stamp paper purchase or rent due dates) and formats it as `DD.MM.YYYY`.

### Agreement End Date
Captures the stated termination date of the contract. When an explicit calendar date is omitted, the system derives the expiration date only if a verified start date is paired with clear duration phrasing, such as:
- *valid for X months*
- *for X months from this date*
- *agreement made only for X months from this date*
- *tenure of X months*

If an explicit end date is written in the text, it takes precedence. Invalid calendar dates caused by typos in the source document are never silently overwritten.

### Renewal Notice (Days)
Captures only the advance warning period required to terminate or vacate the lease, converting time units into total days:
- *three month advance notice* → `90`
- *2 months notice* → `60`
- *60 days notice* → `60`
- *15 days advance notice* → `15`
- *one week notice* → `7`

Overall lease tenure is never confused with the termination notice period.

### Party One and Party Two
Contracting entities are assigned strictly by their order of appearance in the introductory recitals (e.g., the *"BY AND BETWEEN"* clause):
- **Initial contracting entity** → `Party One`
- **Subsequent contracting entity** → `Party Two`

Signatory witnesses and third parties mentioned in later clauses are ignored. Post-processing strips out extraneous text including:
- Honorifics (`Mr.`, `Mrs.`, `Ms.`, `Prof.`)
- Lineage indicators (`S/o`, `D/o`, `W/o`)
- Street addresses and property descriptions

---

## 10. Reference Dataset Alignment
While auditing `data/train.csv` against the raw contract files, the ground-truth rows for the final two training documents were found to be transposed:
- `54770958-Rental-Agreement`
- `54945838-Rental-Agreement`

These two rows were swapped back to their rightful document IDs in `data/train.csv` so that automated scoring compares each prediction against its true source contract. The test split (`data/test.csv`) was left untouched.

---

## 11. Benchmark Results
System accuracy is quantified via **Exact-Match Recall**, where a prediction counts as a hit only if its normalized string is identical to the reference entry. Each of the six fields is graded independently.

Current performance on the training corpus:

| Field | Correct | Eligible | Exact-Match Recall (%) |
| :--- | :---: | :---: | :---: |
| **Agreement Value** | 7 | 10 | 70.00 |
| **Agreement Start Date** | 3 | 10 | 30.00 |
| **Agreement End Date** | 2 | 10 | 20.00 |
| **Renewal Notice (Days)** | 5 | 9 | 55.56 |
| **Party One** | 5 | 10 | 50.00 |
| **Party Two** | 6 | 10 | 60.00 |

Discrepancy logs generated during evaluation guide iterative refinements to both the LLM system prompt and the regex standardization layer.

---

## 12. Operational Constraints & Challenges
Overall extraction fidelity is bounded by several real-world factors:
- clarity and resolution of scanned source images
- inconsistent layout structures across legal templates
- reasoning limits of the local language model
- character-level OCR corruption within proper names, dates, and figures
- vague or non-standard legal phrasing in regional agreements

To mitigate these risks, the architecture pairs neural LLM extraction with deterministic rule-based standardization and validation rather than trusting raw model generations alone.
