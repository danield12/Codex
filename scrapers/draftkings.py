import re
import time
from playwright.sync_api import sync_playwright

def extract_pin_data(card_element):
    """
    Extracts pin coordinates (x, y) relative to the green container from a card element.
    Returns a dictionary {'x': float, 'y': float} or None if not found.
    """
    try:
        return card_element.evaluate("""(element) => {
            function isPin(el) {
                const style = window.getComputedStyle(el);
                const w = parseFloat(style.width);
                const h = parseFloat(style.height);
                const r = style.borderRadius;
                const bg = style.backgroundColor;

                // Check size (e.g. 4px to 20px)
                if (w >= 4 && w <= 20 && h >= 4 && h <= 20) {
                    // simplistic check for circle
                    if (r.includes('50%') || parseFloat(r) >= w/2 - 1) {
                        // check color - red(ish) or black(ish)
                        if (bg.includes('rgb(255, 0, 0)') || bg.includes('rgb(0, 0, 0)') || bg === 'red' || bg === 'black') {
                            return true;
                        }
                    }
                }
                return false;
            }

            // Traverse to find pin
            const allEls = element.querySelectorAll('*');
            let pinEl = null;
            for (const el of allEls) {
                if (isPin(el)) {
                    pinEl = el;
                    break;
                }
            }

            if (!pinEl) return null;

            // Parent is green
            const greenEl = pinEl.parentElement;
            const greenRect = greenEl.getBoundingClientRect();
            const pinRect = pinEl.getBoundingClientRect();

            // Calculate relative center
            const pinCenterX = pinRect.left + pinRect.width / 2;
            const pinCenterY = pinRect.top + pinRect.height / 2;

            if (greenRect.width === 0 || greenRect.height === 0) return null;

            const relX = (pinCenterX - greenRect.left) / greenRect.width;
            const relY = (pinCenterY - greenRect.top) / greenRect.height;

            return { x: relX, y: relY };
        }""")
    except Exception as e:
        print(f"Error extracting pin data: {e}")
        return None

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

            # Extract data by traversing cards
            print("Extracting card data...")
            header_pattern_re = re.compile(r"(.+?) Hole Score - Hole (\d+) - Round (\d+)")

            # Find all elements that match the header pattern
            # We use get_by_text with regex, then iterate to find the container
            header_elements = page.get_by_text(header_pattern_re).all()
            print(f"Found {len(header_elements)} potential card headers")

            processed_ids = set() # To avoid duplicates if multiple headers point to same card

            for header_el in header_elements:
                try:
                    if not header_el.is_visible():
                        continue

                    # Traverse up to find the card container.
                    # We assume the card container contains "Par" (one of the outcomes).
                    # We'll go up a few levels.
                    card_container = None
                    current = header_el
                    # Try going up a few levels to find a container that has "Par"
                    # We limit depth to avoid going to body
                    for _ in range(5):
                        parent = current.locator("xpath=..")
                        if parent.count() == 0:
                            break

                        # Check if parent contains "Par".
                        # We use count() > 0. Note that this searches descendants of parent.
                        # To prevent false positives from other cards, we hope the container isolates the text.
                        if parent.locator("text=Par").count() > 0:
                            card_container = parent
                            break
                        current = parent

                    if not card_container:
                        continue

                    # Get text content of the container
                    container_text = card_container.inner_text()

                    # Parse odds from this text
                    parsed_items = parse_dk_odds(container_text)
                    if not parsed_items:
                        continue

                    # There should be only one item per card typically
                    item = parsed_items[0]

                    # Check if we already processed this player/hole/round
                    uid = (item['player'], item['hole'], item['round'])
                    if uid in processed_ids:
                        continue
                    processed_ids.add(uid)

                    # Extract pin data
                    pin_data = extract_pin_data(card_container)
                    if pin_data:
                        item['pin_x'] = pin_data['x']
                        item['pin_y'] = pin_data['y']

                    data.append(item)

                except Exception as e:
                    print(f"Error processing a card: {e}")

            print(f"Extracted {len(data)} hole scores from DraftKings")

        except Exception as e:
            print(f"Error during DraftKings scrape: {e}")

        browser.close()

    return data
