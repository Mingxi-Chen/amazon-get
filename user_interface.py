"""
User Interface Module for Amazon Reviews Scraper
Handles command-line arguments and interactive input
"""

import argparse
import sys
from typing import Dict, Optional


# Star filter options (imported from scrape.py)
STAR_FILTERS = {
    '5': 'five_star',
    '4': 'four_star',
    '3': 'three_star',
    '2': 'two_star',
    '1': 'one_star',
    'positive': 'positive',  # 4-5 stars
    'critical': 'critical'   # 1-3 stars
}


class UserInterface:
    """Handles user input for scraper configuration"""
    
    @staticmethod
    def get_interactive_input() -> Dict:
        """Get parameters from user input interactively"""
        print("=== Amazon Reviews Scraper ===")
        print()
        
        # Get keyword
        keyword = input("Enter search keyword (e.g., 'laptop bag'): ").strip()
        if not keyword:
            print("Error: Keyword cannot be empty")
            sys.exit(1)
        
        # Get star filter
        print("\nStar filter options:")
        print("  5 - Only 5-star reviews")
        print("  4 - Only 4-star reviews") 
        print("  3 - Only 3-star reviews")
        print("  2 - Only 2-star reviews")
        print("  1 - Only 1-star reviews")
        print("  positive - 4-5 star reviews")
        print("  critical - 1-3 star reviews")
        print("  all - All reviews (default)")
        
        star_filter = input("Enter star filter (press Enter for 'all'): ").strip().lower()
        if star_filter == 'all' or not star_filter:
            star_filter = None
        elif star_filter not in STAR_FILTERS:
            print(f"Warning: Invalid star filter '{star_filter}'. Using 'all' instead.")
            star_filter = None
        
        # Get max products
        max_products = UserInterface._get_positive_int(
            "Enter max number of products to scrape (default: 3): ", 
            default=3
        )
        
        # Get max pages
        max_pages = UserInterface._get_positive_int(
            "Enter max pages per product (default: 2): ", 
            default=2
        )
        
        # Get headless mode
        headless_input = input("Run in headless mode? (y/n, default: n): ").strip().lower()
        headless = headless_input in ['y', 'yes', '1', 'true']
        
        # Get cookies file
        cookies_file = input("Enter path to cookies file (default: amazon_cookies.json): ").strip()
        if not cookies_file:
            cookies_file = "amazon_cookies.json"
        
        return {
            'keyword': keyword,
            'star_filter': star_filter,
            'max_products': max_products,
            'max_pages': max_pages,
            'headless': headless,
            'cookies_file': cookies_file
        }
    
    @staticmethod
    def _get_positive_int(prompt: str, default: int) -> int:
        """Get a positive integer from user input with validation"""
        while True:
            try:
                value = input(prompt).strip()
                if not value:
                    return default
                value = int(value)
                if value <= 0:
                    print("Error: Value must be greater than 0")
                    continue
                return value
            except ValueError:
                print("Error: Please enter a valid number")
    
    @staticmethod
    def parse_command_line() -> argparse.Namespace:
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(
            description='Amazon Reviews Scraper',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python main.py --interactive
  python main.py --keyword "laptop bag" --star-filter 5 --max-products 5
  python main.py -k "wireless mouse" -s positive -p 3 -m 2 --headless
            """
        )
        
        parser.add_argument('--keyword', '-k', type=str, help='Search keyword')
        parser.add_argument('--star-filter', '-s', type=str, 
                          choices=list(STAR_FILTERS.keys()) + ['all'], 
                          help='Star filter (5, 4, 3, 2, 1, positive, critical, all)')
        parser.add_argument('--max-products', '-p', type=int, default=3, 
                          help='Max products to scrape (default: 3)')
        parser.add_argument('--max-pages', '-m', type=int, default=2, 
                          help='Max pages per product (default: 2)')
        parser.add_argument('--headless', action='store_true', 
                          help='Run in headless mode')
        parser.add_argument('--cookies-file', '-c', type=str, default='amazon_cookies.json', 
                          help='Path to cookies file (default: amazon_cookies.json)')
        parser.add_argument('--interactive', '-i', action='store_true', 
                          help='Run in interactive mode (prompt for inputs)')
        
        return parser.parse_args()
    
    @staticmethod
    def get_configuration() -> Dict:
        """Get configuration from command line or interactive input"""
        args = UserInterface.parse_command_line()
        
        # If interactive mode or no keyword provided, get user input
        if args.interactive or not args.keyword:
            return UserInterface.get_interactive_input()
        else:
            # Validate command line arguments
            if args.max_products <= 0:
                print("Error: --max-products must be greater than 0")
                sys.exit(1)
            if args.max_pages <= 0:
                print("Error: --max-pages must be greater than 0")
                sys.exit(1)
            
            # Use command line arguments
            return {
                'keyword': args.keyword,
                'star_filter': args.star_filter if args.star_filter != 'all' else None,
                'max_products': args.max_products,
                'max_pages': args.max_pages,
                'headless': args.headless,
                'cookies_file': args.cookies_file
            }
    
    @staticmethod
    def display_configuration(config: Dict) -> None:
        """Display the current configuration"""
        print(f"\n=== Configuration ===")
        print(f"Keyword: {config['keyword']}")
        print(f"Star filter: {config['star_filter'] or 'all'}")
        print(f"Max products: {config['max_products']}")
        print(f"Max pages per product: {config['max_pages']}")
        print(f"Headless mode: {config['headless']}")
        print(f"Cookies file: {config['cookies_file']}")
        print()
