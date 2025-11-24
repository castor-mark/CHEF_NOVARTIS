# config.py
# Novartis Pension Fund Data Collection Configuration

import os
from datetime import datetime

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

BASE_URL = 'https://www.pensionskassen-novartis.ch/en/services/downloads'
PROVIDER_NAME = 'Novartis Pension Funds'
DATASET_NAME = 'NOVARTIS'
COUNTRY = 'Switzerland'
CURRENCY = 'CHF'

# =============================================================================
# TIMESTAMPED FOLDERS CONFIGURATION
# =============================================================================

# Generate timestamp for this run (format: YYYYMMDD_HHMMSS)
RUN_TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Use timestamped folders to avoid conflicts between runs
USE_TIMESTAMPED_FOLDERS = True

# =============================================================================
# PROCESSING CONFIGURATION
# =============================================================================

# Target year for data extraction
# Set to None to auto-detect most recent year (latest available)
# Format: 2024, 2023, etc.
TARGET_YEAR = 2022   # Options: None (latest), 2024, 2023, 2022, etc.

# When set to True, process all available years from the accordion
PROCESS_ALL_YEARS = False

# =============================================================================
# WEB SCRAPING SELECTORS (from listener session)
# =============================================================================

SELECTORS = {
    # Cookie consent (Cookiebot)
    'cookie_allow_all': 'button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',

    # Annual Reports accordion
    'annual_reports_accordion': 'div#c7006',
    'accordion_header': 'div.panel-heading',
    'accordion_header_expanded': 'div.panel-heading.is-visible',

    # Report links container
    'reports_container': 'div#c7011',
    'report_list': 'ul.document-list',
    'report_items': 'li',
    'report_link': 'a',
    'report_title_span': 'span.underline',

    # PDF link structure
    # Example: /fileadmin/pkn/Jahresberichte/2024/E_Jahresbericht.pdf
    'pdf_link_pattern': '/fileadmin/pkn/Jahresberichte/{year}/'
}

# =============================================================================
# PDF PARSING CONFIGURATION
# =============================================================================

# Keywords to find "The composition of assets" section
PDF_CHART_KEYWORDS = [
    "The composition of assets breaks down as follows:",
    "The composition of assets",
    "composition of assets"
]

# Table column headers to look for
PDF_TABLE_HEADERS = [
    "Assets (CHF millions)",
    "31.12.",  # Date pattern for columns
]

# Asset class names in PDF (map to output codes)
PDF_ASSET_NAMES = {
    'INFRASTRUCTURE': ['Infrastructure investments', 'Infrastructure'],
    'CASH': ['Liquidity deposits', 'Liquidity / Receivables', 'Liquidity', 'Receivables'],
    'MORTGAGES': ['Mortgages'],
    'BONDS': ['Bonds'],
    'EQUITIES': ['Shares', 'Equities'],
    'REALESTATE': ['Real estate investments', 'Real estate'],
    'HEDGEFUNDS/PRIVATEEQUITY': ['Hedge funds and private equity', 'Hedge Funds / Private Equity'],
    'CURRENCYOVERLAY': ['Currency overlay'],
    'COLLATERAL': ['Collateral'],
    'TOTAL': ['Total assets']
}

# Percentage chart keywords (pie chart section)
PERCENTAGE_CHART_KEYWORDS = [
    "Bonds",
    "Shares",
    "Real estate investments",
    "Hedge Funds / Private Equity",
    "Infrastructure investments",
    "Liquidity / Receivables"
]

# =============================================================================
# OUTPUT COLUMN STRUCTURE (EXACT ORDER - DO NOT CHANGE)
# =============================================================================

# Based on CHEF_NOVARTIS_DATA_20230327 - DATA (1).csv
# Column order is ABSOLUTE and must match exactly

OUTPUT_COLUMNS = [
    {
        'code': 'NOVARTIS.TOTAL.LEVEL.NONE.A.1@NOVARTIS',
        'description': 'Assets of Novartis Pension Fund, Total',
        'asset': 'TOTAL',
        'metric': 'LEVEL',
        'unit': 'CHF millions',
        'source': 'table',  # From "Total assets" row
        'multiplier': 0.0  # Already in millions
    },
    {
        'code': 'NOVARTIS.INFRASTRUCTURE.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, Infrastructure',
        'asset': 'INFRASTRUCTURE',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',  # From pie chart
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.CASH.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, Cash',
        'asset': 'CASH',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.MORTGAGES.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, Mortgages',
        'asset': 'MORTGAGES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.BONDS.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, Bonds',
        'asset': 'BONDS',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.EQUITIES.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, Equities',
        'asset': 'EQUITIES',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.REALESTATE.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, RealEstate',
        'asset': 'REALESTATE',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    },
    {
        'code': 'NOVARTIS.HEDGEFUNDS/PRIVATEEQUITY.ACTUALALLOCATION.NONE.A.1@NOVARTIS',
        'description': 'The composition of assets, Actual Allocation, HedgeFunds/PrivateEquity',
        'asset': 'HEDGEFUNDS/PRIVATEEQUITY',
        'metric': 'ACTUALALLOCATION',
        'unit': 'Percentage',
        'source': 'chart',
        'multiplier': 0.0
    }
]

# =============================================================================
# METADATA STANDARD FIELDS
# =============================================================================

METADATA_DEFAULTS = {
    'FREQUENCY': 'A',  # Annual
    'AGGREGATION_TYPE': 'END_OF_PERIOD',
    'UNIT_TYPE': 'LEVEL',
    'DATA_TYPE': 'CURRENCY',
    'DATA_UNIT': CURRENCY,
    'SEASONALLY_ADJUSTED': 'NSA',
    'ANNUALIZED': False,
    'PROVIDER_MEASURE_URL': BASE_URL,
    'PROVIDER': 'AfricaAI',
    'SOURCE': 'NOVARTIS',
    'SOURCE_DESCRIPTION': PROVIDER_NAME,
    'COUNTRY': COUNTRY,
    'DATASET': DATASET_NAME
}

# Metadata file columns
METADATA_COLUMNS = [
    'CODE',
    'DESCRIPTION',
    'FREQUENCY',
    'MULTIPLIER',
    'AGGREGATION_TYPE',
    'UNIT_TYPE',
    'DATA_TYPE',
    'DATA_UNIT',
    'SEASONALLY_ADJUSTED',
    'ANNUALIZED',
    'PROVIDER_MEASURE_URL',
    'PROVIDER',
    'SOURCE',
    'SOURCE_DESCRIPTION',
    'COUNTRY',
    'DATASET'
]

# =============================================================================
# DATE FORMATS
# =============================================================================

DATE_FORMAT_OUTPUT = '%Y'  # Annual format (YYYY)
DATETIME_FORMAT_META = '%Y-%m-%d %H:%M:%S'
FILENAME_DATE_FORMAT = '%Y%m%d'

# =============================================================================
# BROWSER CONFIGURATION
# =============================================================================

HEADLESS_MODE = False
DEBUG_MODE = True
WAIT_TIMEOUT = 20
PAGE_LOAD_DELAY = 3
DOWNLOAD_WAIT_TIME = 10  # Wait time for PDF download

# =============================================================================
# DOWNLOAD CONFIGURATION
# =============================================================================

# Parallel downloads (faster for multiple years)
PARALLEL_DOWNLOADS = True
MAX_WORKERS = 3
DOWNLOAD_DELAY = 1.0  # Seconds between requests

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Base directories
BASE_DOWNLOAD_DIR = './downloads'
BASE_OUTPUT_DIR = './output'
BASE_LOG_DIR = './logs'

# Apply timestamping if enabled
if USE_TIMESTAMPED_FOLDERS:
    DOWNLOAD_DIR = os.path.join(BASE_DOWNLOAD_DIR, RUN_TIMESTAMP)
    OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, RUN_TIMESTAMP)
    LOG_DIR = os.path.join(BASE_LOG_DIR, RUN_TIMESTAMP)
else:
    DOWNLOAD_DIR = BASE_DOWNLOAD_DIR
    OUTPUT_DIR = BASE_OUTPUT_DIR
    LOG_DIR = BASE_LOG_DIR

# Latest folder (always contains most recent extraction)
LATEST_OUTPUT_DIR = os.path.join(BASE_OUTPUT_DIR, 'latest')

# File naming patterns
DATA_FILE_PATTERN = 'CHEF_NOVARTIS_DATA_{timestamp}.xls'
META_FILE_PATTERN = 'CHEF_NOVARTIS_META_{timestamp}.xls'
ZIP_FILE_PATTERN = 'CHEF_NOVARTIS_{timestamp}.zip'

# Log file naming
LOG_FILE_PATTERN = 'novartis_{timestamp}.log'

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'DEBUG' if DEBUG_MODE else 'INFO'

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Console output
LOG_TO_CONSOLE = True
LOG_TO_FILE = True

# =============================================================================
# PDF PARSING LIBRARIES
# =============================================================================

# Use both pdfplumber and camelot for robust extraction
USE_PDFPLUMBER = True  # For text and keyword search
USE_CAMELOT = True     # For table extraction

# Camelot settings
CAMELOT_FLAVOR = 'lattice'  # 'lattice' for tables with lines, 'stream' for tables without lines
CAMELOT_TABLE_AREAS = None  # Auto-detect table areas

# =============================================================================
# VALIDATION SETTINGS
# =============================================================================

# Validate that all required asset classes are found
REQUIRE_ALL_ASSETS = True

# Validate percentage totals (should sum to 100% or close)
VALIDATE_PERCENTAGE_TOTAL = True
PERCENTAGE_TOLERANCE = 2.0  # Allow 2% deviation from 100%

# =============================================================================
# ERROR HANDLING
# =============================================================================

# Continue processing even if some PDFs fail
CONTINUE_ON_ERROR = True

# Maximum retries for download failures
MAX_DOWNLOAD_RETRIES = 3
RETRY_DELAY = 2.0  # Seconds between retries
