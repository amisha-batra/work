import pdfplumber
import re


DOT_PATTERN = re.compile(r"[•●\.]")

def normalize_header(text):
    if not text:
        return ""
    return " ".join(text.split())


def cell_to_bool(cell):
    if not cell:
        return False
    cell = cell.strip()
    if DOT_PATTERN.search(cell):
        return True
    return False


def table_score(table):
    """
    Scores how likely a table is an Options/Availability matrix
    Higher score = more likely
    """
    if not table or len(table) < 5:
        return 0

    rows = len(table)
    cols = max(len(r) for r in table if r)

    # Options tables are large
    if rows < 10 or cols < 5:
        return 0

    score = 0

    # First column should be long descriptive text
    long_text_rows = 0
    symbol_cells = 0
    total_cells = 0

    for row in table[1:]:
        if not row or not row[0]:
            continue

        if len(row[0]) > 15:
            long_text_rows += 1

        for cell in row[1:]:
            total_cells += 1
            if not cell or DOT_PATTERN.search(cell) or cell.strip() in {"-", "–"}:
                symbol_cells += 1

    if long_text_rows / max(1, rows - 1) > 0.7:
        score += 5

    if total_cells > 0 and symbol_cells / total_cells > 0.7:
        score += 5

    return score


def extract_options_table(pdf_path):
    best_table = None
    best_score = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                score = table_score(table)
                if score > best_score:
                    best_score = score
                    best_table = table

    if not best_table:
        return {"options": {}}
        

    header = best_table[0]
    model_headers = [
    normalize_header(h) if h else f"column_{i}"
    for i, h in enumerate(header[1:], start=1)
]


    options = {}

    for row in best_table[1:]:
        if not row or not row[0]:
            continue

        option_name = row[0].strip()
        option_values = {}

        for model, cell in zip(model_headers, row[1:]):
            option_values[model] = cell_to_bool(cell)

        options[option_name] = option_values

    return {"options": options}
