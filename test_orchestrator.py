#!/usr/bin/env python3
# test_orchestrator.py
# Test the orchestrator with existing PDFs (skip download step)

import os
import sys
from logger_setup import setup_logging
from parser import NovartisPDFParser
from file_generator import NovartisFileGenerator
import config
import logging

logger = logging.getLogger(__name__)

# Setup logging
setup_logging()

print("\n" + "="*70)
print(" Novartis Pension Fund - Test Workflow")
print(" Testing parser + file generator with existing PDFs")
print("="*70 + "\n")

# Use existing PDF
pdf_path = "downloads/20251124_091103/2024/E_Jahresbericht.pdf"

if not os.path.exists(pdf_path):
    print(f"[ERROR] PDF not found: {pdf_path}")
    sys.exit(1)

print(f"Using PDF: {pdf_path}\n")

# Parse PDF
print("Parsing PDF...")
parser = NovartisPDFParser()
result = parser.parse_pdf(pdf_path)

if not result:
    print("[ERROR] Failed to parse PDF")
    sys.exit(1)

print(f"\n[SUCCESS] Parsed successfully:")
print(f"  Year: {result['year']}")
print(f"  Total Assets: {result.get('total_assets', 'N/A')} CHF millions")

percentages = result.get('percentages', {})
if percentages:
    print(f"  Asset Allocation:")
    for asset, pct in percentages.items():
        print(f"    {asset}: {pct}%")

# Generate files
print("\n" + "-"*70)
print("Generating output files...\n")

generator = NovartisFileGenerator()
output_files = generator.generate_files([result], config.OUTPUT_DIR)

print("\n" + "="*70)
print(" TEST COMPLETE")
print("="*70 + "\n")

print("Output files:")
print(f"  DATA: {os.path.basename(output_files['data_file'])}")
print(f"  META: {os.path.basename(output_files['meta_file'])}")
print(f"  ZIP:  {os.path.basename(output_files['zip_file'])}")
print(f"\nOutput directory: {os.path.dirname(output_files['data_file'])}")
print(f"Latest files: {config.LATEST_OUTPUT_DIR}\n")
