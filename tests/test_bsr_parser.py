"""
Unit tests for strict BSR parser
"""
import unittest
from app.utils.bsr_parser import parse_bsr, _parse_bsr_number


class TestBSRParser(unittest.TestCase):
    """Test cases for BSR parser"""
    
    def test_valid_bsr_salesrank_div(self):
        """Test valid BSR in SalesRank div"""
        html = '''
        <div id="SalesRank">
            Best Sellers Rank: #1,234 in Kindle Store (See Top 100 in Kindle Store)
        </div>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 1234)
    
    def test_valid_bsr_with_commas(self):
        """Test BSR with comma formatting"""
        html = '''
        <div id="SalesRank">
            #12,345 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 12345)
    
    def test_valid_bsr_in_page_text(self):
        """Test BSR found in page text"""
        html = '''
        <html>
            <body>
                <p>This book is ranked #567 in Kindle Store</p>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 567)
    
    def test_valid_bsr_best_sellers_rank(self):
        """Test BSR with 'Best Sellers Rank' text"""
        html = '''
        <html>
            <body>
                <span>Best Sellers Rank: #890 in Books</span>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 890)
    
    def test_valid_bsr_no_hash(self):
        """Test BSR without hash symbol"""
        html = '''
        <div id="SalesRank">
            Best Sellers Rank: 1,234 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 1234)
    
    def test_missing_bsr(self):
        """Test HTML without BSR"""
        html = '''
        <html>
            <body>
                <h1>Product Title</h1>
                <p>Product description</p>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertIsNone(result)
    
    def test_empty_html(self):
        """Test empty HTML"""
        result = parse_bsr("")
        self.assertIsNone(result)
    
    def test_too_short_html(self):
        """Test HTML that's too short"""
        result = parse_bsr("<html></html>")
        self.assertIsNone(result)
    
    def test_zero_bsr(self):
        """Test BSR value of zero (should return None)"""
        html = '''
        <div id="SalesRank">
            #0 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertIsNone(result)
    
    def test_negative_bsr(self):
        """Test negative BSR (should return None)"""
        html = '''
        <div id="SalesRank">
            #-123 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertIsNone(result)
    
    def test_invalid_bsr_too_large(self):
        """Test BSR exceeding maximum (should return None)"""
        html = '''
        <div id="SalesRank">
            #15,000,000 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertIsNone(result)
    
    def test_invalid_bsr_with_text(self):
        """Test BSR mixed with text (should extract number)"""
        html = '''
        <div id="SalesRank">
            Ranked #2,345 in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 2345)
    
    def test_multiple_bsr_values(self):
        """Test HTML with multiple BSR values (should return first valid)"""
        html = '''
        <html>
            <body>
                <div id="SalesRank">#1,234 in Kindle Store</div>
                <p>Also ranked #5,678 in Books</p>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 1234)  # Should return first valid
    
    def test_bsr_with_whitespace(self):
        """Test BSR with extra whitespace"""
        html = '''
        <div id="SalesRank">
            #   1,234   in Kindle Store
        </div>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 1234)
    
    def test_bsr_in_element_with_id(self):
        """Test BSR in element with rank-related ID"""
        html = '''
        <span id="productRank">#3,456</span>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 3456)
    
    def test_real_amazon_html_fixture(self):
        """Test with realistic Amazon HTML structure"""
        html = '''
        <html>
            <head><title>Book Title</title></head>
            <body>
                <div id="SalesRank">
                    <span class="value">
                        #7,890
                    </span>
                    <span class="label">
                        in Kindle Store (See Top 100 in Kindle Store)
                    </span>
                </div>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertEqual(result, 7890)
    
    def test_captcha_page(self):
        """Test CAPTCHA page (should return None)"""
        html = '''
        <html>
            <body>
                <h1>Sorry, we just need to make sure you're not a robot</h1>
                <p>Please complete the CAPTCHA</p>
            </body>
        </html>
        '''
        result = parse_bsr(html)
        self.assertIsNone(result)
    
    def test_parse_bsr_number_valid(self):
        """Test _parse_bsr_number with valid input"""
        self.assertEqual(_parse_bsr_number("1,234"), 1234)
        self.assertEqual(_parse_bsr_number("#1,234"), 1234)
        self.assertEqual(_parse_bsr_number("1234"), 1234)
        self.assertEqual(_parse_bsr_number(" 1,234 "), 1234)
    
    def test_parse_bsr_number_invalid(self):
        """Test _parse_bsr_number with invalid input"""
        self.assertIsNone(_parse_bsr_number("0"))
        self.assertIsNone(_parse_bsr_number("-123"))
        self.assertIsNone(_parse_bsr_number("abc"))
        self.assertIsNone(_parse_bsr_number(""))
        self.assertIsNone(_parse_bsr_number("15,000,000"))  # Too large
        self.assertIsNone(_parse_bsr_number("12.34"))  # Decimal
    
    def test_parse_bsr_number_edge_cases(self):
        """Test edge cases for _parse_bsr_number"""
        self.assertEqual(_parse_bsr_number("1"), 1)  # Minimum valid
        self.assertEqual(_parse_bsr_number("10000000"), 10000000)  # Maximum valid
        self.assertIsNone(_parse_bsr_number("10000001"))  # Over maximum
        self.assertIsNone(_parse_bsr_number("000"))  # Zero with leading zeros


if __name__ == '__main__':
    unittest.main()

