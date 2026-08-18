# CSV ? Parquet Batch Converter

A Streamlit-based app for converting CSV and Parquet files in batches with automatic encoding detection, preview support, and ZIP export.

## Features

- Batch upload and conversion of multiple CSV and Parquet files
- CSV ? Parquet conversion
- Parquet ? CSV conversion
- Auto encoding detection when the Encoding option is set to Auto
- Advanced CSV parsing controls:
  - delimiter selection
  - header detection
  - quote character
  - null values
  - skip rows
  - ignore errors
  - truncate ragged lines
- Conversion summary table with file stats
- Output CSV preview for generated CSV files
- Output Parquet preview for generated Parquet files
- Download all converted files as a ZIP archive

## Requirements

- Python 3.10+
- Streamlit
- Polars
- Pandas
- PyArrow
- Chardet

Install dependencies:

```bash
pip install -r requirement.txt
```

## Run the app

```bash
streamlit run app.py
```

Then open the local Streamlit URL, usually:

```text
http://localhost:8501
```

## Usage

1. Upload one or more CSV or Parquet files.
2. If CSV files are included, configure the CSV options in the Advanced CSV Settings section.
3. Click Convert.
4. Review the conversion summary and output previews.
5. Download the ZIP bundle containing all converted files.

## CSV settings

Available options include:

- Encoding: Auto, utf8, utf-8, utf-8-sig, latin-1, utf16, cp1252
- Delimiter: Auto, comma, semicolon, tab, pipe
- Has Header
- Quote Character
- Null Values
- Ignore Errors
- Truncate Ragged Lines
- Skip Rows

## Encoding behavior

When Encoding is set to Auto, the app attempts to detect the uploaded CSV encoding automatically. If detection fails, it falls back to common encodings such as utf8-sig, latin1, and cp1252.

## Preview behavior

After conversion, the app shows:

- Output CSV Preview for generated CSV files
- Output Parquet Preview for generated Parquet files

This helps verify the result before downloading the converted files.

## Project structure

```text
CSV-Parquet-Converter/
+-- app.py
+-- converter.py
+-- statistics.py
+-- utils.py
+-- requirement.txt
+-- README.md
+-- output/
+-- temp/
+-- TestingSampleFile/
+-- .gitignore
```

## Notes

- Temporary folders are created during conversion under the `temp` directory.
- Large files may take longer to process depending on the machine and file size.
- This app is intended for local or hosted Streamlit deployment.

## License

This project is provided as-is for personal and internal use.

## Changelog

### Current

- Auto CSV encoding detection
- Output CSV preview for converted files
- Output Parquet preview for converted files
- Batch conversion summary and statistics
- Improved CSV parsing and malformed row handling
