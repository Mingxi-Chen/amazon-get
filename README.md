# Amazon Reviews Scraper

A robust Python tool for scraping product reviews from Amazon using Playwright. This scraper can extract reviews from multiple products based on search keywords, with support for various star rating filters and both manual and automated login methods.

## Features

- 🔍 **Product Search**: Search Amazon for products using keywords
- ⭐ **Star Filtering**: Filter reviews by star ratings (1-5 stars, positive, critical, or all)
- 📊 **Multiple Output Formats**: Save results as CSV and JSON
- 🔐 **Flexible Authentication**: Both manual and automated login options
- 🛡️ **Stealth Mode**: Advanced anti-detection measures to avoid blocking
- 📱 **Headless Support**: Run with or without browser GUI
- 🎯 **Configurable**: Customize number of products and pages to scrape
- 📝 **Detailed Logging**: Comprehensive logging for debugging and monitoring

## Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Setup

1. **Clone or download the project files**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## Quick Start

### 1. Extract Amazon Cookies (Required)

Before scraping, you need to extract cookies from a logged-in Amazon session:

#### Option A: Automated Login
```bash
python cookie_extractor.py --auto
```

#### Option B: Manual Login (Recommended)
```bash
python cookie_extractor.py
```

This will open a browser window where you can manually log in to Amazon. The script will save your session cookies to `amazon_cookies.json`.

### 2. Run the Scraper

#### Interactive Mode
```bash
python main.py --interactive
```

#### Command Line Mode
```bash
python main.py --keyword "laptop bag" --star-filter 5 --max-products 3
```

## Usage Examples

### Basic Usage
```bash
# Scrape all reviews for "wireless headphones"
python main.py --keyword "wireless headphones"

# Scrape only 5-star reviews for "laptop bag"
python main.py --keyword "laptop bag" --star-filter 5

# Scrape 5 products, 3 pages each, in headless mode
python main.py --keyword "bluetooth speaker" --max-products 5 --max-pages 3 --headless
```

### Advanced Usage
```bash
# Scrape positive reviews (4-5 stars) for multiple products
python main.py --keyword "gaming mouse" --star-filter positive --max-products 5 --max-pages 2

# Use custom cookies file
python main.py --keyword "mechanical keyboard" --cookies-file my_cookies.json
```

## Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keyword` | `-k` | Search keyword for products | Required |
| `--star-filter` | `-s` | Filter by star rating (1,2,3,4,5,positive,critical,all) | all |
| `--max-products` | `-p` | Maximum number of products to scrape | 3 |
| `--max-pages` | `-m` | Maximum pages per product | 2 |
| `--headless` | | Run browser in headless mode | False |
| `--cookies-file` | `-c` | Path to cookies file | amazon_cookies.json |
| `--interactive` | `-i` | Run in interactive mode | False |

## Star Filter Options

- `1` - Only 1-star reviews
- `2` - Only 2-star reviews  
- `3` - Only 3-star reviews
- `4` - Only 4-star reviews
- `5` - Only 5-star reviews
- `positive` - 4-5 star reviews
- `critical` - 1-3 star reviews
- `all` - All reviews (default)

## Output Files

The scraper generates two output files for each run:

### CSV Format (`reviews_[keyword].csv`)
```csv
product_id,product_title,reviewer,rating,date,verified_purchase,content,helpful_votes
B09JVG3TWX,Amazon Echo Buds...,KjandKt,5.0,July 20, 2025,true,"Fantastic sound...",35
```

### JSON Format (`reviews_[keyword].json`)
```json
{
  "scrape_date": "2025-09-16T18:14:59.091664",
  "total_reviews": 50,
  "reviews": [
    {
      "product_id": "B09JVG3TWX",
      "product_title": "Amazon Echo Buds...",
      "reviewer": "KjandKt",
      "rating": 5.0,
      "date": "July 20, 2025",
      "verified_purchase": true,
      "content": "Fantastic sound...",
      "helpful_votes": 35
    }
  ]
}
```

## Authentication Methods

### Method 1: Manual Login (Recommended)
```bash
python cookie_extractor.py
```
- Opens browser window
- Manually log in to Amazon
- Handles CAPTCHA and 2FA
- Saves cookies for future use

### Method 2: Automated Login
```bash
# Set environment variables
export AMAZON_EMAIL="your-email@example.com"
export AMAZON_PASSWORD="your-password"

# Run automated extraction
python cookie_extractor.py --auto
```

**Note**: Automated login may fail if Amazon requires CAPTCHA or 2FA. The script will automatically fall back to manual login.

## Configuration

### Environment Variables
Set these to avoid entering credentials repeatedly:
```bash
export AMAZON_EMAIL="your-email@example.com"
export AMAZON_PASSWORD="your-password"
```

### Custom Settings
You can modify default settings in the code:
- Browser arguments in `scrape.py`
- User agent strings
- Request delays and timeouts
- Output file naming patterns

## Troubleshooting

### Common Issues

**"Looking for Something? We're sorry..."**
- Amazon detected automated behavior
- Solution: Use manual login method or try again later

**"No products found"**
- Search keyword too specific or no results
- Solution: Try broader keywords or check Amazon directly

**"Could not verify login status"**
- Cookies may be expired or invalid
- Solution: Re-run cookie extraction

**"CAPTCHA detected"**
- Amazon requires human verification
- Solution: Complete CAPTCHA in browser, then press Enter

**"2FA detected"**
- Account has two-factor authentication enabled
- Solution: Complete 2FA in browser, then press Enter

### Debug Mode
The scraper automatically creates debug screenshots when issues occur:
- `debug_homepage_loaded_TIMESTAMP.png`
- `debug_reviews_page_TIMESTAMP.png`
- `debug_login_redirect_TIMESTAMP.png`

## File Structure

```
scrape-b/
├── main.py                 # Main entry point
├── scrape.py              # Core scraping logic
├── user_interface.py      # CLI and interactive input handling
├── cookie_extractor.py    # Authentication and cookie management
├── test_login.py          # Login testing script
├── example_usage.py       # Usage examples
├── requirements.txt       # Python dependencies
├── amazon_cookies.json    # Saved authentication cookies
├── reviews_*.csv          # Scraped data (CSV format)
├── reviews_*.json         # Scraped data (JSON format)
└── debug_*.png           # Debug screenshots
```

## Dependencies

- `playwright` - Browser automation
- `asyncio` - Asynchronous programming
- `dataclasses` - Data structure handling
- `json` - JSON file handling
- `csv` - CSV file handling
- `logging` - Logging functionality

## Legal and Ethical Considerations

⚠️ **Important**: This tool is for educational and research purposes only. Please ensure you:

1. **Respect Amazon's Terms of Service**
2. **Don't overload their servers** - Use reasonable delays between requests
3. **Follow robots.txt guidelines**
4. **Use data responsibly** - Don't redistribute scraped content
5. **Respect user privacy** - Don't misuse personal information from reviews

## Rate Limiting

The scraper includes built-in delays to be respectful:
- 2-3 second delays between page requests
- 3 second delays between products
- Automatic retry logic for failed requests

## Contributing

Feel free to submit issues and enhancement requests! Areas for improvement:
- Additional output formats
- More robust error handling
- Support for other Amazon domains
- Enhanced anti-detection measures

## License

This project is for educational purposes. Please use responsibly and in accordance with Amazon's Terms of Service.

## Support

If you encounter issues:
1. Check the debug screenshots
2. Review the console logs
3. Try manual login method
4. Ensure cookies are valid and not expired
5. Check your internet connection

---

**Happy Scraping! 🕷️**
