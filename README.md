# CSV ↔ Parquet Batch Converter

A powerful Streamlit web application for converting between CSV and Parquet file formats with advanced encoding and data handling capabilities.

## Features

✨ **Core Features:**
- 🔄 Batch conversion (multiple files at once)
- 📊 Bidirectional conversion (CSV → Parquet and Parquet → CSV)
- 📈 Real-time progress tracking
- 📥 Automatic file download as ZIP

🔧 **Advanced CSV Settings:**
- **Auto Encoding Detection** - Automatically detects file encoding (UTF-8, UTF-16, CP1252, etc.)
- **Automatic Encoding Conversion** - Converts unsupported encodings to UTF-8
- **Custom Delimiters** - Support for comma, semicolon, tab, pipe delimiters
- **Header Detection** - Toggle header row detection
- **Custom Quote Characters** - Define quote character for CSV parsing
- **Null Values Customization** - Define what values should be treated as NULL
- **Ignore Errors** - Skip rows with parsing errors
- **Truncate Ragged Lines** - Handle inconsistent row structures (rows with different column counts)
- **Skip Rows** - Skip initial rows in the file

📊 **Conversion Statistics:**
- File name and size information
- Input/output types
- Row and column counts
- Compression ratio
- Conversion time elapsed

## Requirements

- Python 3.8+
- Streamlit >= 1.45
- Polars >= 1.31
- PyArrow >= 21.0
- Pandas >= 2.3
- Chardet >= 5.0

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/wanmuhammadhasif-alt/CSVtoParquet.git
cd CSVtoParquet
```

2. **Install dependencies:**
```bash
pip install -r requirement.txt
```

3. **Run the application:**
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Basic Conversion

1. **Upload Files:**
   - Click "Upload CSV / Parquet" to select one or more files
   - Supports both CSV and Parquet formats

2. **Configure Settings (Optional):**
   - Click "Advance CSV Setting" expander
   - Adjust delimiter, encoding, and other options as needed

3. **Convert:**
   - Click the "Convert" button
   - Monitor progress in real-time

4. **Download:**
   - Once complete, download all converted files as a ZIP

### Advanced CSV Settings Guide

#### Delimiter
- **Auto** - Automatically detects delimiter
- **,** - Comma (default)
- **;** - Semicolon (common in European CSVs)
- **Tab** - Tab character
- **|** - Pipe character

#### Encoding
- **utf8** - UTF-8 (default, recommended)
- **utf-8** - UTF-8 variant
- **utf-8-sig** - UTF-8 with BOM
- **latin-1** - Western European
- **utf16** - Unicode 16-bit
- **cp1252** - Windows Latin-1

**Note:** If your file uses an unsupported encoding, the converter will automatically attempt to convert it to UTF-8 first using pandas.

#### Truncate Ragged Lines
**What it does:** Handles CSV files with inconsistent row structures (rows having different numbers of columns).

**When to use:**
- File has rows with extra or missing columns
- Rows aren't properly aligned
- Data has irregular structure

**Example:**
```csv
name,age,city,country
John,30,NYC,USA
Jane,25,LA           # Missing country
Bob,35,London,UK,Extra  # Extra column
```

With `Truncate Ragged Lines` enabled:
- Rows with fewer columns get padded with NULL
- Rows with extra columns get truncated
- All rows align to have the same number of columns

### Common Use Cases

#### Converting Vietnamese/Southeast Asian Files
1. Upload CSV file
2. Set Encoding to `utf16` or `latin-1`
3. Enable `Truncate Ragged Lines` if needed
4. Click Convert

#### Handling Malformed CSVs
1. Enable `Ignore Errors` to skip problematic rows
2. Enable `Truncate Ragged Lines` for inconsistent structure
3. Adjust `null_values` to match your data's NULL representations

#### European CSV Files
1. Set Delimiter to `;` (semicolon)
2. Set Encoding to `latin-1` or `utf-8-sig`
3. Convert

## File Structure

```
CSV-Parquet-Converter/
├── app.py                 # Main Streamlit application
├── converter.py           # Conversion logic
├── statistics.py          # Statistics tracking
├── utils.py              # Utility functions
├── requirement.txt       # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # This file
├── output/              # Output folder for conversions
├── temp/                # Temporary processing folder
└── TestingSampleFile/   # Sample test files
```

## How It Works

### CSV to Parquet Conversion

1. **Upload** - User uploads CSV file
2. **Detect Encoding** - Uses `chardet` to auto-detect file encoding
3. **Convert if Needed** - If encoding is unsupported by Polars, converts to UTF-8 using pandas
4. **Parse with Polars** - Reads CSV with specified options
5. **Write Parquet** - Efficiently writes to Parquet format
6. **Statistics** - Collects and displays conversion metrics

### Parquet to CSV Conversion

1. **Upload** - User uploads Parquet file
2. **Read with Polars** - Reads Parquet efficiently
3. **Write CSV** - Exports to CSV format
4. **Statistics** - Shows conversion results

## Compression Benefits

Parquet format provides significant compression compared to CSV:
- **Typical compression ratio:** 80-90% smaller than CSV
- **Example:** 30MB CSV → ~3-5MB Parquet
- **Benefits:** Faster read/write, better for large datasets

## Supported File Types

| Format | Read | Write | Notes |
|--------|------|-------|-------|
| CSV    | ✓    | ✓     | With advanced encoding/delimiter support |
| Parquet| ✓    | ✓     | Columnar, compressed format |

## Error Handling

The converter includes robust error handling:

| Error | Solution |
|-------|----------|
| "invalid utf-8 sequence" | Try different encoding in Advanced Settings |
| "found more fields than defined" | Enable "Truncate Ragged Lines" |
| Rows being skipped | Enable "Ignore Errors" or check delimiter |

## Performance Notes

- **Large files (>1GB):** May take a few minutes to process
- **Memory usage:** Streams data lazily where possible
- **Batch processing:** Converting 50+ small files is more efficient in batches

## Contributing

Feel free to open issues and submit pull requests for improvements!

## License

This project is open source. Feel free to use and modify as needed.

## Changelog

### Version 1.0.0 (2026-08-14)
- ✨ Initial release with CSV ↔ Parquet conversion
- 🔧 Advanced CSV settings with encoding detection
- 📊 Real-time conversion statistics
- 🎯 Batch file processing
- 🐛 Auto-handling of ragged CSV files
- 🌍 Multi-encoding support for international files

## Support

For issues, questions, or suggestions, please open an issue on GitHub:
https://github.com/wanmuhammadhasif-alt/CSVtoParquet/issues

## Author

Created by Wan Muhammad Hasif

---

**Happy Converting!** 🎉
