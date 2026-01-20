import pdfplumber
import re


def normalize(text):
    return re.sub(r"\s+", " ", text.strip()) if text else ""


ROW_PATTERN = re.compile(
    r"""
    ^(ZR|ZT)\s+
    (\d+\s*-\s*\d+(?:\.\d+)?)      # model + pressure (10 / 10.4)
    (?:\s*\(\d+\))?\s+
    ([\d.]+)\s+                   # l/s
    ([\d.]+)\s+                   # m3/min
    (\d+)\s+                      # cfm
    (\d+)\s+                      # kW
    (\d+)\s+                      # hp
    (\d+)\s+                      # dBA
    (\d+)\s+                      # std kg
    (\d+)                          # std lb
    (?:\s+(\d+)\s+(\d+))?          # ff kg/lb
    $
    """,
    re.VERBOSE
)


def extract_technical_specifications(pdf_path):
    specs = {}
    current_section = None
    current_freq = None
    pending_header = False

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    for raw_line in text.split("\n"):
        line = normalize(raw_line)

        # -------- STEP 1: Detect main header --------
        if line.upper() == "TECHNICAL SPECIFICATIONS":
            pending_header = True
            continue

        # -------- STEP 2: Detect model line --------
        if pending_header and re.match(r"(ZR|ZT)\s+\d+\s*-\s*\d+.*\(FF\)", line):
            current_section = f"TECHNICAL SPECIFICATIONS {line}"
            specs[current_section] = {}
            pending_header = False
            current_freq = None
            continue

        pending_header = False if line else pending_header

        if not current_section:
            continue

        # -------- FREQUENCY BLOCKS --------
        if line.startswith("50 Hz"):
            specs[current_section]["50Hz"] = []
            current_freq = "50Hz"
            continue

        if line.startswith("60 Hz"):
            specs[current_section]["60Hz"] = []
            current_freq = "60Hz"
            continue

        if not current_freq:
            continue

        # -------- DATA ROWS --------
        match = ROW_PATTERN.match(line)
        if not match:
            continue

        (
            model_type,
            model_pressure,
            lps,
            m3min,
            cfm,
            kw,
            hp,
            dba,
            std_kg,
            std_lb,
            ff_kg,
            ff_lb
        ) = match.groups()

        specs[current_section][current_freq].append({
            "model_type": model_type,
            "model_pressure": model_pressure.replace(" ", ""),
            "free_air_delivery": {
                "l_s": float(lps),
                "m3_min": float(m3min),
                "cfm": int(cfm)
            },
            "installed_motor": {
                "kW": int(kw),
                "hp": int(hp)
            },
            "noise_level_dBA": int(dba),
            "weight": {
                "standard": {
                    "kg": int(std_kg),
                    "lb": int(std_lb)
                },
                "full_feature": {
                    "kg": int(ff_kg) if ff_kg else None,
                    "lb": int(ff_lb) if ff_lb else None
                }
            }
        })

    return specs
