import re
import string


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    # Remove excessive punctuation
    text = text.strip()
    return text
