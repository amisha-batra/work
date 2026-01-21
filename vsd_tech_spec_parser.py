import pdfplumber
import re


def normalize(text):
    return re.sub(r"\s+", " ", text.strip())


# Matches ONE FULL DATA ROW
ROW_PATTERN = re.compile(
    r"(Minimum|Effective|Maximum)\s+"
    r"([\d.]+)\s+"                       # working pressure
    r"(\d+)\s*-\s*(\d+)\s+"              # l/s
    r"([\d.]+)\s*-\s*([\d.]+)\s+"        # m3/min
    r"(\d+)\s*-\s*(\d+)\s+"              # cfm
    r"(\d{2})\s+"                        # noise
    r"(\d{4})\s+(\d{4,5})\s+"            # std kg lb
    r"(\d{4})\s+(\d{4,5})"               # ff kg lb
)


TYPE_PATTERN = re.compile(
    r"(ZR|ZT)\s+\d+\s+VSD\s*-\s*[\d.]+\s*bar\(e\)",
    re.IGNORECASE
)


def extract_vsd_technical_specifications(pdf_path):
    result = {
        "table_present": False,
        "vsd_technical_specifications": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        text = normalize(" ".join(page.extract_text() or "" for page in pdf.pages))

    types = list(TYPE_PATTERN.finditer(text))
    if not types:
        return result

    result["table_present"] = True

    for idx, match in enumerate(types):
        type_name = normalize(match.group())
        start = match.end()
        end = types[idx + 1].start() if idx + 1 < len(types) else len(text)

        segment = text[start:end]

        stages = {}
        noise = None
        weight = None

        for row in ROW_PATTERN.finditer(segment):
            (
                stage, wp,
                lps_min, lps_max,
                m3_min, m3_max,
                cfm_min, cfm_max,
                noise_db,
                std_kg, std_lb,
                ff_kg, ff_lb
            ) = row.groups()

            stages[stage.lower()] = {
                "working_pressure_bar": float(wp),
                "free_air_delivery": {
                    "l_s": [int(lps_min), int(lps_max)],
                    "m3_min": [float(m3_min), float(m3_max)],
                    "cfm": [int(cfm_min), int(cfm_max)]
                }
            }

            noise = int(noise_db)
            weight = {
                "standard": {"kg": int(std_kg), "lb": int(std_lb)},
                "full_feature": {"kg": int(ff_kg), "lb": int(ff_lb)}
            }

        if stages:
            result["vsd_technical_specifications"].append({
                "type": type_name,
                "noise_level_dbA": noise,
                "weight": weight,
                "stages": stages
            })

    return result
