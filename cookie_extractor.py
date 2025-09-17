"""
Amazon Cookie Extraction Helper
This script helps you extract and save cookies from Amazon with both manual and automated login options
"""

import asyncio
import json
import getpass
import os
from playwright.async_api import async_playwright
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_page_state(page, step_name):
    """Debug helper to capture page state for troubleshooting"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        debug_filename = f"debug_{step_name}_{timestamp}.png"
        
        logger.info(f"🐛 Debug: {step_name}")
        logger.info(f"Current URL: {page.url}")
        logger.info(f"Page title: {await page.title()}")
        
        # Take screenshot for debugging
        await page.screenshot(path=debug_filename)
        logger.info(f"Screenshot saved: {debug_filename}")
        
        # Check for common error indicators
        error_indicators = [
            "sorry", "error", "not found", "blocked", "captcha", 
            "verification", "unusual activity", "try again"
        ]
        
        page_content = await page.content()
        page_text = page_content.lower()
        
        for indicator in error_indicators:
            if indicator in page_text:
                logger.warning(f"⚠️ Detected '{indicator}' in page content")
                
    except Exception as e:
        logger.error(f"Debug function failed: {e}")


def get_credentials():
    """
    Get Amazon login credentials from user input or environment variables
    """
    # Check for environment variables first
    email = os.getenv('AMAZON_EMAIL')
    password = os.getenv('AMAZON_PASSWORD')
    
    if email and password:
        logger.info("Using credentials from environment variables")
        return email, password
    
    print("\n" + "="*60)
    print("AMAZON LOGIN CREDENTIALS")
    print("You can set AMAZON_EMAIL and AMAZON_PASSWORD environment variables")
    print("to avoid entering credentials each time.")
    print("="*60 + "\n")
    
    email = input("Enter your Amazon email/phone: ").strip()
    password = getpass.getpass("Enter your Amazon password: ").strip()
    
    if not email or not password:
        raise ValueError("Email and password are required")
    
    return email, password


async def automated_login(page, email, password):
    """
    Attempt automated login to Amazon with improved error handling
    Returns True if successful, False if manual intervention needed
    """
    try:
        logger.info("Attempting automated login...")
        
        # First navigate to Amazon homepage to establish session
        logger.info("Establishing session with Amazon...")
        await page.goto("https://www.amazon.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Debug: Check homepage state
        await debug_page_state(page, "homepage_loaded")
        
        # Check if page loaded correctly
        page_title = await page.title()
        if "sorry" in page_title.lower() or "error" in page_title.lower():
            logger.warning(f"Amazon homepage returned an error page: {page_title}")
            await debug_page_state(page, "homepage_error")
            return False
        
        # Look for sign-in link and click it
        try:
            # Try multiple selectors for sign-in
            sign_in_selectors = [
                "#nav-link-accountList",
                "a[href*='signin']",
                "#nav-signin-tooltip a",
                ".nav-signin-tooltip a"
            ]
            
            sign_in_clicked = False
            for selector in sign_in_selectors:
                try:
                    sign_in_element = page.locator(selector).first
                    if await sign_in_element.is_visible():
                        logger.info(f"Clicking sign-in link: {selector}")
                        await sign_in_element.click()
                        await page.wait_for_timeout(3000)
                        sign_in_clicked = True
                        break
                except:
                    continue
            
            if not sign_in_clicked:
                # Fallback: navigate directly to sign-in page
                logger.info("Fallback: navigating directly to sign-in page")
                await page.goto("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=usflex&openid.mode=checkid_setup&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&", wait_until="domcontentloaded")
                await page.wait_for_timeout(3000)
                await debug_page_state(page, "signin_page_direct")
            
        except Exception as e:
            logger.warning(f"Error navigating to sign-in: {e}")
            return False
        
        # Check if we're on a sign-in page
        current_url = page.url
        if "signin" not in current_url and "ap/" not in current_url:
            logger.warning(f"Not on sign-in page. Current URL: {current_url}")
            await debug_page_state(page, "not_signin_page")
            return False
        
        # Enter email/phone with multiple selector attempts
        email_selectors = ["#ap_email", "input[name='email']", "input[type='email']", "#ap_email_login"]
        email_entered = False
        
        for selector in email_selectors:
            try:
                email_input = page.locator(selector)
                if await email_input.is_visible():
                    logger.info(f"Entering email using selector: {selector}")
                    await email_input.clear()
                    await email_input.fill(email)
                    email_entered = True
                    break
            except:
                continue
        
        if not email_entered:
            logger.warning("Could not find email input field")
            await debug_page_state(page, "email_field_not_found")
            return False
        
        # Click continue button
        continue_selectors = ["#continue", "input[id='continue']", "button[type='submit']"]
        continue_clicked = False
        
        for selector in continue_selectors:
            try:
                continue_btn = page.locator(selector)
                if await continue_btn.is_visible():
                    logger.info(f"Clicking continue button: {selector}")
                    await continue_btn.click()
                    await page.wait_for_timeout(3000)
                    continue_clicked = True
                    break
            except:
                continue
        
        if not continue_clicked:
            logger.warning("Could not find continue button")
            return False
        
        # Enter password with multiple selector attempts
        password_selectors = ["#ap_password", "input[name='password']", "input[type='password']"]
        password_entered = False
        
        await page.wait_for_timeout(2000)  # Wait for password field to appear
        
        for selector in password_selectors:
            try:
                password_input = page.locator(selector)
                if await password_input.is_visible():
                    logger.info(f"Entering password using selector: {selector}")
                    await password_input.clear()
                    await password_input.fill(password)
                    password_entered = True
                    break
            except:
                continue
        
        if not password_entered:
            logger.warning("Could not find password input field")
            return False
        
        # Click sign-in button
        signin_selectors = ["#signInSubmit", "input[id='signInSubmit']", "button[type='submit']", "#auth-signin-button"]
        signin_clicked = False
        
        for selector in signin_selectors:
            try:
                signin_btn = page.locator(selector)
                if await signin_btn.is_visible():
                    logger.info(f"Clicking sign-in button: {selector}")
                    await signin_btn.click()
                    await page.wait_for_timeout(5000)  # Wait longer for login processing
                    signin_clicked = True
                    break
            except:
                continue
        
        if not signin_clicked:
            logger.warning("Could not find sign-in button")
            return False
        
        # Check for various challenges and errors
        await page.wait_for_timeout(3000)
        
        # Check for CAPTCHA
        captcha_selectors = [
            "#auth-captcha-image", 
            "[name='cvf_captcha_input']",
            ".cvf-captcha-img",
            "#captchacharacters"
        ]
        
        for selector in captcha_selectors:
            if await page.locator(selector).is_visible():
                logger.warning("CAPTCHA detected - requires manual intervention")
                return False
        
        # Check for 2FA
        twofa_selectors = [
            "#auth-mfa-form",
            "[name='otpCode']",
            "#auth-mfa-otpcode",
            ".cvf-challenge-form"
        ]
        
        for selector in twofa_selectors:
            if await page.locator(selector).is_visible():
                logger.warning("2FA detected - requires manual intervention")
                return False
        
        # Check for error messages
        error_selectors = [
            ".a-alert-error",
            "#auth-error-message-box",
            ".auth-error-message"
        ]
        
        for selector in error_selectors:
            if await page.locator(selector).is_visible():
                error_text = await page.locator(selector).text_content()
                logger.warning(f"Login error detected: {error_text}")
                return False
        
        # Check if we're successfully logged in
        await page.wait_for_timeout(3000)
        
        # Try to navigate to homepage to verify login
        await page.goto("https://www.amazon.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Check for account menu indicators
        account_selectors = [
            "#nav-link-accountList-nav-line-1",
            "#nav-link-accountList span",
            ".nav-line-1"
        ]
        
        for selector in account_selectors:
            try:
                account_element = page.locator(selector)
                if await account_element.is_visible():
                    account_text = await account_element.text_content()
                    if account_text and ("Hello" in account_text or "Hi" in account_text):
                        logger.info(f"✅ Automated login successful: {account_text}")
                        return True
            except:
                continue
        
        logger.warning("Login status unclear - may need manual verification")
        return False
        
    except Exception as e:
        logger.error(f"Automated login failed: {e}")
        return False


async def extract_amazon_cookies(auto_login=False):
    """
    Extract Amazon cookies with optional automated login
    
    Args:
        auto_login (bool): If True, attempt automated login using credentials
    """
    email, password = None, None
    
    if auto_login:
        try:
            email, password = get_credentials()
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            auto_login = False
    
    async with async_playwright() as p:
        # Launch browser with stealth configuration
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--start-maximized',
                '--no-first-run',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',  # Faster loading
                '--disable-javascript-harmony-shipping',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        # Create context with realistic browser fingerprint
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Sec-Fetch-Dest': 'document'
            }
        )
        
        # Add stealth scripts to avoid detection
        await context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            
            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mock platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'MacIntel',
            });
        """)
        
        page = await context.new_page()
        
        login_successful = False
        
        if auto_login and email and password:
            login_successful = await automated_login(page, email, password)
            
        if not login_successful:
            logger.info("Falling back to manual login...")
            await page.goto("https://www.amazon.com", wait_until="domcontentloaded")
            
            print("\n" + "="*60)
            print("MANUAL LOGIN REQUIRED:")
            if auto_login:
                print("Automated login failed - please complete login manually")
            print("1. Sign in to your Amazon account in the browser window")
            print("2. Complete any CAPTCHA if required")
            print("3. Handle 2FA if prompted")
            print("4. Make sure you're fully logged in")
            print("5. Press Enter in this terminal when ready...")
            print("="*60 + "\n")
            
            input("Press Enter after you've logged in successfully...")
        
        # Get cookies
        cookies = await context.cookies()
        
        # Save cookies to file
        with open("amazon_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        
        logger.info(f"Saved {len(cookies)} cookies to amazon_cookies.json")
        
        # Test if we're logged in by checking for account element
        try:
            account_element = await page.locator("#nav-link-accountList-nav-line-1").text_content()
            if account_element and "Hello" in account_element:
                logger.info(f"Successfully logged in as: {account_element}")
            else:
                logger.warning("Could not verify login status")
        except Exception as e:
            logger.warning(f"Could not verify login status: {e}")
        
        # Navigate to a product review page to test
        test_url = "https://www.amazon.com/product-reviews/B00DUGZFWY/"
        logger.info(f"Testing review page access: {test_url}")
        try:
            await page.goto(test_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Check if we can see reviews
            if await page.locator('[data-hook="review"]').count() > 0:
                logger.info("✅ Successfully accessed review page with cookies!")
            else:
                logger.warning("⚠️ Could not find reviews - may need additional steps")
        except Exception as e:
            logger.warning(f"Could not test review page access: {e}")
            
        await browser.close()
        print("\nCookie extraction complete! You can now use 'amazon_cookies.json' with the main scraper.")


def main():
    """Main function with command line argument handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Amazon cookies with optional automated login")
    parser.add_argument("--auto", action="store_true", 
                       help="Attempt automated login using credentials")
    parser.add_argument("--manual", action="store_true", 
                       help="Force manual login (default)")
    
    args = parser.parse_args()
    
    # Default to manual login unless --auto is specified
    auto_login = args.auto and not args.manual
    
    if auto_login:
        print("🤖 Automated login mode selected")
        print("You can set environment variables:")
        print("  export AMAZON_EMAIL='your-email@example.com'")
        print("  export AMAZON_PASSWORD='your-password'")
        print("Or you'll be prompted for credentials.\n")
    else:
        print("👤 Manual login mode selected")
        print("Use --auto flag for automated login attempt.\n")
    
    asyncio.run(extract_amazon_cookies(auto_login=auto_login))


if __name__ == "__main__":
    main()