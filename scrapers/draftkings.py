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

    # Regex for header: "Daniel Berger Hole Score - Hole 10 - Round 3"
    header_pattern = re.compile(r"(.+?) Hole Score - Hole (\d+) - Round (\d+)")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = header_pattern.match(line)

        if match:
            # If we were processing a previous player, save it
            if current_player and current_odds:
                data.append({
                    "player": current_player,
                    "hole": current_hole,
                    "round": current_round,
                    "odds": current_odds,
                    "book": "DraftKings"
                })
                current_odds = {}

            current_player = match.group(1).strip()
            current_hole = match.group(2)
            current_round = match.group(3)
            i += 1
            continue

        if current_player:
            # Look for odds lines
            if line in ["Par", "Bogey or Worse", "Birdie or Better"]:
                market_type = line
                if i + 1 < len(lines):
                    odds_value = lines[i+1].strip()
                    # Normalize minus sign
                    odds_value = odds_value.replace("−", "-")
                    current_odds[market_type] = odds_value
                    i += 1 # Skip odds value line

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

    Args:
        url (str, optional): The URL to scrape. Defaults to a known tournament URL.
    """
    if url is None:
        url = "https://sportsbook.draftkings.com/leagues/golf/at%2526t-pebble-beach-pro-am"

    data = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to {url}")

        try:
            page.goto(url, timeout=60000)

            # Click HOLE tab
            # Wait for tab to be visible
            try:
                page.wait_for_selector("text=HOLE", timeout=10000)
                page.click("text=HOLE")
                print("Clicked HOLE tab")
                time.sleep(5) # Wait for content
            except Exception as e:
                print(f"Error clicking HOLE tab: {e}")
                browser.close()
                return []

            # Click "2 Ball Player Hole Score" accordion if needed
            # We assume it exists based on exploration
            try:
                # Check if it's already expanded? Hard to tell. Just click it.
                # Usually text is visible.
                page.wait_for_selector("text=2 Ball Player Hole Score", timeout=5000)
                page.click("text=2 Ball Player Hole Score")
                print("Clicked '2 Ball Player Hole Score'")
                time.sleep(3)
            except Exception as e:
                print(f"Warning: '2 Ball Player Hole Score' not found or clickable: {e}")
                # Maybe continue anyway, as other content might be visible

            # Extract text
            text = page.inner_text("body")

            # Parse
            data = parse_dk_odds(text)
            print(f"Extracted {len(data)} hole scores from DraftKings")

        except Exception as e:
            print(f"Error during DraftKings scrape: {e}")

        browser.close()

    return data

if __name__ == "__main__":
    import json
    odds = scrape_dk()
    print(json.dumps(odds, indent=2))
