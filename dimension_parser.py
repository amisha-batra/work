import pdfplumber
import re


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()) if text else ""


def extract_model_groups(first_page_text):
    groups = {}
    for line in first_page_text.split("\n"):
        if "ZR/ZT" in line and "(" in line:
            for g in re.split(r"\s*&\s*", line):
                groups[normalize(g)] = {}
    return groups


def extract_dimension_rows_from_text(text):
    """
    Extracts rows like:
    ZR 110-145 2540 1650 2000 3440 1650 2000
    """
    rows = []

    pattern = re.compile(
        r"\b(ZR|ZT)\s+(\d+\s*-\s*\d+)\s+"
        r"(\d{3,5})\s+\d+\.\d+\s+"   # A mm + inch
        r"(\d{3,5})\s+\d+\.\d+\s+"   # B mm + inch
        r"(\d{3,5})\s+\d+\.\d+\s+"   # C mm + inch
        r"(\d{3,5})\s+\d+\.\d+\s+"   # FF A mm + inch
        r"(\d{3,5})\s+\d+\.\d+\s+"   # FF B mm + inch
        r"(\d{3,5})"                # FF C mm
    )

    for match in pattern.finditer(text):
        rows.append(match.groups())

    return rows


def extract_dimensions_from_pdf(pdf_path):
    result = {
        "product_family": None,
        "model_groups": {}
    }

    with pdfplumber.open(pdf_path) as pdf:

        # -------- PAGE 1 --------
        first_page_text = pdf.pages[0].extract_text()
        result["product_family"] = normalize(first_page_text.split("\n")[0])
        result["model_groups"] = extract_model_groups(first_page_text)

        # -------- ALL PAGES --------
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

        dimension_rows = extract_dimension_rows_from_text(full_text)

        for model_type, model_range, a, b, c, fa, fb, fc in dimension_rows:
            for group in result["model_groups"]:
                result["model_groups"][group].setdefault(model_type, {})
                result["model_groups"][group][model_type].setdefault(
                    model_range.replace(" ", ""),
                    {
                        "standard": {},
                        "full_feature": {}
                    }
                )

                result["model_groups"][group][model_type][model_range.replace(" ", "")]["standard"] = {
                    "A_length_mm": int(a),
                    "B_width_mm": int(b),
                    "C_height_mm": int(c)
                }

                result["model_groups"][group][model_type][model_range.replace(" ", "")]["full_feature"] = {
                    "A_length_mm": int(fa),
                    "B_width_mm": int(fb),
                    "C_height_mm": int(fc)
                }

    return result
