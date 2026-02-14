from playwright.sync_api import sync_playwright
import time
import sys

def scrape_fanduel():
    """
    Scrapes FanDuel Sportsbook for PGA hole scores.
    Uses better headers to attempt bypass.
    """
    print("Attempting to scrape FanDuel...", file=sys.stderr)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=[
            '--disable-blink-features=AutomationControlled',
            '--start-maximized'
        ])

        # New context with user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale="en-US"
        )

        try:
            page = context.new_page()
            url = "https://sportsbook.fanduel.com/navigation/golf"
            print(f"Navigating to {url}", file=sys.stderr)

            page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
            })

            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Small random wait
            time.sleep(2)

            # Check for bot protection or access denied
            title = page.title()
            print(f"FanDuel Title: {title}", file=sys.stderr)

            if "Access to this page has been denied" in title or "human" in page.content().lower() or "Incapsula" in title:
                print("FanDuel access restricted due to bot protection.", file=sys.stderr)
                # Still try to screenshot
                try:
                    page.screenshot(path="fanduel_fail.png")
                except:
                    pass
            else:
                # If successful, logic would go here.
                # Look for "Hole Score" or player names if we got lucky
                text = page.inner_text("body")
                if "Hole Score" in text:
                    print("Found Hole Score on FanDuel!", file=sys.stderr)
                else:
                    print("No Hole Score text found on FanDuel page.", file=sys.stderr)

        except Exception as e:
            print(f"Error scraping FanDuel: {e}", file=sys.stderr)
        finally:
            browser.close()

    if not data:
        print("Warning: No data found for FanDuel.", file=sys.stderr)

    return data
