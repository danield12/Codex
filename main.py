import json
import sys
import argparse
from scrapers.draftkings import scrape_dk
from scrapers.caesars import scrape_caesars
from scrapers.fanduel import scrape_fanduel

def normalize_player_name(name):
    """
    Normalizes player name for comparison across books.
    Simple strip and title case.
    """
    return name.strip().title()

def main():
    parser = argparse.ArgumentParser(description="Scrape and compare PGA hole score odds.")
    parser.add_argument("--dk-url", help="DraftKings tournament URL", default=None)
    args = parser.parse_args()

    print("Starting PGA hole score odds comparison...", file=sys.stderr)

    # 1. Scrape DraftKings
    try:
        dk_data = scrape_dk(url=args.dk_url)
    except Exception as e:
        print(f"Error scraping DraftKings: {e}", file=sys.stderr)
        dk_data = []

    # 2. Scrape Caesars (placeholder)
    try:
        czr_data = scrape_caesars()
    except Exception as e:
        print(f"Error scraping Caesars: {e}", file=sys.stderr)
        czr_data = []

    # 3. Scrape FanDuel (placeholder)
    try:
        fd_data = scrape_fanduel()
    except Exception as e:
        print(f"Error scraping FanDuel: {e}", file=sys.stderr)
        fd_data = []

    # 4. Consolidate data
    # Key: (player_norm, hole, round)
    consolidated = {}

    # Process DK
    for entry in dk_data:
        player = normalize_player_name(entry['player'])
        hole = entry['hole']
        round_num = entry['round']
        odds = entry['odds']
        key = (player, hole, round_num)

        if key not in consolidated:
            consolidated[key] = {'DraftKings': {}, 'Caesars': {}, 'FanDuel': {}}

        consolidated[key]['DraftKings'] = odds

    # Process Caesars
    for entry in czr_data:
        player = normalize_player_name(entry['player'])
        hole = entry['hole']
        round_num = entry['round']
        odds = entry['odds']
        key = (player, hole, round_num)

        if key not in consolidated:
            consolidated[key] = {'DraftKings': {}, 'Caesars': {}, 'FanDuel': {}}

        consolidated[key]['Caesars'] = odds

    # Process FanDuel
    for entry in fd_data:
        player = normalize_player_name(entry['player'])
        hole = entry['hole']
        round_num = entry['round']
        odds = entry['odds']
        key = (player, hole, round_num)

        if key not in consolidated:
            consolidated[key] = {'DraftKings': {}, 'Caesars': {}, 'FanDuel': {}}

        consolidated[key]['FanDuel'] = odds

    # 5. Print Table
    if not consolidated:
        print("No data found from any sportsbook.")
        return

    # Define markets and their display names
    markets = [
        ("Birdie or Better", "Birdie+"),
        ("Par", "Par"),
        ("Bogey or Worse", "Bogey+")
    ]

    # Header
    print(f"{'Player':<20} | {'Hole':<4} | {'Rnd':<3} | {'Market':<10} | {'DK':<6} | {'CZR':<6} | {'FD':<6}")
    print("-" * 75)

    # Sort by player, then hole, then round
    sorted_keys = sorted(consolidated.keys(), key=lambda x: (x[0], int(x[1]), int(x[2])))

    for key in sorted_keys:
        player, hole, round_num = key
        book_odds = consolidated[key]

        for market_key, market_display in markets:
            dk_val = book_odds['DraftKings'].get(market_key, "-")
            czr_val = book_odds['Caesars'].get(market_key, "-")
            fd_val = book_odds['FanDuel'].get(market_key, "-")

            print(f"{player:<20} | {hole:<4} | {round_num:<3} | {market_display:<10} | {dk_val:<6} | {czr_val:<6} | {fd_val:<6}")

if __name__ == "__main__":
    main()
