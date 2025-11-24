# scraper.py
# Downloads Annual Report PDFs from Novartis Pension Fund website

import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config
import concurrent.futures
import requests
import re

# Setup logging
logger = logging.getLogger(__name__)


class NovartisDownloader:
    """Downloads annual report PDFs from Novartis Pension Fund website"""

    def __init__(self):
        self.driver = None
        self.download_dir = None
        self.logger = logger

    def setup_driver(self):
        """Initialize Chrome driver with download preferences"""

        # Create download directory with timestamp
        self.download_dir = os.path.abspath(config.DOWNLOAD_DIR)
        os.makedirs(self.download_dir, exist_ok=True)

        chrome_options = Options()

        # Set download directory
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,  # Don't open in browser
            "plugins.plugins_disabled": ["Chrome PDF Viewer"]
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if config.HEADLESS_MODE:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(config.WAIT_TIMEOUT)

        self.logger.info(f"Chrome driver initialized")
        self.logger.info(f"Download directory: {self.download_dir}")

    def navigate_to_downloads_page(self):
        """Navigate to the downloads page"""

        self.logger.info(f"Navigating to {config.BASE_URL}")

        self.driver.get(config.BASE_URL)
        time.sleep(config.PAGE_LOAD_DELAY)

        self.logger.info("Page loaded successfully")

    def handle_cookie_consent(self):
        """Click 'Allow all' on Cookiebot consent dialog"""

        self.logger.info("Handling cookie consent...")

        try:
            # Wait for cookie consent button to appear
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)
            consent_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, config.SELECTORS['cookie_allow_all']))
            )

            self.logger.info("Cookie consent dialog found")
            consent_button.click()
            time.sleep(2)  # Wait for dialog to close

            self.logger.info("Cookie consent accepted")
            return True

        except TimeoutException:
            self.logger.warning("Cookie consent dialog not found (may have been accepted previously)")
            return False
        except Exception as e:
            self.logger.error(f"Error handling cookie consent: {e}")
            return False

    def scroll_to_annual_reports(self):
        """Scroll down to Annual Reports accordion"""

        self.logger.info("Scrolling to Annual Reports section...")

        try:
            # Find the Annual Reports accordion
            accordion = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS['annual_reports_accordion'])

            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", accordion)
            time.sleep(1)

            self.logger.info("Scrolled to Annual Reports accordion")
            return True

        except NoSuchElementException:
            self.logger.error("Annual Reports accordion not found")
            return False

    def expand_annual_reports_accordion(self):
        """Click on Annual Reports accordion header to expand it"""

        self.logger.info("Expanding Annual Reports accordion...")

        try:
            wait = WebDriverWait(self.driver, config.WAIT_TIMEOUT)

            # Find the accordion header (clickable element)
            accordion_header = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, f"{config.SELECTORS['annual_reports_accordion']} {config.SELECTORS['accordion_header']}")
                )
            )

            # Check if already expanded
            classes = accordion_header.get_attribute('class')
            if 'is-visible' in classes:
                self.logger.info("Accordion already expanded")
                return True

            # Click to expand
            accordion_header.click()
            time.sleep(2)  # Wait for expansion animation

            self.logger.info("Annual Reports accordion expanded")
            return True

        except Exception as e:
            self.logger.error(f"Error expanding accordion: {e}")
            return False

    def extract_year_from_text(self, text):
        """Extract year from report title (e.g., 'Annual Report 2024' -> 2024)"""

        # Look for 4-digit year
        match = re.search(r'(\d{4})', text)
        if match:
            return match.group(1)
        return None

    def get_report_links(self):
        """
        Extract all report links from the Annual Reports accordion.
        Returns list of dicts with year, title, and URL.
        """

        self.logger.info("Extracting report links...")

        try:
            # Find all report items
            report_items = self.driver.find_elements(
                By.CSS_SELECTOR,
                f"{config.SELECTORS['reports_container']} {config.SELECTORS['report_items']}"
            )

            self.logger.info(f"Found {len(report_items)} report entries")

            reports = []

            for item in report_items:
                try:
                    # Find the link element
                    link_element = item.find_element(By.TAG_NAME, 'a')
                    url = link_element.get_attribute('href')

                    # Get title from span
                    title_span = link_element.find_element(By.CSS_SELECTOR, config.SELECTORS['report_title_span'])
                    title = title_span.text.strip()

                    # Extract year from title
                    year = self.extract_year_from_text(title)

                    if year and url:
                        reports.append({
                            'year': year,
                            'title': title,
                            'url': url
                        })
                        self.logger.debug(f"Found: {year} - {title}")

                except Exception as e:
                    self.logger.warning(f"Error extracting report info: {e}")
                    continue

            self.logger.info(f"Extracted {len(reports)} valid report links")
            return reports

        except Exception as e:
            self.logger.error(f"Error getting report links: {e}")
            return []

    def filter_reports_by_config(self, reports):
        """
        Filter reports based on TARGET_YEAR configuration.
        Returns filtered list.
        """

        # Check PROCESS_ALL_YEARS first
        if config.PROCESS_ALL_YEARS:
            self.logger.info(f"Mode: ALL YEARS - {len(reports)} reports")
            return reports

        if config.TARGET_YEAR is None:
            # Get the most recent report (first in list, assuming descending order)
            if reports:
                # Sort by year descending to get latest
                reports_sorted = sorted(reports, key=lambda x: x['year'], reverse=True)
                filtered = [reports_sorted[0]]
                self.logger.info(f"Mode: Latest year - {filtered[0]['year']}")
                return filtered
            return []
        else:
            # Specific year
            target_year_str = str(config.TARGET_YEAR)
            filtered = [r for r in reports if r['year'] == target_year_str]
            self.logger.info(f"Mode: Specific year {config.TARGET_YEAR} - {len(filtered)} report(s)")
            return filtered

    def download_pdf_direct(self, report_info):
        """
        Download PDF directly using requests (faster, parallel-safe).
        Returns the local file path if successful.
        """

        year = report_info['year']
        title = report_info['title']
        url = report_info['url']

        # Create year subdirectory
        year_dir = os.path.join(self.download_dir, year)
        os.makedirs(year_dir, exist_ok=True)

        # Extract filename from URL or generate one
        if '/' in url:
            filename = url.split('/')[-1]
        else:
            filename = f"Annual_Report_{year}.pdf"

        expected_file = os.path.join(year_dir, filename)

        # Check if file already exists (caching)
        if os.path.exists(expected_file) and os.path.getsize(expected_file) > 10000:
            self.logger.info(f"Cached: {year} - {filename}")
            return expected_file

        self.logger.info(f"Downloading {year} - {title}")

        try:
            # Make URL absolute if relative
            if url.startswith('/'):
                base_domain = 'https://www.pensionskassen-novartis.ch'
                url = base_domain + url

            # Download with requests
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Save file
            with open(expected_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Verify file size
            if os.path.getsize(expected_file) > 10000:
                self.logger.info(f"Downloaded: {year} - {os.path.getsize(expected_file)} bytes")
                return expected_file
            else:
                os.remove(expected_file)
                self.logger.error(f"Download failed - file too small: {year}")
                return None

        except Exception as e:
            self.logger.error(f"Download failed for {year}: {e}")
            return None

    def download_reports(self):
        """
        Main method to download reports based on configuration.
        Returns list of downloaded file paths and metadata.
        """

        try:
            self.setup_driver()
            self.navigate_to_downloads_page()

            # Handle cookie consent
            self.handle_cookie_consent()

            # Scroll to Annual Reports section
            if not self.scroll_to_annual_reports():
                self.logger.error("Failed to scroll to Annual Reports")
                return []

            # Expand the accordion
            if not self.expand_annual_reports_accordion():
                self.logger.error("Failed to expand Annual Reports accordion")
                return []

            # Get all report links
            all_reports = self.get_report_links()

            if not all_reports:
                self.logger.error("No report links found")
                return []

            # Filter based on configuration
            target_reports = self.filter_reports_by_config(all_reports)

            if not target_reports:
                self.logger.error("No reports match the specified criteria")
                return []

            print(f"\n{'='*60}")
            print(f"Downloading {len(target_reports)} report(s)")
            if config.PARALLEL_DOWNLOADS:
                print(f"Mode: PARALLEL (up to {config.MAX_WORKERS} workers)")
            else:
                print(f"Mode: SEQUENTIAL")
            print(f"{'='*60}\n")

            # Download reports
            downloaded_files = []

            if config.PARALLEL_DOWNLOADS and len(target_reports) > 1:
                # Parallel download using ThreadPoolExecutor
                self.logger.info(f"Starting parallel downloads with {config.MAX_WORKERS} workers")

                with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
                    # Submit all download tasks
                    future_to_report = {
                        executor.submit(self.download_pdf_direct, report): report
                        for report in target_reports
                    }

                    # Process completed downloads
                    for i, future in enumerate(concurrent.futures.as_completed(future_to_report), 1):
                        report = future_to_report[future]
                        try:
                            file_path = future.result()
                            if file_path:
                                downloaded_files.append({
                                    'year': report['year'],
                                    'title': report['title'],
                                    'file_path': file_path
                                })
                                print(f"[{i}/{len(target_reports)}] {report['year']} [OK]")
                            else:
                                print(f"[{i}/{len(target_reports)}] {report['year']} [FAILED]")
                        except Exception as e:
                            self.logger.error(f"Error downloading {report['year']}: {e}")
                            print(f"[{i}/{len(target_reports)}] {report['year']} [ERROR]")

                        # Rate limiting
                        if i < len(target_reports):
                            time.sleep(config.DOWNLOAD_DELAY)

            else:
                # Sequential download
                for i, report in enumerate(target_reports, 1):
                    print(f"[{i}/{len(target_reports)}] {report['year']} - {report['title']}")

                    file_path = self.download_pdf_direct(report)
                    if file_path:
                        downloaded_files.append({
                            'year': report['year'],
                            'title': report['title'],
                            'file_path': file_path
                        })
                        print(f"  [OK] Downloaded\n")
                    else:
                        print(f"  [FAILED]\n")

                    time.sleep(config.DOWNLOAD_DELAY)

            print(f"\n{'='*60}")
            print(f"Download complete: {len(downloaded_files)} of {len(target_reports)} successful")
            print(f"{'='*60}\n")

            return downloaded_files

        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")


def main():
    """Test the downloader"""
    downloader = NovartisDownloader()
    results = downloader.download_reports()

    print("\nDownloaded files:")
    for result in results:
        print(f"  {result['year']}: {result['file_path']}")


if __name__ == '__main__':
    main()
