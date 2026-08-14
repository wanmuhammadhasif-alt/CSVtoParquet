from pathlib import Path
import os
import time
import polars as pl
import chardet

from statistics import ConversionStat


def detect_encoding(file_path):
    """Detect file encoding using chardet"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)  # Read first 100KB for detection
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf8')
            return encoding if encoding else 'utf8'
    except Exception:
        return 'utf8'


def convert_file(input_file, output_folder, csv_options=None):

    input_file = Path(input_file)

    start = time.time()

    filename = input_file.name
    extension = input_file.suffix.lower()

    input_size = input_file.stat().st_size

    csv_options = csv_options or {}

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
        
        # Auto-detect encoding if set to utf8 and file has issues
        detected_encoding = detect_encoding(input_file)
        original_encoding = encoding

        scan_args = {
            "encoding": encoding,
            "has_header": csv_options.get("has_header", True),
            "null_values": csv_options.get("null_values", ["NULL", "NA", "N/A"]),
            "ignore_errors": csv_options.get("ignore_errors", False),
            "skip_rows": csv_options.get("skip_rows", 0),
        }
        quote_char = csv_options.get("quote_char", '"')
        if quote_char:
            scan_args["quote_char"] = quote_char
        if delimiter is not None:
            scan_args["separator"] = delimiter

        def _scan_csv_with_args(args):
            return pl.scan_csv(input_file, **args)

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
                # Try detected encoding first, then other fallbacks
                fallback_encodings = [detected_encoding, "utf8-sig", "latin1", "cp1252", "iso-8859-1", "windows-1252", "utf16"]
                # Remove duplicates while preserving order
                fallback_encodings = list(dict.fromkeys(fallback_encodings))
                
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