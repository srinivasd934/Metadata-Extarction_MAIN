import re
from pathlib import Path
import pandas as pd
from .config import SCHEMA_FIELDS
from .document_loader import normalize_filename


def clean_filename_key(name):
    if pd.isna(name) or name is None:
        return ""
    s = str(name).strip()
    try:
        s = normalize_filename(s)
    except Exception:
        s = Path(s).stem
    while Path(s).suffix.lower() in {".docx", ".pdf", ".png", ".jpg", ".jpeg", ".txt"}:
        s = Path(s).stem
    return s.strip().casefold()


def normalize_for_match(value):
    if pd.isna(value) or value is None:
        return ""
    val = str(value).strip()
    if re.fullmatch(r"\d+\.0", val):
        val = val[:-2]
    val = re.sub(r"\s+", " ", val).casefold()
    return val.strip(" ,.\"'`\u201c\u201d\u2018\u2019")


def evaluate(train_df, predictions_df):
    train_df = train_df.rename(columns={
        "Aggrement Value": "Agreement Value",
        "Aggrement Start Date": "Agreement Start Date",
        "Aggrement End Date": "Agreement End Date",
    })

    truth_cols = ["File Name"] + SCHEMA_FIELDS
    truth = train_df[truth_cols].copy()

    pred_cols = ["File Name"] + SCHEMA_FIELDS
    pred = predictions_df[pred_cols].copy()

    truth["_join_key"] = truth["File Name"].apply(clean_filename_key)
    pred["_join_key"] = pred["File Name"].apply(clean_filename_key)

    truth = truth.rename(columns={field: f"{field}_truth" for field in SCHEMA_FIELDS})
    pred = pred.rename(columns={field: f"{field}_pred" for field in SCHEMA_FIELDS})

    merged_df = pd.merge(
        truth,
        pred.drop(columns=["File Name"]),
        on="_join_key",
        how="left",
    )

    evaluation_results = []

    for field in SCHEMA_FIELDS:
        truth_col = f"{field}_truth"
        pred_col = f"{field}_pred"

        eligible = merged_df[truth_col].notna() & (merged_df[truth_col].astype(str).str.strip() != "")

        truth_values = merged_df.loc[eligible, truth_col].apply(normalize_for_match)
        pred_values = merged_df.loc[eligible, pred_col].apply(normalize_for_match)

        correct = int((truth_values == pred_values).sum())
        eligible_count = int(eligible.sum())

        recall = (correct / eligible_count * 100) if eligible_count > 0 else 0.0

        evaluation_results.append({
            "Field": field,
            "Correct": correct,
            "Eligible": eligible_count,
            "Exact-match recall (%)": round(recall, 2),
        })

    evaluation_summary_df = pd.DataFrame(evaluation_results)
    return evaluation_summary_df, merged_df


def failure_cases(merged):
    tables = {}
    for field in SCHEMA_FIELDS:
        truth_col, pred_col = f"{field}_truth", f"{field}_pred"
        t_norm = merged[truth_col].apply(normalize_for_match)
        p_norm = merged[pred_col].apply(normalize_for_match)
        mask = merged[truth_col].notna() & (t_norm != p_norm)
        cols = ["File Name", truth_col, pred_col]
        tables[field] = merged.loc[mask, [c for c in cols if c in merged.columns]].copy()
    return tables
