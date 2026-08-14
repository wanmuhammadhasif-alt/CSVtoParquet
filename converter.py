from pathlib import Path
import os
import time
import polars as pl
import chardet
import pandas as pd

from statistics import ConversionStat


def detect_encoding(file_path):
    """Detect file encoding using chardet"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(500000)  # Read first 500KB for detection
            
            # Also check just the first line (header)
            f.seek(0)
            first_line = f.readline()
            
            # Try detection on first line + rest
            combined_data = first_line + raw_data
            result = chardet.detect(combined_data)
            encoding = result.get('encoding', 'utf8')
            confidence = result.get('confidence', 0)
            
            # If confidence is low, try alternative detections
            if confidence < 0.7:
                # Try with just first line
                result_header = chardet.detect(first_line)
                if result_header.get('confidence', 0) > confidence:
                    encoding = result_header.get('encoding', encoding)
            
            return encoding if encoding else 'utf8'
    except Exception:
        return 'utf8'


def convert_to_utf8(file_path, temp_output_path, detected_encoding):
    """
    Convert file to UTF-8 if it's using an unsupported encoding.
    Polars only supports 'utf8' and 'utf8-lossy', so we need to convert other encodings.
    """
    try:
        # Try to read with detected encoding
        df = pd.read_csv(file_path, encoding=detected_encoding, on_bad_lines='skip')
        # Write back as UTF-8
        df.to_csv(temp_output_path, index=False, encoding='utf-8')
        return temp_output_path
    except Exception:
        # If detected encoding fails, try common encodings
        for enc in ['utf8', 'latin1', 'cp1252', 'iso-8859-1', 'windows-1252', 'utf-8-sig']:
            try:
                df = pd.read_csv(file_path, encoding=enc, on_bad_lines='skip')
                df.to_csv(temp_output_path, index=False, encoding='utf-8')
                return temp_output_path
            except Exception:
                continue
        
        # If all attempts fail, return the original file
        return file_path


def convert_file(input_file, output_folder, csv_options=None):

    input_file = Path(input_file)

    start = time.time()

    filename = input_file.name
    extension = input_file.suffix.lower()

    input_size = input_file.stat().st_size

    csv_options = csv_options or {}
    
    # Initialize temp_csv_path for cleanup later
    temp_csv_path = None

    if extension == ".csv":
        delimiter = csv_options.get("delimiter", "Auto")
        if delimiter == "Auto":
            delimiter = None
        elif delimiter == "Tab":
            delimiter = "\t"

        output = Path(output_folder) / f"{input_file.stem}.parquet"

        encoding = csv_options.get("encoding", "utf8")
        if isinstance(encoding, str):
            encoding = encoding.strip().lower()
            if encoding == "utf-8":
                encoding = "utf8"
            if encoding == "utf-8-sig":
                encoding = "utf8-sig"
        
        # Auto-detect encoding
        detected_encoding = detect_encoding(input_file)
        original_encoding = encoding
        
        # Check if detected encoding is not UTF-8 compatible
        # If so, convert to UTF-8 first
        temp_csv_path = input_file
        unsupported_encodings = ['utf-16', 'utf-16-le', 'utf-16-be', 'utf16', 'cp1252', 'iso-8859-1', 'windows-1252', 'cp1258', 'latin1']
        
        if detected_encoding and detected_encoding.lower().replace('-', '').replace('_', '') in [e.lower().replace('-', '').replace('_', '') for e in unsupported_encodings]:
            # Convert to UTF-8 first
            temp_csv_path = Path(input_file.parent) / f".temp_{input_file.name}"
            convert_to_utf8(input_file, temp_csv_path, detected_encoding)
            encoding = "utf8"  # Use UTF-8 after conversion
        elif encoding == "utf8" and detected_encoding and detected_encoding.lower() != "utf8" and detected_encoding.lower() != "ascii":
            # If we detected a different encoding, try converting
            try:
                temp_csv_path = Path(input_file.parent) / f".temp_{input_file.name}"
                convert_to_utf8(input_file, temp_csv_path, detected_encoding)
                encoding = "utf8"
            except Exception:
                temp_csv_path = input_file
                encoding = "utf8"

        scan_args = {
            "encoding": encoding,
            "has_header": csv_options.get("has_header", True),
            "null_values": csv_options.get("null_values", ["NULL", "NA", "N/A"]),
            "ignore_errors": csv_options.get("ignore_errors", False),
            "truncate_ragged_lines": csv_options.get("truncate_ragged_lines", False),
            "skip_rows": csv_options.get("skip_rows", 0),
        }
        quote_char = csv_options.get("quote_char", '"')
        if quote_char:
            scan_args["quote_char"] = quote_char
        if delimiter is not None:
            scan_args["separator"] = delimiter

        def _scan_csv_with_args(args):
            return pl.scan_csv(temp_csv_path, **args)

        def _is_encoding_error(message):
            return "utf-8" in message or "utf8" in message

        def _is_ragged_error(message):
            return "found more fields than defined in 'schema'" in message or "truncate_ragged_lines" in message or "ragged" in message

        try:
            df_lazy = _scan_csv_with_args(scan_args)
        except Exception as e:
            error_message = str(e).lower()
            df_lazy = None

            if _is_encoding_error(error_message):
                # Only use Polars-supported encodings
                # If we got an encoding error, try utf8-lossy as fallback
                fallback_encodings = ["utf8-lossy", "utf8"]
                
                for fallback_encoding in fallback_encodings:
                    scan_args["encoding"] = fallback_encoding
                    try:
                        df_lazy = _scan_csv_with_args(scan_args)
                        break
                    except Exception as inner_e:
                        if _is_ragged_error(str(inner_e).lower()):
                            break
                        continue

            if df_lazy is None:
                if _is_ragged_error(error_message):
                    scan_args["truncate_ragged_lines"] = True
                    df_lazy = _scan_csv_with_args(scan_args)
                else:
                    # last attempt: allow ragged rows if any scan_csv error remains
                    scan_args["truncate_ragged_lines"] = True
                    df_lazy = _scan_csv_with_args(scan_args)

        # write out lazily
        df_lazy.sink_parquet(output)

        output_type = "Parquet"

        # compute rows and columns without collecting the full dataset
        try:
            cnt_df = df_lazy.select(pl.count()).collect()
            rows = cnt_df.row(0)[0] if cnt_df.height > 0 else 0
            columns = len(df_lazy.collect_schema().names())
        except Exception:
            # fallback to collecting (may use more memory)
            eager = df_lazy.collect()
            rows = eager.height
            columns = eager.width

    elif extension == ".parquet":

        df_lazy = pl.scan_parquet(input_file)

        output = Path(output_folder) / f"{input_file.stem}.csv"

        # write out lazily
        df_lazy.sink_csv(output)

        output_type = "CSV"

        # compute rows and columns without collecting the full dataset
        try:
            cnt_df = df_lazy.select(pl.count()).collect()
            rows = cnt_df.row(0)[0] if cnt_df.height > 0 else 0
            columns = len(df_lazy.collect_schema().names())
        except Exception:
            eager = df_lazy.collect()
            rows = eager.height
            columns = eager.width

    else:
        raise ValueError(f"Unsupported file type: {extension}")

    elapsed = time.time() - start

    output_size = output.stat().st_size
    
    # Clean up temporary file if one was created
    if temp_csv_path and temp_csv_path != input_file and temp_csv_path.exists():
        try:
            temp_csv_path.unlink()
        except Exception:
            pass  # Silently ignore cleanup errors

    stat = ConversionStat(
        filename=filename,
        input_type=extension.replace(".", "").upper(),
        output_type=output_type,
        rows=rows,
        columns=columns,
        input_size=input_size,
        output_size=output_size,
        elapsed=elapsed,
        status="Success"
    )

    return stat, output