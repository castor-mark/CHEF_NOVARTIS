# parser.py
# Parse "The composition of assets" from Novartis Annual Report PDFs

import pdfplumber
import camelot
import re
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class NovartisPDFParser:
    """Extracts asset composition data from Novartis Annual Report PDFs"""

    def __init__(self):
        self.debug = config.DEBUG_MODE
        self.logger = logger

    def extract_year_from_pdf(self, pdf_path):
        """
        Extract the report year from PDF filename or content.
        Priority: filename -> PDF content
        """

        # Try filename first
        import os
        filename = os.path.basename(pdf_path)
        year_match = re.search(r'(\d{4})', filename)
        if year_match:
            year = year_match.group(1)
            self.logger.info(f"Extracted year from filename: {year}")
            return year

        # Try PDF content
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first 3 pages
                for page in pdf.pages[:3]:
                    text = page.extract_text()

                    # Look for "Annual Report YYYY"
                    match = re.search(r'Annual Report\s+(\d{4})', text)
                    if match:
                        year = match.group(1)
                        self.logger.info(f"Extracted year from PDF content: {year}")
                        return year

        except Exception as e:
            self.logger.error(f"Error extracting year: {e}")

        return None

    def find_composition_section(self, pdf_path):
        """
        Find the page containing "The composition of assets" section.
        Returns (page_number, page_text).
        """

        self.logger.info("Searching for composition of assets section...")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()

                    # Check if this page contains the composition section
                    for keyword in config.PDF_CHART_KEYWORDS:
                        if keyword.lower() in text.lower():
                            self.logger.info(f"Found composition section on page {page_num + 1}")
                            return page_num, text

        except Exception as e:
            self.logger.error(f"Error finding composition section: {e}")

        return None, None

    def extract_percentages_from_text(self, text):
        """
        Extract asset allocation percentages from text using regex.
        Looks for patterns like "Bonds 27%" or "Shares 27%"
        """

        percentages = {}

        self.logger.info("Extracting percentages from text...")

        # For each asset class, look for percentage
        for asset_code, asset_names in config.PDF_ASSET_NAMES.items():
            for asset_name in asset_names:
                # Pattern: "Asset Name XX%" (flexible spacing)
                pattern = rf'{re.escape(asset_name)}\s+(\d+)%'
                match = re.search(pattern, text, re.IGNORECASE)

                if match:
                    percentage = float(match.group(1))
                    percentages[asset_code] = percentage
                    self.logger.debug(f"Found {asset_code}: {percentage}%")
                    break  # Found match for this asset, move to next

        return percentages

    def find_balance_sheet_page(self, pdf_path):
        """
        Find the page containing "Balance sheet" section.
        Returns page number (0-indexed) or None if not found.
        """

        self.logger.info("Searching for Balance sheet page...")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and 'balance sheet' in text.lower():
                        self.logger.info(f"Found Balance sheet on page {page_num + 1}")
                        return page_num
        except Exception as e:
            self.logger.error(f"Error searching for Balance sheet: {e}")

        return None

    def extract_total_assets_from_table(self, pdf_path, page_num=None):
        """
        Extract "Total assets" value from the balance sheet table.
        Uses proven 6-part pattern validated across 2020-2024 reports.
        Returns the value in CHF millions.

        Pattern: "Total assets DD DDD DD DDD" -> parts[2] + parts[3] = current year value
        Example: "Total assets 13 432 13 083" -> "13" + "432" = 13432
        """

        # If page_num not provided, search for Balance sheet page dynamically
        if page_num is None:
            page_num = self.find_balance_sheet_page(pdf_path)
            if page_num is None:
                self.logger.error("Balance sheet page not found")
                return None

        self.logger.info(f"Extracting total assets from page {page_num + 1}...")

        try:
            with pdfplumber.open(pdf_path) as pdf:
                page = pdf.pages[page_num]
                text = page.extract_text()

                if not text:
                    self.logger.error("No text extracted from page")
                    return None

                lines = text.split('\n')

                # Find "Total assets" line (exclude "Total liabilities")
                for line in lines:
                    if 'total assets' in line.lower() and 'total liabilities' not in line.lower():
                        self.logger.debug(f"Found Total assets line: [{line}]")

                        # Split by spaces
                        parts = line.split()
                        self.logger.debug(f"Split into {len(parts)} parts: {parts}")

                        # Validate expected pattern: ['Total', 'assets', d1, d2, d3, d4]
                        if len(parts) != 6:
                            self.logger.warning(f"Unexpected pattern: expected 6 parts, got {len(parts)}")
                            # Try fallback method
                            return self.extract_total_assets_fallback(line, parts)

                        if parts[0].lower() != 'total' or parts[1].lower() != 'assets':
                            self.logger.warning(f"Pattern validation failed: parts[0]={parts[0]}, parts[1]={parts[1]}")
                            return None

                        # Reconstruct current year value from parts[2] + parts[3]
                        # Example: ['Total', 'assets', '13', '432', '13', '083'] -> "13432"
                        current_year_str = parts[2] + parts[3]
                        self.logger.debug(f"Reconstructed current year value: {current_year_str}")

                        # Clean and convert
                        total_assets = self.clean_number(current_year_str)

                        if total_assets is None:
                            self.logger.error(f"Failed to convert '{current_year_str}' to number")
                            return None

                        # Validation: Total assets should be > 10000 CHF millions
                        if total_assets < 10000:
                            self.logger.warning(f"Total assets value {total_assets} seems too low (expected > 10000)")

                        self.logger.info(f"Extracted Total assets: {total_assets} CHF millions")
                        return total_assets

                self.logger.error("'Total assets' line not found in page text")
                return None

        except Exception as e:
            self.logger.error(f"Error extracting total assets: {e}")
            return None

    def extract_total_assets_fallback(self, line, parts):
        """
        Fallback method for non-standard patterns.
        Handles cases where parts count != 6.
        """

        self.logger.info("Attempting fallback extraction method...")

        # If we have fewer parts, maybe numbers aren't space-separated
        # Try to find all digit sequences
        digit_sequences = re.findall(r'\d+', line)

        self.logger.debug(f"Found digit sequences: {digit_sequences}")

        if len(digit_sequences) >= 2:
            # Try to reconstruct from digit sequences
            # Look for sequences that could form a 5-digit number (e.g., "13432")
            for i in range(len(digit_sequences) - 1):
                # Try combining consecutive sequences
                combined = digit_sequences[i] + digit_sequences[i+1]
                val = self.clean_number(combined)

                if val and 10000 <= val <= 50000:
                    self.logger.info(f"Fallback succeeded: {val} CHF millions")
                    return val

        # Last resort: try to extract any 5-digit number
        five_digit_match = re.search(r'\b1[34]\d{3}\b', line)
        if five_digit_match:
            val = self.clean_number(five_digit_match.group())
            if val:
                self.logger.warning(f"Using last resort extraction: {val} CHF millions")
                return val

        self.logger.error("Fallback extraction failed")
        return None

    def clean_number(self, value_str):
        """Clean and convert a string to a number (handles spaces, commas, etc.)"""

        if value_str is None or value_str == '' or value_str == 'nan':
            return None

        # Remove spaces, commas, and other non-numeric characters except decimal point
        cleaned = str(value_str).replace(' ', '').replace(',', '').replace('\xa0', '').strip()

        # Try to convert to float
        try:
            return float(cleaned)
        except ValueError:
            return None

    def calculate_cash_percentage(self, percentages):
        """
        Calculate Cash percentage if not directly stated.
        Cash = Liquidity + Receivables, or inferred from other percentages.
        """

        # Check if we have Infrastructure, Bonds, Shares, Real Estate, Hedge Funds
        known_assets = ['INFRASTRUCTURE', 'BONDS', 'EQUITIES', 'REALESTATE', 'HEDGEFUNDS/PRIVATEEQUITY']

        if all(asset in percentages for asset in known_assets):
            # Calculate remaining percentage for Cash
            total_known = sum(percentages[asset] for asset in known_assets)
            cash_percentage = 100.0 - total_known

            if 0 <= cash_percentage <= 100:
                self.logger.info(f"Calculated CASH percentage: {cash_percentage}%")
                return cash_percentage

        return None

    def parse_pdf(self, pdf_path):
        """
        Main method to parse a PDF report.
        Returns dict with year and all asset class data.
        """

        self.logger.info(f"\nParsing PDF: {pdf_path}")

        # Extract year
        year = self.extract_year_from_pdf(pdf_path)

        if not year:
            self.logger.error("Could not extract year from PDF")
            return None

        # Find composition section
        page_num, page_text = self.find_composition_section(pdf_path)

        if page_num is None:
            self.logger.error("Could not find composition of assets section")
            return None

        # Extract percentages from text
        percentages = self.extract_percentages_from_text(page_text)

        if not percentages:
            self.logger.error("Could not extract asset percentages")
            return None

        self.logger.info(f"Extracted {len(percentages)} asset percentages")

        # Calculate Cash if not found
        if 'CASH' not in percentages:
            cash_pct = self.calculate_cash_percentage(percentages)
            if cash_pct is not None:
                percentages['CASH'] = cash_pct

        # Extract Total assets from Balance sheet (searches dynamically, doesn't use page_num from composition section)
        total_assets = self.extract_total_assets_from_table(pdf_path)

        if total_assets is None:
            self.logger.warning("Could not extract total assets value")

        # Build result dictionary
        result = {
            'year': year,
            'total_assets': total_assets,
            'percentages': percentages
        }

        # Validation
        if config.VALIDATE_PERCENTAGE_TOTAL:
            total_pct = sum(percentages.values())
            deviation = abs(total_pct - 100.0)

            if deviation > config.PERCENTAGE_TOLERANCE:
                self.logger.warning(f"Percentage total: {total_pct}% (deviation: {deviation}%)")
            else:
                self.logger.info(f"Percentage validation passed: {total_pct}%")

        # Check if all required assets are present
        if config.REQUIRE_ALL_ASSETS:
            required_assets = [col['asset'] for col in config.OUTPUT_COLUMNS if col['metric'] == 'ACTUALALLOCATION']
            missing_assets = [asset for asset in required_assets if asset not in percentages]

            if missing_assets:
                self.logger.warning(f"Missing assets: {', '.join(missing_assets)}")

        self.logger.info(f"Successfully parsed {year} - Total Assets: {total_assets}, Percentages: {len(percentages)}")

        return result


def main():
    """Test the parser with a sample PDF"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parser.py <pdf_file>")
        sys.exit(1)

    pdf_file = sys.argv[1]
    parser = NovartisPDFParser()
    result = parser.parse_pdf(pdf_file)

    if result:
        print(f"\nYear: {result['year']}")
        print(f"Total Assets: {result['total_assets']} CHF millions")
        print(f"\nAsset Allocation Percentages:")

        for asset_code, percentage in result['percentages'].items():
            print(f"  {asset_code}: {percentage}%")


if __name__ == '__main__':
    main()
