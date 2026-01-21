import pdfplumber
import re


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()) if text else ""


def extract_technical_specifications(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    return extract_fixed_speed_table(text)


# ==========================================================
# STRICT FIXED-SPEED TABLE EXTRACTOR
# ==========================================================
def extract_fixed_speed_table(text):
    """
    Extracts ONLY tables with the following columns:

    Type | l/s | m³/min | cfm | kW | hp | dB(A) | kg | lb | kg | lb
    """

    result = {
        "frequency": {
            "50Hz": [],
            "60Hz": []
        }
    }

    current_freq = None

    # EXACT row structure (no guessing)
    row_pattern = re.compile(
        r"([A-Z]{1,3})\s+(\d+)\s*-\s*([\d.]+)\s+"  # Type
        r"([\d.]+)\s+"                            # l/s
        r"([\d.]+)\s+"                            # m3/min
        r"(\d+)\s+"                               # cfm
        r"(\d+)\s+"                               # kW
        r"(\d+)\s+"                               # hp
        r"(\d+)\s+"                               # dB(A)
        r"(\d+)\s+"                               # Std kg
        r"(\d+)\s+"                               # Std lb
        r"(\d+)\s+"                               # FF kg
        r"(\d+)"                                  # FF lb
    )

    for raw_line in text.split("\n"):
        line = normalize(raw_line)

        # -------- Frequency blocks --------
        if line == "50 Hz":
            current_freq = "50Hz"
            continue

        if line == "60 Hz":
            current_freq = "60Hz"
            continue

        if current_freq is None:
            continue

        # -------- Data row --------
        match = row_pattern.fullmatch(line)
        if not match:
            continue

        (
            series,
            model,
            pressure,
            lps,
            m3min,
            cfm,
            kw,
            hp,
            noise,
            std_kg,
            std_lb,
            ff_kg,
            ff_lb
        ) = match.groups()

        result["frequency"][current_freq].append({
            "type": f"{series} {model}-{pressure}",
            "free_air_delivery": {
                "l_s": float(lps),
                "m3_min": float(m3min),
                "cfm": int(cfm)
            },
            "installed_motor": {
                "kw": int(kw),
                "hp": int(hp)
            },
            "noise_level_dbA": int(noise),
            "weight": {
                "standard": {
                    "kg": int(std_kg),
                    "lb": int(std_lb)
                },
                "full_feature": {
                    "kg": int(ff_kg),
                    "lb": int(ff_lb)
                }
            }
        })

    return result
