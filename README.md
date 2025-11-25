# Novartis Pension Fund Data Collection System

Automated data collection and extraction system for Novartis Pension Fund annual reports.

## Overview

This system automatically:
1. Downloads annual report PDFs from the Novartis Pension Funds website
2. Extracts asset allocation percentages and total assets
3. Generates Excel DATA and META files in the required format

## Project Structure

```
CHEF_NOVARTIS/
├── config.py              # Configuration (URLs, selectors, output structure)
├── logger_setup.py        # Logging configuration
├── scraper.py             # Web scraping and PDF downloading
├── parser.py              # PDF parsing and data extraction
├── file_generator.py      # Excel file generation
├── orchestrator.py        # Main workflow coordinator
├── downloads/             # Downloaded PDFs (timestamped)
├── output/                # Generated Excel files (timestamped)
│   └── latest/            # Latest output files
├── logs/                  # Execution logs (timestamped)
└── bin/                   # Test/debug files (archived)
```

## Requirements

- Python 3.11+
- Chrome browser (for Selenium)
- Required packages: selenium, pdfplumber, camelot-py, xlwt

## Installation

```bash
pip install selenium pdfplumber camelot-py xlwt
```

## Usage

### Run Full Workflow (Download + Parse + Generate)

```bash
python orchestrator.py
```

This will:
- Download the latest annual report PDF
- Extract data from the PDF
- Generate DATA, META, and ZIP files
- Save to timestamped and 'latest' folders

### Configuration

Edit `config.py` to configure:

```python
# Target year (None = latest, or specify year/list of years)
TARGET_YEAR = None  # or 2024 or [2023, 2024]

# Output structure (8 columns matching spec)
OUTPUT_COLUMNS = [...]
```

## Output Files

The system generates three files:

1. **CHEF_NOVARTIS_DATA_YYYYMMDD_HHMMSS.xls**
   - Time series data with years in rows
   - 8 columns: TOTAL (LEVEL) + 7 asset classes (ACTUALALLOCATION)

2. **CHEF_NOVARTIS_META_YYYYMMDD_HHMMSS.xls**
   - Metadata for all time series
   - Includes codes, descriptions, frequency, multiplier, etc.

3. **CHEF_NOVARTIS_YYYYMMDD_HHMMSS.zip**
   - Combined archive of DATA and META files

All files are also copied to `output/latest/` for easy access.

## Data Extracted

### Total Assets
- **Source**: Balance sheet table
- **Value**: Total assets in CHF millions
- **Method**: Keyword search + pattern matching (validated 2020-2024)

### Asset Allocation Percentages
- **Source**: "The composition of assets" pie chart
- **Asset Classes**:
  - Infrastructure investments
  - Liquidity / Receivables (Cash)
  - Bonds
  - Shares (Equities)
  - Real estate investments
  - Hedge Funds / Private Equity

## Validation

The parser has been validated across 5 years (2020-2024) with **100% accuracy**:

| Year | Total Assets (CHF millions) | Status |
|------|----------------------------|--------|
| 2024 | 13,432 | ✅ |
| 2023 | 13,083 | ✅ |
| 2022 | 13,149 | ✅ |
| 2021 | 14,572 | ✅ |
| 2020 | 14,116 | ✅ |

## Logging

Logs are saved in timestamped folders: `logs/YYYYMMDD_HHMMSS/`

- Console: INFO level
- File: DEBUG level
- Third-party libraries (pdfminer, selenium): WARNING level

## Troubleshooting

### Download fails
- Check internet connection
- Verify website is accessible
- Check Chrome/chromedriver compatibility

### Parser fails
- Verify PDF format hasn't changed
- Check logs for specific errors
- Ensure PDF contains "Balance sheet" and "composition of assets" sections

### Missing data
- Check `config.PDF_ASSET_NAMES` mappings
- Verify percentage keywords match PDF text
- Review DEBUG logs for extraction details

## License

Proprietary - Novartis Pension Fund Data Collection

## Author

Created by following the USAF project pattern.
