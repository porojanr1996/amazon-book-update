"""
Strict BSR (Best Sellers Rank) Parser
Extracts and validates BSR values from HTML with strict rules
"""
import re
import logging
from typing import Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Maximum reasonable BSR value (Amazon's max is around 10 million)
MAX_BSR_VALUE = 10000000


def parse_bsr(html: str) -> Optional[int]:
    """
    Strict BSR parser that extracts BSR from HTML
    
    Rules:
    - Returns None if BSR is missing, invalid, zero, or negative
    - Strips all formatting (#, commas, text)
    - Validates BSR is within reasonable range (1 to MAX_BSR_VALUE)
    - Never returns invalid values
    
    Args:
        html: HTML content from Amazon product page
        
    Returns:
        BSR value as integer (1 to MAX_BSR_VALUE), or None if not found/invalid
    """
    if not html or len(html) < 100:
        logger.debug("HTML too short or empty")
        return None
    
    try:
        soup = BeautifulSoup(html, 'lxml')
    except Exception as e:
        logger.warning(f"Failed to parse HTML: {e}")
        return None
    
    # Try multiple extraction methods in order of specificity
    
    # Method 1: SalesRank div (most reliable)
    bsr = _extract_from_salesrank_div(soup)
    if bsr:
        return bsr
    
    # Method 2: Search in all text for BSR patterns
    bsr = _extract_from_page_text(soup)
    if bsr:
        return bsr
    
    # Method 3: Look for BSR in specific elements
    bsr = _extract_from_elements(soup)
    if bsr:
        return bsr
    
    logger.debug("BSR not found in HTML")
    return None


def _extract_from_salesrank_div(soup: BeautifulSoup) -> Optional[int]:
    """Extract BSR from SalesRank div - prioritize main BSR over category BSRs"""
    product_details = soup.find('div', {'id': 'SalesRank'})
    if not product_details:
        return None
    
    text = product_details.get_text()
    if not text:
        return None
    
    # Patterns ordered by priority (most specific/main BSR first)
    # Priority 1: Main BSR - "Best Sellers Rank: #X in Kindle Store" (US) or "Best Sellers Rank: X in Kindle Store" (UK)
    patterns = [
        # Main BSR patterns (highest priority) - US format with #
        r'Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'Amazon\s+Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        # Main BSR patterns - UK format without # (e.g., "Best Sellers Rank: 1,726 in Kindle Store")
        r'Best\s+Sellers\s+Rank:\s*(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'Amazon\s+Best\s+Sellers\s+Rank:\s*(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        # Fallback patterns (with or without #)
        r'Best\s+Sellers\s+Rank:\s*#?(\d{1,3}(?:,\d{3})*)',  # With or without #
        r'Amazon\s+Best\s+Sellers\s+Rank:\s*#?(\d{1,3}(?:,\d{3})*)',
        # Main BSR with "See Top" - prioritize Kindle Store
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store.*?\(See\s+Top',
        r'(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store.*?\(See\s+Top',  # UK format without #
        # General patterns (lower priority - may match category BSRs)
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
        r'(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',  # UK format without #
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+.*?Store.*?\(See\s+Top',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            bsr_value = _parse_bsr_number(match.group(1))
            if bsr_value:
                # Additional validation: if BSR is very low (< 1000), it might be a category BSR
                # Main BSR is usually higher (thousands or tens of thousands)
                # But we still return it if it matches the main BSR pattern
                logger.debug(f"Found BSR in SalesRank div: {bsr_value} (pattern: {pattern[:50]})")
                return bsr_value
    
    return None


def _extract_from_page_text(soup: BeautifulSoup) -> Optional[int]:
    """Extract BSR from page text - prioritize main BSR over category BSRs"""
    page_text = soup.get_text()
    if not page_text:
        return None
    
    # Patterns ordered by priority (main BSR first, category BSRs last)
    # Priority 1: Main BSR patterns (works for both US and UK)
    patterns = [
        # Main BSR - US format: "Best Sellers Rank: #X in Kindle Store" (highest priority)
        r'Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'Amazon\s+Best\s+Sellers\s+Rank:\s*#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        # Main BSR - UK format: "Best Sellers Rank: X in Kindle Store" (without #)
        r'Best\s+Sellers\s+Rank:\s*(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'Amazon\s+Best\s+Sellers\s+Rank:\s*(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        # UK format: "Best Sellers Rank: X" (without "in Kindle Store" sometimes)
        r'Best\s+Sellers\s+Rank:\s*#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
        # Main BSR with "See Top" - prioritize Kindle Store (both formats)
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store.*?\(See\s+Top',
        r'(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store.*?\(See\s+Top',  # UK format without #
        # Main BSR without explicit "Best Sellers Rank:" but in Kindle Store
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',
        r'(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle\s+Store',  # UK format without #
        # Fallback patterns (may match category BSRs - use with caution)
        r'Best\s+Sellers\s+Rank.*?#?(\d{1,3}(?:,\d{3})*)\s+in\s+Kindle',
        # Only match "in Store" if it's a reasonable BSR (>= 1000) to avoid category rankings
        r'#(\d{1,3}(?:,\d{3}){2,})\s+in\s+.*?Store',  # At least 3 digits (1,000+) to avoid small category ranks
        r'(\d{1,3}(?:,\d{3}){2,})\s+in\s+Kindle\s+Store',  # UK format, at least 1,000+
        r'#(\d{1,3}(?:,\d{3})*)\s+in\s+.*?\(See\s+Top',
        # Last resort: "Best Sellers Rank:" without "in" (validate it's reasonable)
        r'Best\s+Sellers\s+Rank[:\s]*#?(\d{1,3}(?:,\d{3}){2,})',  # At least 1,000 to avoid category ranks
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, page_text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            bsr_value = _parse_bsr_number(match.group(1))
            if bsr_value:
                logger.debug(f"Found BSR in page text: {bsr_value} (pattern: {pattern[:50]})")
                return bsr_value
    
    return None


def _extract_from_elements(soup: BeautifulSoup) -> Optional[int]:
    """Extract BSR from specific HTML elements"""
    # Look for BSR in span/div elements with rank-related IDs
    rank_elements = soup.find_all(['span', 'div'], {'id': re.compile(r'.*rank.*|.*bsr.*', re.I)})
    for element in rank_elements:
        text = element.get_text()
        if text:
            match = re.search(r'#?(\d{1,3}(?:,\d{3})+)', text)
            if match:
                bsr_value = _parse_bsr_number(match.group(1))
                if bsr_value:
                    logger.debug(f"Found BSR in element: {bsr_value}")
                    return bsr_value
    
    # Look for elements containing "Best Sellers Rank" text
    rank_sections = soup.find_all(text=re.compile(r'Best.*Seller.*Rank', re.I))
    for section in rank_sections:
        parent = section.parent if hasattr(section, 'parent') else None
        if parent:
            text = parent.get_text()
            match = re.search(r'#(\d{1,3}(?:,\d{3})+)', text)
            if match:
                bsr_value = _parse_bsr_number(match.group(1))
                if bsr_value:
                    logger.debug(f"Found BSR in rank section: {bsr_value}")
                    return bsr_value
    
    return None


def _parse_bsr_number(bsr_str: str) -> Optional[int]:
    """
    Parse BSR number string with strict validation
    
    Rules:
    - Strips all formatting (#, commas, whitespace)
    - Returns None if zero, negative, or invalid
    - Validates range (1 to MAX_BSR_VALUE)
    
    Args:
        bsr_str: BSR string (e.g., "1,234" or "#1,234")
        
    Returns:
        Validated BSR integer or None
    """
    if not bsr_str:
        return None
    
    # Strip all formatting: #, commas, whitespace
    cleaned = re.sub(r'[#,\s]', '', str(bsr_str))
    
    # Must be digits only
    if not cleaned.isdigit():
        logger.debug(f"BSR string contains non-digits: {bsr_str}")
        return None
    
    try:
        bsr_value = int(cleaned)
    except (ValueError, OverflowError):
        logger.debug(f"Failed to parse BSR as integer: {bsr_str}")
        return None
    
    # Validate: must be positive and within reasonable range
    if bsr_value <= 0:
        logger.debug(f"BSR is zero or negative: {bsr_value}")
        return None
    
    if bsr_value > MAX_BSR_VALUE:
        logger.debug(f"BSR exceeds maximum: {bsr_value} > {MAX_BSR_VALUE}")
        return None
    
    return bsr_value

