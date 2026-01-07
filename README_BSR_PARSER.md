# Strict BSR Parser

## Overview

A strict BSR (Best Sellers Rank) parser that ensures data integrity by:
- Returning `None` for missing, invalid, zero, or negative values
- Stripping all formatting (#, commas, text)
- Validating BSR is within reasonable range (1 to 10,000,000)
- **Never writing invalid BSR values to Google Sheets or database**

## Function Signature

```python
parse_bsr(html: str) -> int | None
```

## Rules

1. **Returns None if:**
   - HTML is empty or too short (< 100 chars)
   - BSR is missing from HTML
   - BSR is zero or negative
   - BSR exceeds maximum (10,000,000)
   - BSR contains non-numeric characters (after stripping formatting)

2. **Strips all formatting:**
   - Hash symbols (#)
   - Commas (,)
   - Whitespace
   - Text surrounding the number

3. **Validates range:**
   - Minimum: 1
   - Maximum: 10,000,000

## Usage

```python
from app.utils.bsr_parser import parse_bsr

html = "<div id='SalesRank'>#1,234 in Kindle Store</div>"
bsr = parse_bsr(html)  # Returns: 1234

# Invalid cases return None
parse_bsr("<div>No BSR here</div>")  # None
parse_bsr("<div>#0 in Store</div>")  # None
parse_bsr("<div>#-123 in Store</div>")  # None
parse_bsr("<div>#15,000,000 in Store</div>")  # None (exceeds max)
```

## Integration

The strict parser is automatically used in:
- `AmazonScraper.extract_bsr()` - All BSR extraction methods
- `TieredAmazonScraper.fetch_page()` - Tier 1 and Tier 2
- `PlaywrightScraper.extract_bsr_with_playwright()` - Browser-based extraction
- `GoogleSheetsManager.update_bsr()` - Validates before writing

## Unit Tests

Run tests:
```bash
python -m pytest tests/test_bsr_parser.py -v
```

Test coverage includes:
- Valid BSR extraction from various HTML formats
- Invalid BSR detection (zero, negative, too large)
- Formatting stripping (#, commas, whitespace)
- Edge cases (empty HTML, missing BSR, etc.)

## Safety Guarantees

1. **Never writes invalid values:** All BSR values are validated before writing to Google Sheets
2. **Type safety:** Only returns `int` or `None`, never strings or other types
3. **Range validation:** Ensures BSR is within Amazon's valid range
4. **Format agnostic:** Handles various HTML formats and BSR presentations

