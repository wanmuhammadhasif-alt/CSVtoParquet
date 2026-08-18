import os
import uuid
import zipfile
import time
import pandas as pd
import polars as pl
import streamlit as st
import shutil

from converter import convert_file, detect_encoding
from utils import format_size
from pathlib import Path
import uuid

TEMP_ROOT = Path("temp")
if "temp_root_cleared" not in st.session_state:
    if TEMP_ROOT.exists():
        shutil.rmtree(TEMP_ROOT)
    TEMP_ROOT.mkdir(exist_ok=True)
    st.session_state.temp_root_cleared = True



st.set_page_config(
    page_title="CSV ↔ Parquet Converter",
    layout="wide"
)

st.title("CSV ↔ Parquet Batch Converter")

uploaded = st.file_uploader(

    "Upload CSV / Parquet",

    type=["csv","parquet"],

    accept_multiple_files=True
)

if uploaded:

    show_csv_settings = any(file.name.lower().endswith(".csv") for file in uploaded)
    if show_csv_settings:
        with st.expander("Advance CSV Setting"):
            delimiter_choice = st.selectbox(
                "Delimiter",
                ["Auto", ",", ";", "Tab", "|"],
                index=0
            )
            encoding = st.selectbox(
                "Encoding",
                ["Auto", "utf8", "utf-8", "utf-8-sig", "latin-1", "utf16", "cp1252"],
                index=0
            )
            has_header = st.checkbox("Has Header", value=True)
            quote_char = st.text_input("Quote Character", value='"', max_chars=1)
            null_values_input = st.text_input("Null Values", value="NULL,NA,N/A")
            ignore_errors = st.checkbox("Ignore Errors", value=False)
            truncate_ragged_lines = st.checkbox("Truncate Ragged Lines", value=True, help="Automatically truncate rows with extra columns and pad rows with missing columns")
            skip_rows = st.number_input("Skip Rows", min_value=0, value=0, step=1)
    else:
        delimiter_choice = "Auto"
        encoding = "utf8"
        has_header = True
        quote_char = '"'
        null_values_input = "NULL,NA,N/A"
        ignore_errors = False
        truncate_ragged_lines = False
        skip_rows = 0

    st.write(f"Files Selected : {len(uploaded)}")

    print(uploaded)

    def build_preview_df(csv_path, selected_delimiter, selected_encoding, has_header_value, quote_char_value, null_values_input_value, ignore_errors_value, skip_rows_value):
        encoding_name = selected_encoding.strip().lower() if isinstance(selected_encoding, str) else selected_encoding
        if str(encoding_name).lower() == "auto":
            encoding_name = detect_encoding(csv_path) or "utf8"
        if encoding_name == "utf-8":
            encoding_name = "utf8"
        elif encoding_name == "utf-8-sig":
            encoding_name = "utf8-sig"

        read_kwargs = {
            "encoding": encoding_name,
            "has_header": has_header_value,
            "quote_char": quote_char_value,
            "null_values": [v.strip() for v in null_values_input_value.split(",") if v.strip()],
            "ignore_errors": ignore_errors_value,
            "skip_rows": int(skip_rows_value),
        }
        if selected_delimiter != "Auto":
            read_kwargs["separator"] = "\t" if selected_delimiter == "Tab" else selected_delimiter

        try:
            return pl.read_csv(csv_path, **read_kwargs)
        except Exception:
            fallback_encodings = ["utf8-sig", "latin1", "cp1252"]
            for fallback_encoding in fallback_encodings:
                if fallback_encoding == encoding_name:
                    continue
                read_kwargs["encoding"] = fallback_encoding
                try:
                    return pl.read_csv(csv_path, **read_kwargs)
                except Exception:
                    continue

            read_kwargs["truncate_ragged_lines"] = True
            return pl.read_csv(csv_path, **read_kwargs)

    if st.button("Convert"):

        if TEMP_ROOT.exists():
            shutil.rmtree(TEMP_ROOT)
        TEMP_ROOT.mkdir(exist_ok=True)

        session_folder = TEMP_ROOT / str(uuid.uuid4())
        session_folder.mkdir()

        upload_folder = session_folder / "upload"
        converted_folder = session_folder / "converted"

        upload_folder.mkdir()
        converted_folder.mkdir()

        st.session_state.session_folder = session_folder
        st.session_state.upload_folder = upload_folder
        st.session_state.converted_folder = converted_folder

        session_folder = st.session_state.session_folder
        upload_folder = st.session_state.upload_folder
        converted_folder = st.session_state.converted_folder

        progress = st.progress(0)

        status = st.empty()

        table = []

        total = len(uploaded)

        overall_start = time.time()

        converted_files = []
        preview_frames = []

        for i,file in enumerate(uploaded):

            status.info(
                f"Converting ({i+1}/{total}) : {file.name}"
            )

            temp = upload_folder / file.name

            temp.write_bytes(file.getbuffer())

            if file.name.lower().endswith('.csv'):
                csv_preview = build_preview_df(
                    temp,
                    delimiter_choice,
                    encoding,
                    has_header,
                    quote_char,
                    null_values_input,
                    ignore_errors,
                    skip_rows,
                )
                preview_frames.append({"filename": file.name, "path": temp, "data": csv_preview})

            selected_encoding = encoding
            if str(selected_encoding).lower() == "auto":
                detected_encoding = detect_encoding(temp)
                selected_encoding = detected_encoding or "utf8"

            csv_options = {
                "delimiter": delimiter_choice,
                "encoding": selected_encoding,
                "has_header": has_header,
                "quote_char": quote_char,
                "null_values": [v.strip() for v in null_values_input.split(",") if v.strip()],
                "ignore_errors": ignore_errors,
                "truncate_ragged_lines": truncate_ragged_lines,
                "skip_rows": int(skip_rows),
            }

            try:

                stat, output = convert_file(temp, converted_folder, csv_options=csv_options)

                converted_files.append(output)

                table.append(stat.__dict__)

            except Exception as e:

                table.append({
                    "filename": file.name,
                    "input_type": "Unknown",
                    "output_type": "Unknown",
                    "rows": 0,
                    "columns": 0,
                    "input_size": 0,
                    "output_size": 0,
                    "elapsed": 0.0,
                    "status": "Failed",
                    "error": str(e)
                })

                st.error(f"{file.name} failed: {e}")
                print(f"Conversion failed for {file.name}: {e}")

            progress.progress((i+1)/total)

        elapsed = time.time()-overall_start

        status.success("Conversion Finished")

        df = pd.DataFrame(table)

        for col, default in [
            ("input_size", 0),
            ("output_size", 0),
            ("elapsed", 0.0),
            ("input_type", "Unknown"),
            ("output_type", "Unknown"),
            ("rows", 0),
            ("columns", 0),
        ]:
            if col not in df.columns:
                df[col] = default


        df["Input Size"] = df["input_size"].apply(format_size)
        df["Output Size"] = df["output_size"].apply(format_size)
        df["Elapsed"] = df["elapsed"].round(2)

        df["ratio"] = df.apply(
            lambda row: "N/A"
            if row.get("input_size", 0) == 0 or pd.isna(row.get("output_size"))
            else f"{((row['output_size'] - row['input_size']) / row['input_size'] * 100):.2f}%",
            axis=1
        )

        st.dataframe(

            df[[
                "filename",
                "input_type",
                "output_type",
                "rows",
                "columns",
                "Input Size",
                "Output Size",
                "ratio",
                "Elapsed",
                "status"
            ]],

            width="stretch"
        )

        st.markdown("### CSV Options Applied")
        st.write({
            "delimiter": delimiter_choice,
            "encoding": encoding,
            "has_header": has_header,
            "quote_char": quote_char,
            "null_values": [v.strip() for v in null_values_input.split(",") if v.strip()],
            "ignore_errors": ignore_errors,
            "skip_rows": int(skip_rows),
        })

        if preview_frames:
            st.markdown("### CSV Previews")
            for preview in preview_frames:
                preview_path = preview["path"] if "path" in preview else None
                detected_encoding = "Auto"
                if preview_path is not None:
                    detected_encoding = detect_encoding(preview_path) or "utf8"
                label = f"{preview['filename']} • {detected_encoding}"
                with st.expander(label, expanded=False):
                    st.dataframe(preview["data"].head(10), width="stretch")

        st.metric(
            "Total Conversion Time",
            f"{elapsed:.2f} seconds"
        )

        zip_path = session_folder / "Converted_Files.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:

            for file in converted_files:

                zipf.write(file, arcname=file.name)

        with open(zip_path, "rb") as f:

            st.download_button(
                "📦 Download All Files",
                f,
                file_name="Converted_Files.zip",
                mime="application/zip"
            )

        