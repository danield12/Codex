import json
import sys
import argparse
import csv
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
    parser.add_argument("--output", help="Output CSV file", default="pga_hole_scores.csv")
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

    if not consolidated:
        print("No data found from any sportsbook.")
        return

    # Define markets and their display names
    markets = [
        ("Birdie or Better", "Birdie+"),
        ("Par", "Par"),
        ("Bogey or Worse", "Bogey+")
    ]

    # 5. Print Table and Write CSV
    print(f"{'Player':<20} | {'Hole':<4} | {'Rnd':<3} | {'Market':<10} | {'DK':<6} | {'CZR':<6} | {'FD':<6}")
    print("-" * 75)

    sorted_keys = sorted(consolidated.keys(), key=lambda x: (x[0], int(x[1]), int(x[2])))

    csv_rows = []

    for key in sorted_keys:
        player, hole, round_num = key
        book_odds = consolidated[key]

        for market_key, market_display in markets:
            dk_val = book_odds['DraftKings'].get(market_key, "-")
            czr_val = book_odds['Caesars'].get(market_key, "-")
            fd_val = book_odds['FanDuel'].get(market_key, "-")

            print(f"{player:<20} | {hole:<4} | {round_num:<3} | {market_display:<10} | {dk_val:<6} | {czr_val:<6} | {fd_val:<6}")

            csv_rows.append({
                "Player": player,
                "Hole": hole,
                "Round": round_num,
                "Market": market_display,
                "DraftKings Odds": dk_val,
                "Caesars Odds": czr_val,
                "FanDuel Odds": fd_val
            })

    # Write to CSV
    if args.output:
        try:
            with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Player", "Hole", "Round", "Market", "DraftKings Odds", "Caesars Odds", "FanDuel Odds"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)
            print(f"\nSuccessfully wrote {len(csv_rows)} rows to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"\nError writing to CSV: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
