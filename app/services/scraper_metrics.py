"""
Metrics tracking for Amazon scraper
Tracks success rate, CAPTCHA rate, retry rate, and scrape times
"""
import time
from collections import defaultdict
from threading import Lock
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ScraperMetrics:
    """Thread-safe metrics tracker for scraper performance"""
    
    def __init__(self):
        self._lock = Lock()
        self._reset()
    
    def _reset(self):
        """Reset all metrics"""
        self.total_requests = 0
        self.successful_extractions = 0
        self.captcha_detections = 0
        self.network_errors = 0
        self.other_errors = 0
        self.retries = 0
        self.scrape_times = []  # List of scrape durations in seconds
        self.error_reasons = defaultdict(int)  # Error reason -> count
    
    def record_request(self, duration: float, success: bool, 
                      captcha: bool = False, retried: bool = False,
                      error_reason: Optional[str] = None):
        """
        Record a scraping request
        
        Args:
            duration: Time taken in seconds
            success: Whether BSR was successfully extracted
            captcha: Whether CAPTCHA was detected
            retried: Whether this was a retry attempt
            error_reason: Reason for failure if not successful
        """
        with self._lock:
            self.total_requests += 1
            self.scrape_times.append(duration)
            
            if success:
                self.successful_extractions += 1
            elif captcha:
                self.captcha_detections += 1
                if error_reason:
                    self.error_reasons[error_reason] += 1
            else:
                if 'network' in (error_reason or '').lower() or 'timeout' in (error_reason or '').lower():
                    self.network_errors += 1
                else:
                    self.other_errors += 1
                if error_reason:
                    self.error_reasons[error_reason] += 1
            
            if retried:
                self.retries += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self._lock:
            if self.total_requests == 0:
                return {
                    'total_requests': 0,
                    'success_rate': 0.0,
                    'captcha_rate': 0.0,
                    'retry_rate': 0.0,
                    'avg_scrape_time': 0.0,
                    'network_error_rate': 0.0,
                    'error_reasons': {}
                }
            
            avg_time = sum(self.scrape_times) / len(self.scrape_times) if self.scrape_times else 0.0
            
            return {
                'total_requests': self.total_requests,
                'success_rate': self.successful_extractions / self.total_requests,
                'captcha_rate': self.captcha_detections / self.total_requests,
                'retry_rate': self.retries / self.total_requests,
                'avg_scrape_time': avg_time,
                'network_error_rate': self.network_errors / self.total_requests,
                'successful_extractions': self.successful_extractions,
                'captcha_detections': self.captcha_detections,
                'network_errors': self.network_errors,
                'other_errors': self.other_errors,
                'retries': self.retries,
                'error_reasons': dict(self.error_reasons)
            }
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("SCRAPER METRICS")
        logger.info("=" * 60)
        logger.info(f"Total Requests: {stats['total_requests']}")
        logger.info(f"Success Rate: {stats['success_rate']:.1%}")
        logger.info(f"CAPTCHA Rate: {stats['captcha_rate']:.1%}")
        logger.info(f"Retry Rate: {stats['retry_rate']:.1%}")
        logger.info(f"Avg Scrape Time: {stats['avg_scrape_time']:.2f}s")
        logger.info(f"Network Error Rate: {stats['network_error_rate']:.1%}")
        if stats['error_reasons']:
            logger.info("Error Reasons:")
            for reason, count in stats['error_reasons'].items():
                logger.info(f"  - {reason}: {count}")
        logger.info("=" * 60)
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._reset()


# Global metrics instance
_metrics = ScraperMetrics()


def get_metrics() -> ScraperMetrics:
    """Get global metrics instance"""
    return _metrics

