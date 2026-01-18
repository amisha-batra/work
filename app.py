import streamlit as st
import tempfile
import json
import os
import re
from dimension_parser import extract_dimensions_from_pdf


def sanitize(text):
    """
    Make text safe for filenames
    """
    text = text.replace("/", "-")
    text = re.sub(r'[<>:"\\|?*]', "", text)
    return text.strip()


st.set_page_config(
    page_title="Compressor Dimension Extractor",
    layout="wide"
)

st.title("Compressor PDF → Dimensions Extractor")

uploaded_file = st.file_uploader(
    "Upload compressor specification PDF",
    type=["pdf"]
)

if uploaded_file:
    # ---------- SAVE TEMP PDF ----------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        pdf_path = tmp.name

    # ---------- EXTRACT ----------
    with st.spinner("Extracting dimensions..."):
        data = extract_dimensions_from_pdf(pdf_path)

    st.success("Extraction completed ✅")

    # ---------- DISPLAY JSON ----------
    st.subheader("📦 Extracted JSON Output")
    st.json(data)

    # ---------- BUILD FILENAME ----------
    product_family = sanitize(data.get("product_family", "UNKNOWN"))

    model_groups = list(data.get("model_groups", {}).keys())
    model_part = "_".join(f'"{sanitize(mg)}"' for mg in model_groups)

    filename = f"{product_family}_{model_part}_dimensions.json"

    # ---------- SAVE FILE ----------
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    st.success(f"JSON saved automatically at:\n`{file_path}`")

    # ---------- DOWNLOAD ----------
    st.download_button(
        "⬇ Download JSON",
        json.dumps(data, indent=2),
        file_name=filename,
        mime="application/json"
    )
