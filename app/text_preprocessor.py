import re


def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def prepare_document(text: str) -> str:
    return clean_text(text)
