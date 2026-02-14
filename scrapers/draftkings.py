import re
import time
from playwright.sync_api import sync_playwright

def parse_dk_odds(text):
    """
    Parses the raw text from DraftKings page to extract hole score odds.
    """
    lines = text.split('\n')
    data = []

    current_player = None
    current_hole = None
    current_round = None
    current_odds = {}

    # Header pattern: "Name Hole Score - Hole X - Round Y"
    # Example: "Daniel Berger Hole Score - Hole 10 - Round 3"
    header_pattern = re.compile(r"(.+?) Hole Score - Hole (\d+) - Round (\d+)")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = header_pattern.match(line)

        if match:
            # Save previous if complete-ish (has at least one odd)
            if current_player and current_odds:
                data.append({
                    "player": current_player,
                    "hole": current_hole,
                    "round": current_round,
                    "odds": current_odds.copy(),
                    "book": "DraftKings"
                })
                current_odds = {}

            current_player = match.group(1).strip()
            current_hole = match.group(2)
            current_round = match.group(3)
            i += 1
            continue

        if current_player:
            if line in ["Par", "Bogey or Worse", "Birdie or Better"]:
                market_type = line
                if i + 1 < len(lines):
                    odds_value = lines[i+1].strip()
                    # Normalize minus sign
                    odds_value = odds_value.replace("−", "-")
                    current_odds[market_type] = odds_value
                    i += 1

        i += 1

    # Append the last one
    if current_player and current_odds:
        data.append({
            "player": current_player,
            "hole": current_hole,
            "round": current_round,
            "odds": current_odds,
            "book": "DraftKings"
        })

    return data

def scrape_dk(url=None):
    """
    Scrapes DraftKings for PGA hole scores.
    """
    if url is None:
        url = "https://sportsbook.draftkings.com/leagues/golf/at%2526t-pebble-beach-pro-am"

    data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a realistic user agent
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()
        print(f"Navigating to {url}")

        try:
            page.goto(url, timeout=60000)

            # Click HOLE tab
            try:
                page.wait_for_selector("text=HOLE", timeout=10000)
                page.click("text=HOLE")
                print("Clicked HOLE tab")
                time.sleep(5)
            except Exception as e:
                print(f"Error clicking HOLE tab: {e}")
                browser.close()
                return []

            # Scroll down to ensure content loads
            print("Scrolling page...")
            for _ in range(5):
                page.mouse.wheel(0, 1000)
                time.sleep(1)

            # Click "2 Ball Player Hole Score" and "3 Ball Player Hole Score"
            # It seems the class selector was failing, so rely on text.
            targets = ["2 Ball Player Hole Score", "3 Ball Player Hole Score"]
            for t in targets:
                try:
                    # Find elements by text
                    # We iterate because sometimes there are multiple matches (e.g. mobile view hidden vs desktop)
                    elements = page.get_by_text(t).all()
                    for el in elements:
                        if el.is_visible():
                            try:
                                el.scroll_into_view_if_needed()
                                el.click(timeout=2000)
                                print(f"Clicked '{t}'")
                                time.sleep(2) # Wait for expansion
                            except Exception:
                                pass
                except Exception:
                    pass

            # Wait a bit for expansions and data load
            time.sleep(3)

            # Extract text
            text = page.inner_text("body")

            # Parse
            data = parse_dk_odds(text)
            print(f"Extracted {len(data)} hole scores from DraftKings")

        except Exception as e:
            print(f"Error during DraftKings scrape: {e}")

        browser.close()

    return data
