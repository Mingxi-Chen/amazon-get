# Amazon Cookie Extractor - Usage Guide

The `cookie_extractor.py` script now supports both **manual** and **automated** login methods for extracting Amazon cookies.

## Quick Start

### Method 1: Command Line Usage

**Automated Login:**
```bash
python cookie_extractor.py --auto
```

**Manual Login (default):**
```bash
python cookie_extractor.py
# or explicitly:
python cookie_extractor.py --manual
```

### Method 2: Environment Variables (Recommended for Automation)

Set your credentials as environment variables to avoid entering them each time:

```bash
export AMAZON_EMAIL="your-email@example.com"
export AMAZON_PASSWORD="your-password"
python cookie_extractor.py --auto
```

### Method 3: Programmatic Usage

```python
import asyncio
from cookie_extractor import extract_amazon_cookies

# Automated login
await extract_amazon_cookies(auto_login=True)

# Manual login
await extract_amazon_cookies(auto_login=False)
```

## Features

### ✅ Automated Login
- Automatically fills in email/phone and password
- Handles Amazon's multi-step login process
- Detects and handles common challenges:
  - CAPTCHA detection (falls back to manual)
  - 2FA detection (falls back to manual)
  - Various login form variations

### ✅ Secure Credential Handling
- Environment variable support (`AMAZON_EMAIL`, `AMAZON_PASSWORD`)
- Secure password input using `getpass` (password hidden)
- No credential storage in code or files

### ✅ Robust Error Handling
- Automatic fallback to manual login if automation fails
- Detailed logging of login attempts and issues
- Graceful handling of network timeouts and page load issues

### ✅ Login Verification
- Verifies successful login by checking account elements
- Tests cookie functionality on actual review pages
- Provides clear success/failure feedback

## Common Scenarios

### Scenario 1: First Time Setup
```bash
# Try automated login first
python cookie_extractor.py --auto
# Enter credentials when prompted
# If CAPTCHA appears, complete it manually and press Enter
```

### Scenario 2: Automated Workflow
```bash
# Set environment variables once
export AMAZON_EMAIL="your-email@example.com"
export AMAZON_PASSWORD="your-password"

# Run automated extraction
python cookie_extractor.py --auto
```

### Scenario 3: Accounts with 2FA
```bash
# Automated login will detect 2FA and fall back to manual
python cookie_extractor.py --auto
# Complete 2FA in the browser, then press Enter
```

### Scenario 4: CAPTCHA Required
```bash
# If CAPTCHA is detected, you'll be prompted to solve it manually
python cookie_extractor.py --auto
# Solve CAPTCHA in browser, then press Enter
```

## Security Notes

⚠️ **Important Security Considerations:**

1. **Environment Variables**: Store credentials in environment variables, not in code
2. **Temporary Credentials**: Consider using temporary/app-specific passwords if available
3. **Network Security**: Run on trusted networks only
4. **Cookie Security**: The generated `amazon_cookies.json` contains sensitive session data

## Troubleshooting

### Issue: "Looking for Something? We're sorry. The Web address you entered is not a functioning page on our site"
- **Cause**: Amazon detected automated behavior or blocked the request
- **Solution**: The script now includes enhanced stealth features and better error handling. Try running again, or use manual login as fallback.

### Issue: "Automated login failed"
- **Solution**: Amazon may require CAPTCHA or 2FA. The script will automatically fall back to manual login.

### Issue: "Could not verify login status"
- **Solution**: Check if you're actually logged in by looking at the browser. Press Enter to continue.

### Issue: "CAPTCHA detected"
- **Solution**: Complete the CAPTCHA in the browser window, then press Enter in the terminal.

### Issue: "2FA detected" 
- **Solution**: Complete two-factor authentication in the browser, then press Enter.

### Issue: Environment variables not working
- **Solution**: Make sure to export variables in the same terminal session:
  ```bash
  export AMAZON_EMAIL="your-email"
  export AMAZON_PASSWORD="your-password"
  python cookie_extractor.py --auto
  ```

### Debug Mode
If you encounter issues, the script now automatically creates debug screenshots:
- `debug_homepage_loaded_TIMESTAMP.png` - Shows the Amazon homepage
- `debug_signin_page_direct_TIMESTAMP.png` - Shows the sign-in page
- `debug_email_field_not_found_TIMESTAMP.png` - Shows issues finding email field

These screenshots help identify what Amazon is showing and troubleshoot login issues.

## Output

The script generates:
- `amazon_cookies.json`: Contains all Amazon session cookies
- Console logs showing the login process and verification results
- Success confirmation with account information

## Integration with Main Scraper

The extracted cookies work seamlessly with the main scraper:

```python
# In your scraping code
scraper = AmazonReviewsScraper(
    headless=True, 
    cookies_file="amazon_cookies.json"  # Use the extracted cookies
)
```
