#!/usr/bin/env python3
"""
Script pentru extragerea BSR-ului din screenshot-uri Amazon folosind OCR
"""
import sys
import re
from pathlib import Path
import argparse

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("❌ OCR not available. Install with: pip install pytesseract pillow")
    print("   Also install tesseract: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
    sys.exit(1)


def extract_bsr_from_screenshot(screenshot_path: str) -> int:
    """
    Extract BSR from screenshot using OCR
    
    Args:
        screenshot_path: Path to screenshot image
        
    Returns:
        BSR value or None
    """
    if not Path(screenshot_path).exists():
        print(f"❌ Screenshot not found: {screenshot_path}")
        return None
    
    try:
        # Load image
        image = Image.open(screenshot_path)
        print(f"📸 Processing screenshot: {screenshot_path}")
        print(f"   Image size: {image.size}")
        
        # Extract text using OCR
        print("🔍 Extracting text with OCR...")
        text = pytesseract.image_to_string(image)
        print(f"   Extracted {len(text)} characters")
        
        # Search for BSR pattern
        bsr_patterns = [
            r'Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
            r'Best\s+Sellers\s+Rank[:\s]*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
            r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
            r'Best\s+Sellers\s+Rank[:\s]*#?(\d{1,3}(?:,\d{3})*)',
        ]
        
        print("\n🔍 Searching for BSR patterns...")
        for i, pattern in enumerate(bsr_patterns, 1):
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    bsr_str = match.group(1).replace(',', '')
                    bsr_value = int(bsr_str)
                    if 1 <= bsr_value < 10000000:
                        print(f"✅ BSR found with pattern {i}: #{bsr_value:,}")
                        return bsr_value
                except (ValueError, AttributeError):
                    continue
        
        print("❌ BSR not found in OCR text")
        print("\n📋 First 500 characters of extracted text:")
        print(text[:500])
        return None
        
    except Exception as e:
        print(f"❌ Error processing screenshot: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description='Extract BSR from Amazon screenshot using OCR')
    parser.add_argument('screenshot', help='Path to screenshot image')
    parser.add_argument('--show-text', action='store_true', help='Show all extracted OCR text')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔍 EXTRAGERE BSR DIN SCREENSHOT")
    print("=" * 60)
    print()
    
    bsr = extract_bsr_from_screenshot(args.screenshot)
    
    if bsr:
        print()
        print("=" * 60)
        print(f"✅ BSR EXTRAS: #{bsr:,}")
        print("=" * 60)
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ BSR NU A FOST GĂSIT")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

