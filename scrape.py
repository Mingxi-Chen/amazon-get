"""
Amazon Reviews Scraper Tool
A robust scraper using Playwright to extract product reviews from Amazon
"""

import asyncio
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

from playwright.async_api import async_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Review:
    """Data class for storing review information"""
    product_id: str
    product_title: str
    reviewer: str
    rating: float
    date: str
    verified_purchase: bool
    content: str
    helpful_votes: int = 0


class AmazonReviewsScraper:
    """Main scraper class for Amazon reviews"""
    
    def __init__(self, headless: bool = False, cookies_file: Optional[str] = None):
        self.headless = headless
        self.cookies_file = cookies_file
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.reviews: List[Review] = []
        
    async def initialize(self):
        """Initialize browser and page"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--start-maximized'
            ]
        )
        
        # Create context with stealth settings
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
        )
        
        # Load cookies if provided
        if self.cookies_file and Path(self.cookies_file).exists():
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                await context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies from {self.cookies_file}")
        else:
            logger.warning(f"No cookies file found at {self.cookies_file}. You may encounter login redirects.")
        
        self.page = await context.new_page()
        
        # Additional stealth measures
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
            });
        """)
        
        # If cookies are loaded, verify we're logged in
        if self.cookies_file and Path(self.cookies_file).exists():
            await self.page.goto("https://www.amazon.com", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)
            
            # Check if logged in
            account_text = await self.page.locator("#nav-link-accountList-nav-line-1").text_content()
            if account_text and "Hello" in account_text:
                logger.info(f"Successfully logged in: {account_text}")
            else:
                logger.warning("Could not verify login status - cookies may be invalid")
        
    async def search_products(self, keyword: str, max_products: int = 3) -> List[Dict]:
        """Search for products and get top N results"""
        logger.info(f"Searching for: {keyword}")
        
        search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
        
        try:
            await self.page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            
            # Wait for page to settle
            await asyncio.sleep(2)
            
            # Try multiple possible selectors for search results
            selectors = [
                '[data-component-type="s-search-result"]',
                '[data-asin]:not([data-asin=""])',
                '.s-result-item[data-asin]',
                'div.s-card-container'
            ]
            
            result_selector = None
            for selector in selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        result_selector = selector
                        logger.info(f"Found results with selector: {selector}")
                        break
                except:
                    continue
            
            if not result_selector:
                logger.warning("No product results found on page")
                # Take screenshot for debugging
                await self.page.screenshot(path="debug_search_page.png")
                return []
            
            # Extract product information
            products = []
            product_cards = await self.page.locator(result_selector).all()
            
            for i, card in enumerate(product_cards[:max_products]):
                try:
                    # Get ASIN from data attribute
                    asin = await card.get_attribute('data-asin')
                    if not asin:
                        continue
                    
                    # Get product title - try multiple selectors
                    title = "Unknown"
                    title_selectors = ['h2 a span', 'h2 span', '.a-text-normal', '.s-link-style span']
                    for ts in title_selectors:
                        title_element = card.locator(ts)
                        if await title_element.count() > 0:
                            title = await title_element.first.text_content()
                            break
                    
                    # Get product link
                    link_element = card.locator('h2 a, a.s-link, a[href*="/dp/"]').first
                    relative_link = await link_element.get_attribute('href') if await link_element.count() > 0 else ""
                    full_link = f"https://www.amazon.com{relative_link}" if relative_link and not relative_link.startswith('http') else relative_link
                    
                    # Get price if available
                    price_element = card.locator('.a-price-whole, .a-price span').first
                    price = await price_element.text_content() if await price_element.count() > 0 else "N/A"
                    
                    # Get rating if available
                    rating_element = card.locator('[aria-label*="out of 5 stars"], .a-icon-star-small')
                    rating_text = await rating_element.get_attribute('aria-label') if await rating_element.count() > 0 else ""
                    if not rating_text:
                        rating_text = await rating_element.text_content() if await rating_element.count() > 0 else ""
                    rating = self._extract_rating(rating_text)
                    
                    products.append({
                        'asin': asin,
                        'title': title.strip() if title else "Unknown",
                        'link': full_link,
                        'price': price,
                        'rating': rating,
                        'position': i + 1
                    })
                    
                    logger.info(f"Found product {i+1}: {title[:50] if title else 'Unknown'}... (ASIN: {asin})")
                    
                except Exception as e:
                    logger.warning(f"Error extracting product {i+1}: {e}")
                    continue
            
            if not products:
                logger.warning("Could not extract any product information")
                await self.page.screenshot(path="debug_no_products.png")
            
            return products
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout loading search page: {e}")
            await self.page.screenshot(path="debug_timeout.png")
            return []
        except Exception as e:
            logger.error(f"Error in search_products: {e}")
            return []
    
    def _extract_rating(self, rating_text: str) -> float:
        """Extract numeric rating from text"""
        if not rating_text:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s+out of', rating_text)
        return float(match.group(1)) if match else 0.0
    
    async def scrape_reviews(self, product: Dict, star_filter: Optional[str] = None, 
                           max_pages: int = 2) -> List[Review]:
        """Scrape reviews for a specific product"""
        asin = product['asin']
        product_title = product['title']
        
        logger.info(f"Scraping reviews for: {product_title[:50]}...")
        
        reviews = []
        
        for page_num in range(1, max_pages + 1):
            # Construct review URL
            review_url = f"https://www.amazon.com/product-reviews/{asin}/?pageNumber={page_num}"
            
            # Add star filter if specified
            if star_filter:
                review_url += f"&filterByStar={star_filter}"
                
            logger.info(f"Fetching page {page_num}: {review_url}")
            
            try:
                await self.page.goto(review_url, wait_until="domcontentloaded", timeout=60000)
                
                # Wait a bit for content to load
                await asyncio.sleep(2)
                
                # Check if reviews exist - try multiple selectors
                review_selectors = [
                    '[data-hook="review"]',
                    'div.review',
                    '[id*="customer_review"]'
                ]
                
                found_reviews = False
                for selector in review_selectors:
                    if await self.page.locator(selector).count() > 0:
                        found_reviews = True
                        logger.info(f"Found reviews with selector: {selector}")
                        break
                
                if not found_reviews:
                    logger.warning(f"No reviews found on page {page_num}")
                    await self.page.screenshot(path=f"debug_reviews_page_{page_num}.png")
                    break
                
                # Extract reviews from current page
                page_reviews = await self._extract_reviews_from_page(asin, product_title)
                reviews.extend(page_reviews)
                
                logger.info(f"Extracted {len(page_reviews)} reviews from page {page_num}")
                
                # Small delay between pages
                await asyncio.sleep(2)
                
            except PlaywrightTimeoutError:
                logger.warning(f"Timeout on page {page_num} for product {asin}")
                break
            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                break
        
        return reviews
    
    async def _extract_reviews_from_page(self, asin: str, product_title: str) -> List[Review]:
        """Extract all reviews from current page"""
        reviews = []
        
        # First check if we're on a login page
        if "signin" in self.page.url.lower() or "ap/signin" in self.page.url:
            logger.error("Redirected to login page - cookies may be invalid or expired")
            await self.page.screenshot(path="debug_login_redirect.png")
            return reviews
        
        # Try multiple review selectors
        review_selectors = [
            '[data-hook="review"]',
            'div[id*="customer_review"]',
            '.review',
            'div.a-section.review'
        ]
        
        review_elements = []
        for selector in review_selectors:
            review_elements = await self.page.locator(selector).all()
            if review_elements:
                logger.info(f"Found {len(review_elements)} reviews using selector: {selector}")
                break
        
        if not review_elements:
            logger.warning("No review elements found on page")
            # Check if there's a "no reviews" message
            no_reviews_text = await self.page.locator('.no-reviews-section, [data-hook="noReviewsSection"]').count()
            if no_reviews_text > 0:
                logger.info("Product has no reviews yet")
            return reviews
        
        for element in review_elements:
            try:
                # Extract reviewer name
                reviewer_elem = element.locator('.a-profile-name')
                reviewer = await reviewer_elem.text_content() if await reviewer_elem.count() > 0 else "Anonymous"
                
                # Extract rating
                rating_elem = element.locator('[data-hook="review-star-rating"], [data-hook="cmps-review-star-rating"]')
                rating_text = await rating_elem.text_content() if await rating_elem.count() > 0 else ""
                rating = self._extract_rating_from_stars(rating_text)
                
                # Extract date
                date_elem = element.locator('[data-hook="review-date"]')
                date_text = await date_elem.text_content() if await date_elem.count() > 0 else ""
                date = self._clean_date(date_text)
                
                # Extract review content
                content_elem = element.locator('[data-hook="review-body"]')
                content = await content_elem.text_content() if await content_elem.count() > 0 else ""
                
                # Check for verified purchase
                verified_elem = element.locator('[data-hook="avp-badge"]')
                verified = await verified_elem.count() > 0
                
                # Extract helpful votes
                helpful_elem = element.locator('[data-hook="helpful-vote-statement"]')
                helpful_text = await helpful_elem.text_content() if await helpful_elem.count() > 0 else ""
                helpful_votes = self._extract_helpful_votes(helpful_text)
                
                review = Review(
                    product_id=asin,
                    product_title=product_title,
                    reviewer=reviewer.strip(),
                    rating=rating,
                    date=date,
                    verified_purchase=verified,
                    content=content.strip(),
                    helpful_votes=helpful_votes
                )
                
                reviews.append(review)
                
            except Exception as e:
                logger.warning(f"Error extracting individual review: {e}")
                continue
        
        return reviews
    
    def _extract_rating_from_stars(self, text: str) -> float:
        """Extract rating from star text"""
        if not text:
            return 0.0
        match = re.search(r'(\d+\.?\d*)\s+out of\s+5', text)
        if match:
            return float(match.group(1))
        # Alternative format
        match = re.search(r'(\d+\.?\d*)\s+stars?', text)
        return float(match.group(1)) if match else 0.0
    
    def _clean_date(self, date_text: str) -> str:
        """Clean and format date string"""
        if not date_text:
            return ""
        # Remove "Reviewed in" prefix
        date_text = re.sub(r'Reviewed in.*?on\s+', '', date_text)
        return date_text.strip()
    
    def _extract_helpful_votes(self, text: str) -> int:
        """Extract number of helpful votes"""
        if not text:
            return 0
        match = re.search(r'(\d+)\s+people?\s+found', text)
        return int(match.group(1)) if match else 0
    
    async def save_to_csv(self, filename: str = "amazon_reviews.csv"):
        """Save reviews to CSV file"""
        if not self.reviews:
            logger.warning("No reviews to save")
            return
        
        keys = ['product_id', 'product_title', 'reviewer', 'rating', 'date', 
                'verified_purchase', 'content', 'helpful_votes']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=keys)
            writer.writeheader()
            for review in self.reviews:
                writer.writerow(asdict(review))
        
        logger.info(f"Saved {len(self.reviews)} reviews to {filename}")
    
    async def save_to_json(self, filename: str = "amazon_reviews.json"):
        """Save reviews to JSON file"""
        if not self.reviews:
            logger.warning("No reviews to save")
            return
        
        data = {
            'scrape_date': datetime.now().isoformat(),
            'total_reviews': len(self.reviews),
            'reviews': [asdict(review) for review in self.reviews]
        }
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.reviews)} reviews to {filename}")
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
    
    async def run(self, keyword: str, star_filter: Optional[str] = None, 
                  max_products: int = 3, max_pages: int = 2):
        """Main execution method"""
        try:
            await self.initialize()
            
            # Search for products
            products = await self.search_products(keyword, max_products)
            
            if not products:
                logger.warning("No products found")
                return
            
            # Scrape reviews for each product
            for product in products:
                reviews = await self.scrape_reviews(product, star_filter, max_pages)
                self.reviews.extend(reviews)
                
                # Delay between products to avoid rate limiting
                await asyncio.sleep(3)
            
            # Save results
            await self.save_to_csv(f"reviews_{keyword.replace(' ', '_')}.csv")
            await self.save_to_json(f"reviews_{keyword.replace(' ', '_')}.json")
            
            logger.info(f"Total reviews collected: {len(self.reviews)}")
            
        finally:
            await self.close()


# Star filter options (moved to top for import)
STAR_FILTERS = {
    '5': 'five_star',
    '4': 'four_star',
    '3': 'three_star',
    '2': 'two_star',
    '1': 'one_star',
    'positive': 'positive',  # 4-5 stars
    'critical': 'critical'   # 1-3 stars
}
