# Rental Agreement Metadata Extraction

## 1. Project Overview

This project extracts structured metadata from rental agreement documents using OCR text, an LLM, and rule-based validation.

The system extracts the following six fields:

- Agreement Value
- Agreement Start Date
- Agreement End Date
- Renewal Notice (Days)
- Party One
- Party Two

The extracted results are compared with the provided ground-truth data to measure exact-match recall.

---

## 2. Processing Pipeline

The project follows this pipeline:

```text
Rental Agreement Documents
          ↓
OCR / Text Extraction
          ↓
Clean and Prepare Text
          ↓
LLM Metadata Extraction
          ↓
Rule-Based Normalization
          ↓
Validation
          ↓
Final Metadata
          ↓
Evaluation

Step 1: OCR / Text Extraction
The rental agreement documents are converted into text using OCR.
The OCR text may contain errors such as:
- incorrect characters
- missing spaces
- incorrect numbers
- incorrect names
- formatting issues
The system works with the extracted document text and does not use outside information to correct the document.

Step 2: Clean and Prepare Text
The extracted text is cleaned and prepared before sending it to the LLM.
This makes the document text easier for the extraction model to process.
Step 3: LLM Metadata Extraction
The LLM receives the prepared rental agreement text and extracts the six required fields.
The extraction prompt provides specific rules for each field.
The LLM returns one JSON object containing the requested metadata.
Step 4: Rule-Based Normalization
The extracted values are normalized after LLM extraction.
Examples include:
- converting rent values to numeric values
- converting renewal notice periods to days
- standardizing dates to DD.MM.YYYY
- keeping Party One and Party Two in the correct order
- removing unwanted prefixes or descriptions from party names where applicable
Step 5: Validation
The extracted metadata is validated using predefined rules.
For example:
- dates follow the required DD.MM.YYYY format
- missing or unreliable values are returned as null
- agreement end dates are not calculated without reliable supporting information
- Party One and Party Two must remain in the correct order
- invalid dates present in the source are not silently corrected
Step 6: Evaluation
The predictions are compared against the provided ground-truth labels.
The evaluation uses exact-match recall:
Exact-match recall =
Correct predictions / Eligible ground-truth values × 100

The evaluation is performed separately for each metadata field.

3. Project Structure
metadata-extraction/
│
├── app/
│   ├── config.py
│   ├── extractor.py
│   ├── loader.py
│   ├── validator.py
│   └── ...
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
├── metadata_extraction.ipynb
├── requirements.txt
├── README.md
└── assignment-details.pdf

4. Main Notebook
The main implementation is provided in:
metadata_extraction.ipynb

The notebook contains the complete workflow for:
1. loading the documents
2. preparing the document text
3. extracting metadata
4. validating the extracted values
5. generating predictions
6. evaluating predictions
7. generating failure cases
8. running extraction on the test documents

5. Required Environment
The project uses Python and the following main libraries:
- Python
- Pandas
- Requests
- tqdm
The LLM is accessed through a locally running Ollama server.
The current configuration uses:
Ollama
Model: llama3:latest
Endpoint: http://localhost:11434/api/chat

No external LLM API is required.

6. Setup
Create and activate the project environment:
conda create -n metadata-extraction python=3.12
conda activate metadata-extraction

Install the required packages:
pip install -r requirements.txt

Make sure Ollama is running locally and the required model is available:
ollama run llama3:latest

7. Running the Project
Open the project in VS Code and open:
metadata_extraction.ipynb

Select the Python kernel from the metadata-extraction environment.
Then run the notebook cells from top to bottom.
The notebook will:
Load documents
   ↓
Prepare OCR text
   ↓
Extract metadata using LLM
   ↓
Normalize and validate results
   ↓
Save predictions
   ↓
Evaluate training predictions
   ↓
Generate failure report
   ↓
Extract metadata from test documents
   ↓
Save test predictions

The training documents are used for evaluation because their ground-truth metadata is available in train.csv.
The test documents are processed separately and their predictions are saved without calculating recall, since the test ground-truth values are not used for evaluation.

8. Output Files
train_predictions.csv
Contains the metadata extracted from the training documents.
The file contains:
- File Name
- Split
- Agreement Value
- Agreement Start Date
- Agreement End Date
- Renewal Notice (Days)
- Party One
- Party Two
- Extraction Status
test_predictions.csv
Contains the metadata extracted from the test documents.
The test set contains four documents. Since ground-truth labels are not used for the test set, this file contains the final extracted predictions for those documents.
evaluation_summary.csv
Contains the evaluation results for each metadata field.
Example:
Field                         Correct    Eligible    Exact-match recall
Agreement Value                  ...         ...             ...
Agreement Start Date             ...         ...             ...
Agreement End Date               ...         ...             ...
Renewal Notice (Days)            ...         ...             ...
Party One                        ...         ...             ...
Party Two                        ...         ...             ...

evaluation_failures.csv
Contains the documents where the predicted value does not exactly match the ground-truth value.
It is used to analyse extraction errors.

9. Important Extraction Rules
Agreement Value
The system extracts the monthly rental amount.
It does not use:
- security deposit
- advance
- maintenance charges
- electricity charges
Agreement Start Date
The system identifies the agreement commencement or effective date.
Payment dates are not treated as the agreement start date.
The extracted date is returned in:
DD.MM.YYYY

Agreement End Date
The system looks for an explicit expiry or end date.
It also considers agreement duration when the document provides reliable evidence such as:
- valid for X months
- for X months from this date
- agreement made only for X months from this date
- tenure of X months
An end date may be calculated when both a reliable start date and reliable duration are available.
If an explicit end date is present in the document, that date is used.
Dates from the source are not silently replaced with a different date when OCR or document data contains an invalid calendar date.
Renewal Notice
Only the notice period associated with termination, cancellation, or ending the agreement is extracted.
Examples:
three month advance notice → 90
2 months notice → 60
60 days notice → 60
15 days advance notice → 15
one week notice → 7

Agreement duration or rental period is not treated as the notice period.
Party One and Party Two
The parties are extracted according to their order in the agreement.
First contracting party  → Party One
Second contracting party → Party Two

The extraction focuses on the opening contracting-party section, such as the BY AND BETWEEN section.
Witnesses and unrelated people mentioned later in the document are not selected as contracting parties.
The party extraction rules also remove unnecessary information such as:
- Mr.
- Mrs.
- Ms.
- Prof.
- S/o
- D/o
- W/o
- addresses
- property descriptions
where applicable.

10. Ground-Truth Correction
During manual validation of the training data, the final two training records were identified as being swapped.
The records for:
54770958-Rental-Agreement
54945838-Rental-Agreement

were therefore corrected in data/train.csv so that their metadata corresponds to the correct rental agreement documents.
This correction is important because the evaluation compares predictions against the corresponding document's ground-truth values.
No changes were made to the test ground-truth because the test set is used only for final prediction.

11. Evaluation
The main evaluation metric is exact-match recall.
A prediction is counted as correct only when the normalized prediction matches the corresponding ground-truth value.
The evaluation is performed independently for all six fields.
The current training-set evaluation is:
Field                         Correct    Eligible    Exact-match recall
Agreement Value                  6          10              60.00%
Agreement Start Date             5          10              50.00%
Agreement End Date               2          10              20.00%
Renewal Notice (Days)            5           9              55.56%
Party One                        5          10              50.00%
Party Two                        5          10              50.00%

The failure report is used to identify incorrect, missing, or mismatched predictions and to improve the extraction prompt and validation rules.

12. Limitations
The extraction quality depends on:
- OCR quality
- document formatting
- LLM extraction accuracy
- OCR errors in names, dates, and numbers
- ambiguous wording in rental agreements
The system therefore combines LLM extraction with rule-based normalization and validation instead of relying only on the LLM output.
```
