#!/usr/bin/env python3
# test_scraper.py
# Test script for the Novartis scraper

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger_setup import setup_logging
from scraper import NovartisDownloader
import config

def main():
    """Test the scraper"""

    # Setup logging
    logger = setup_logging()

    print("\n" + "="*60)
    print(" NOVARTIS PENSION FUND SCRAPER - TEST MODE")
    print("="*60 + "\n")

    print("Configuration:")
    print("-" * 60)
    print(f"  Target Year: {config.TARGET_YEAR if config.TARGET_YEAR else 'Latest (automatic)'}")
    print(f"  Process All Years: {config.PROCESS_ALL_YEARS}")
    print(f"  Parallel Downloads: {config.PARALLEL_DOWNLOADS}")
    print(f"  Headless Mode: {config.HEADLESS_MODE}")
    print(f"  Download Directory: {config.DOWNLOAD_DIR}")
    print(f"  Log Directory: {config.LOG_DIR}")
    print("-" * 60 + "\n")

    try:
        # Create downloader instance
        downloader = NovartisDownloader()

        # Download reports
        logger.info("Starting download process...")
        results = downloader.download_reports()

        # Display results
        print("\n" + "="*60)
        print(" TEST RESULTS")
        print("="*60 + "\n")

        if results:
            print(f"Successfully downloaded {len(results)} report(s):\n")
            for result in results:
                print(f"  Year: {result['year']}")
                print(f"  Title: {result['title']}")
                print(f"  File: {result['file_path']}")
                print(f"  Size: {os.path.getsize(result['file_path'])} bytes")
                print()

            print("="*60)
            print("TEST PASSED [SUCCESS]")
            print("="*60)
            return 0
        else:
            print("No files were downloaded.")
            print("="*60)
            print("TEST FAILED [ERROR]")
            print("="*60)
            return 1

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test cancelled by user")
        logger.warning("Test interrupted by user")
        return 1

    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        logger.error(f"Test failed with error: {e}", exc_info=True)
        print("="*60)
        print("TEST FAILED [ERROR]")
        print("="*60)
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
