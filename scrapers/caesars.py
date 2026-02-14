from playwright.sync_api import sync_playwright
import time
import sys

def scrape_caesars():
    """
    Scrapes Caesars Sportsbook for PGA hole scores.
    Uses better headers to attempt bypass.
    """
    print("Attempting to scrape Caesars...", file=sys.stderr)
    data = []

    with sync_playwright() as p:
        # Launch with realistic args
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized'
        ])

        # New context with user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="en-US"
        )

        try:
            page = context.new_page()
            url = "https://sportsbook.caesars.com/us/nj/bet/golf"
            print(f"Navigating to {url}", file=sys.stderr)

            # Add extra headers
            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
            })

            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Small random wait
            time.sleep(2)

            # Check for bot protection or access denied
            title = page.title()
            print(f"Caesars Title: {title}", file=sys.stderr)

            if "Access Denied" in title or "MARKETS NOT AVAILABLE" in page.content() or "Incapsula" in title:
                print("Caesars access restricted or blocked.", file=sys.stderr)
                # Still try to screenshot
                try:
                    page.screenshot(path="caesars_fail.png")
                except:
                    pass
            else:
                # If successful, logic would go here.
                # For now, just try to extract basic golf text
                text = page.inner_text("body")
                # Look for "Hole Score" or player names if we got lucky
                if "Hole Score" in text:
                    print("Found Hole Score on Caesars!", file=sys.stderr)
                else:
                    print("No Hole Score text found on Caesars page.", file=sys.stderr)

        except Exception as e:
            print(f"Error scraping Caesars: {e}", file=sys.stderr)
        finally:
            browser.close()

    if not data:
        print("Warning: No data found for Caesars.", file=sys.stderr)

    return data
