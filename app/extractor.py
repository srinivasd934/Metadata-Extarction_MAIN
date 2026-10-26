import json
import re
import time
import requests
from .config import OLLAMA_URL, MODEL_NAME, OLLAMA_TIMEOUT, SCHEMA_FIELDS
from .validation import normalize_metadata

PROMPT = r"""You are extracting structured metadata from ONE rental agreement.

Return ONLY a valid JSON object with these exact six keys:
{
  "Agreement Value": string or null,
  "Agreement Start Date": string or null,
  "Agreement End Date": string or null,
  "Renewal Notice (Days)": string or null,
  "Party One": string or null,
  "Party Two": string or null
}

RULES FOR EACH FIELD:
1. "Agreement Value":
   - Monthly rent amount as a plain integer string (e.g., "4000", "6500", "3000").
   - Ignore security deposits, advance amounts, and stamp duty.
   - Remove commas, decimals, or currency symbols (e.g., "6,500.00" -> "6500").

2. "Agreement Start Date":
   - Format MUST be DD.MM.YYYY (e.g., "01.05.2010", "05.12.2008").
   - Convert written dates into DD.MM.YYYY (e.g., "1st of May 2010" -> "01.05.2010", "20th April 2011" -> "20.04.2011").
   - Look for phrases like "executed on", "commencing from", "starting from", or "effective from".

3. "Agreement End Date":
   - Format MUST be DD.MM.YYYY (e.g., "20.05.2008", "30.03.2011").
   - If the agreement states a duration (e.g., "for a period of 11 months" or "12 months") starting from the Start Date, calculate the end date in DD.MM.YYYY format.

4. "Renewal Notice (Days)":
   - Number of days required for notice/termination/renewal as an integer string (e.g., "30", "60", "90", "15").
   - Convert months to days if written in months (1 month = "30", 2 months = "60", 3 months = "90").

5. "Party One" (Landlord / Lessor / Owner):
   - Extract ONLY the person's full name.
   - Do NOT include father's name (S/o, D/o, W/o), age, or address (R/o, residing at).

6. "Party Two" (Tenant / Lessee):
   - Extract ONLY the person's full name.
   - Do NOT include father's name (S/o, D/o, W/o), age, or address (R/o, residing at).

DOCUMENT TEXT:
\"\"\"
{document_text}
\"\"\"
"""


def build_prompt(document_text: str) -> str:
    # Truncate extremely long noise if needed so local model doesn't overflow context
    trimmed = document_text[:12000]
    return PROMPT.replace("{document_text}", trimmed)


def call_ollama(prompt: str, retries: int = 3) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_ctx": 8192
        }
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "{}")
        except Exception as e:
            if attempt == retries:
                raise RuntimeError(f"Ollama request failed after {retries} attempts: {e}")
            time.sleep(2 * attempt)


def clean_party_name(value):
    if not value or not isinstance(value, str):
        return None
    val = value.strip()
    # Remove everything starting from S/o, D/o, W/o, R/o, C/o, aged, residing
    val = re.split(r",?\s*\b(?:s/o|d/o|w/o|r/o|c/o|aged|residing)\b", val, flags=re.IGNORECASE)[0]
    # Remove quoted house names like "Laxmi Leela"
    val = re.sub(r"[\"\u201c\u201d'].*?[\"\u201c\u201d']", "", val)
    # Remove titles like Prof., Sri., Smt., Mrs., Dr. (keep MR.K.Kuttan intact if no space, strip otherwise)
    val = re.sub(r"\b(?:prof|sri|smt|mrs|ms|dr)\.?\s*", "", val, flags=re.IGNORECASE)
    val = re.sub(r"\bmr\.\s+", "", val, flags=re.IGNORECASE)
    val = re.sub(r"&\s*mr\.?\s*", "& ", val, flags=re.IGNORECASE)
    # Fix OCR artifacts like «
    val = val.replace("«", ".")
    val = re.sub(r"\s+", " ", val).strip(" ,.-")
    return val or None


def clean_agreement_value(value):
    if value is None:
        return None
    val = str(value).strip()
    # Handle format like 6.500.00 or 6,500.00 -> 6500
    m = re.search(r"\b(\d{1,2})[.,](\d{3})(?:[.,]\d+)?\b", val)
    if m:
        return m.group(1) + m.group(2)
    m2 = re.search(r"\b(\d{3,6})\b", val)
    if m2:
        return m2.group(1)
    return None


def extract_metadata(document_text: str) -> dict:
    prompt = build_prompt(document_text)
    response_text = call_ollama(prompt)

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            return {field: None for field in SCHEMA_FIELDS}

    data["Agreement Value"] = clean_agreement_value(data.get("Agreement Value"))
    if data.get("Party One"):
        data["Party One"] = clean_party_name(data["Party One"])
    if data.get("Party Two"):
        data["Party Two"] = clean_party_name(data["Party Two"])

    return normalize_metadata(data)
