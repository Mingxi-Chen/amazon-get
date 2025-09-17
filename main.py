"""
Main entry point for Amazon Reviews Scraper
"""

import asyncio
from scrape import AmazonReviewsScraper, STAR_FILTERS
from user_interface import UserInterface


async def main():
    """Main function with user input handling"""
    # Get configuration from user
    config = UserInterface.get_configuration()
    
    # Display configuration
    UserInterface.display_configuration(config)
    
    # Create scraper instance
    scraper = AmazonReviewsScraper(
        headless=config['headless'], 
        cookies_file=config['cookies_file']
    )
    
    # Convert star filter
    star_param = None
    if config['star_filter'] and config['star_filter'] in STAR_FILTERS:
        star_param = STAR_FILTERS[config['star_filter']]
    
    # Run scraper
    await scraper.run(
        keyword=config['keyword'],
        star_filter=star_param,
        max_products=config['max_products'],
        max_pages=config['max_pages']
    )


if __name__ == "__main__":
    asyncio.run(main())
