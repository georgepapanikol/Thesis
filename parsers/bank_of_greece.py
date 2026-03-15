from pathlib import Path


# -----------------------------
# Store to file
# -----------------------------
def store_to_file(texts, filename="output.txt"):
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(texts)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_text)


# -----------------------------
# Extractors
# -----------------------------
def pdfplumber_extractor(pdf_path):
    import pdfplumber
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return texts


def pymupdf_extractor(pdf_path):
    import fitz 
    import re           # regular expressions: pattern matching
    import unicodedata  # unicode operations

    def is_gibberish_line(s: str) -> bool:
        s = s.strip()
        if not s:
            return False

        # πολλά chart symbols
        if s.count("␦") >= 1:
            return True

        # γραμμές που είναι κυρίως A-Z/0-9/σύμβολα (encoded chart text)
        letters_digits = sum(ch.isalnum() for ch in s)
        ratio_alnum = letters_digits / max(len(s), 1)

        # αν είναι πολύ "αλφαριθμητικό" και έχει λίγα normal words → σκουπίδι
        if ratio_alnum > 0.75:
            # πόσα "normal words" (με πεζά ή ελληνικά)
            normal_words = re.findall(r"[A-Za-zα-ωΑ-Ω]{3,}", s)
            # πόσα all-caps chunks
            caps_chunks = re.findall(r"\b[A-Z]{6,}\b", s)

            # π.χ. DPOUJOVFE / MFGUIBOETDBMF / 8BHFPGOFXIJSFT
            if len(caps_chunks) >= 1 and len(normal_words) <= 3:
                return True

        # patterns σαν 4PVSDF("...
        if re.match(r"^[0-9A-Z]{3,}\(", s):
            return True

        return False

    texts = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text") or ""

            
            text = unicodedata.normalize("NFC", text)  # normalize unicode: Reassure consistent representation

            # remove invisible / problematic chars
            text = text.replace("\u00ad", "")   # soft hyphen           
            text = text.replace("\u200b", "")   # zero width space               
            text = text.replace("\ufeff", "")   # BOM
            text = text.replace("\xa0", " ")    # NBSP

            # remove typical artifacts
            text = text.replace("\ufffd", "")   # replacement char �
            text = text.replace("￾", "")
            text = text.replace("□", "")

            # fix hyphenation: word-\nword -> wordword
            text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

            # --- Remove gibberish/chart lines (STRONGER) ---
            cleaned_lines = []
            for line in text.splitlines():
                if is_gibberish_line(line):
                    continue
                cleaned_lines.append(line)

            text = "\n".join(cleaned_lines)

            # cleanup whitespace
            text = re.sub(r"[ \t]+\n", "\n", text)
            text = re.sub(r"[ \t]{2,}", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)

            text = text.strip()
            # -----------------------------
            # END PREPROCESSING
            # -----------------------------

            texts.append(text)

    return texts



def pdfminer_extractor(pdf_path):
    from pdfminer.high_level import extract_text
    text = extract_text(str(pdf_path)) or ""
    return [text]


def pypdf_extractor(pdf_path):
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return texts


def pypdf2_extractor(pdf_path):
    import PyPDF2
    texts = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            texts.append(page.extract_text() or "")
    return texts


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    pdf_path = Path(__file__).parent.parent / "datasets" / "GreenskillsGreece.pdf"
    OUTPUT_DIR = Path(__file__).parent / "outputs"
    OUTPUT_DIR.mkdir(exist_ok=True)

    CHOSEN_METHOD = "pymupdf"  # Options: "pdfplumber", "pymupdf", "pdfminer", "pypdf", "pypdf2"

    EXTRACTORS = {
        "pdfplumber": pdfplumber_extractor,
        "pymupdf": pymupdf_extractor,
        "pdfminer": pdfminer_extractor,
        "pypdf": pypdf_extractor,
        "pypdf2": pypdf2_extractor,
    }
    

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if CHOSEN_METHOD not in EXTRACTORS:
        raise ValueError(f"Unknown CHOSEN_METHOD: {CHOSEN_METHOD}")

    print(f"\n[INFO] PDF: {pdf_path}")
    print(f"[INFO] Using method: {CHOSEN_METHOD}\n")

    texts = EXTRACTORS[CHOSEN_METHOD](pdf_path)

    out_path = OUTPUT_DIR / f"{CHOSEN_METHOD}_clean_output.txt"
    store_to_file(texts, filename=str(out_path))

    
    full_text = "\n\n--- PAGE BREAK ---\n\n".join(texts)
    print(full_text)

    print(f"\n[OK] Saved cleaned output to: {out_path}\n")
