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
    # Sometimes it might just be "Hole Score - Hole 10 - Round 3" without player name? No, usually has player.
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
            try:
                page.wait_for_selector("text=HOLE", timeout=10000)
                page.click("text=HOLE")
                print("Clicked HOLE tab")
                time.sleep(5)
            except Exception as e:
                print(f"Error clicking HOLE tab: {e}")
                browser.close()
                return []

            # Look for any accordion containing "Hole Score"
            # This covers "2 Ball Player Hole Score", "3 Ball Player Hole Score", etc.
            accordions = page.query_selector_all(".sportsbook-event-accordion__title")
            clicked_count = 0

            for acc in accordions:
                text = acc.inner_text()
                if "Hole Score" in text:
                    print(f"Found accordion: {text}")
                    # Check if likely already open or needs clicking. Just click to be safe?
                    # Or check class.
                    # Let's try to click it.
                    try:
                        acc.click()
                        clicked_count += 1
                        time.sleep(1)
                    except Exception as e:
                        print(f"Failed to click accordion {text}: {e}")

            if clicked_count == 0:
                print("No specific 'Hole Score' accordions found via class. Trying text search fallback.")
                # Fallback: Try specific texts
                targets = ["2 Ball Player Hole Score", "3 Ball Player Hole Score"]
                for t in targets:
                    try:
                        if page.is_visible(f"text={t}"):
                            page.click(f"text={t}")
                            print(f"Clicked '{t}'")
                            time.sleep(2)
                    except Exception:
                        pass

            # Wait a bit for expansions
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
