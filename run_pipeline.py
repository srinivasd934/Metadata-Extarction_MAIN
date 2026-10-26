from pathlib import Path
import pandas as pd
from app.config import TRAIN_DIR, TEST_DIR, TRAIN_CSV, OUTPUT_DIR, SCHEMA_FIELDS
from app.document_loader import extract_text
from app.extractor import extract_metadata
from app.evaluator import evaluate

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

target_dir = TRAIN_DIR
files = sorted([f for f in target_dir.iterdir() if f.is_file()])
print(f"Found {len(files)} documents in {target_dir.name}/")

records = []
for idx, file_path in enumerate(files, 1):
    print(f"\n[{idx}/{len(files)}] Processing: {file_path.name}")
    extracted = {field: None for field in SCHEMA_FIELDS}
    extracted["File Name"] = file_path.name
    
    try:
        text = extract_text(file_path)
        if not text or not text.strip():
            print("  Warning: Extracted text is empty!")
        else:
            print("  Extracting metadata via Ollama...")
            result = extract_metadata(text)
            if isinstance(result, dict):
                extracted.update(result)
        print("  Extracted:", extracted)
    except Exception as e:
        print(f"  Error processing {file_path.name}: {e} (recording nulls)")

    records.append(extracted)

predictions_df = pd.DataFrame(records)
output_path = OUTPUT_DIR / "predictions.csv"
predictions_df.to_csv(output_path, index=False)
print(f"\nAll predictions saved to: {output_path}")

if target_dir == TRAIN_DIR and TRAIN_CSV.exists():
    print("\nRunning Evaluation against Ground Truth (train.csv)...")
    train_df = pd.read_csv(TRAIN_CSV)
    
    # FIX: Rename the misspelled columns in the ground truth to match SCHEMA_FIELDS
    train_df = train_df.rename(columns={
        "Aggrement Value": "Agreement Value",
        "Aggrement Start Date": "Agreement Start Date",
        "Aggrement End Date": "Agreement End Date"
    })
    
    try:
        # evaluate() returns a tuple (evaluation_summary_df, merged_df)
        eval_summary, merged_df = evaluate(train_df, predictions_df)
        print("\nEvaluation Results:")
        print(eval_summary.to_string(index=False))
    except Exception as e:
        print(f"Evaluation failed: {e}")
