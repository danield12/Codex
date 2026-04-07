import argparse
import sys
import csv
import random
from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime

# --- Tournament Identification ---

def get_tournament_importance(name):
    """
    Returns a score for tournament importance/payout.
    Higher is better.
    """
    # Major/Signature events
    if any(x in name for x in ["Masters", "PGA Championship", "U.S. Open", "Open Championship", "THE PLAYERS", "Genesis", "Arnold Palmer", "Memorial"]):
        return 100
    # Regular events with high profile
    if "Cognizant Classic" in name or "Honda Classic" in name:
        return 80
    if "Phoenix Open" in name:
        return 80
    # Regular events
    return 50

def get_upcoming_tournament():
    """
    Attempts to identify the upcoming PGA tournament.
    Uses ESPN API to find active or upcoming events, and selects the most important one.
    """
    print("Identifying upcoming tournament...", file=sys.stderr)
    import urllib.request
    import json

    url = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            events = data.get('events', [])

            if not events:
                print("No upcoming events found from API. Defaulting to 'Cognizant Classic in The Palm Beaches'.", file=sys.stderr)
                return "Cognizant Classic in The Palm Beaches"

            best_tournament = None
            max_payout = -1

            for event in events:
                name = event.get('name', '')

                # ESPN API purse
                purse = 0
                for comp in event.get('competitions', []):
                    purse_val = comp.get('purse', 0)
                    if isinstance(purse_val, (int, float)) and purse_val > purse:
                        purse = purse_val

                # If API purse is not available/0, use our fallback importance function (scaling it up to act as purse)
                if purse == 0:
                    purse = get_tournament_importance(name) * 100000

                if purse > max_payout:
                    max_payout = purse
                    best_tournament = name

            if best_tournament:
                print(f"Selected: {best_tournament} with score/payout proxy: {max_payout}", file=sys.stderr)
                return best_tournament

    except Exception as e:
        print(f"API fetch error: {e}", file=sys.stderr)

    return "Cognizant Classic in The Palm Beaches"


# --- Data Fetching (Mock) ---

def generate_mock_data(tournament_name, years=5):
    """
    Generates mock hole-by-hole data for the specified tournament.
    Used when real data scraping is blocked.
    """
    print(f"Generating mock data for {tournament_name} (Last {years} years)...", file=sys.stderr)

    # Defaults
    pars = {}
    base_yards = {}

    if "Cognizant" in tournament_name:
        # PGA National Champion Course (Par 71)
        # Bear Trap: 15, 16, 17
        pars = {
            1: 4, 2: 4, 3: 5, 4: 4, 5: 3, 6: 4, 7: 3, 8: 4, 9: 4,
            10: 5, 11: 4, 12: 4, 13: 4, 14: 4, 15: 3, 16: 4, 17: 3, 18: 5
        }
        base_yards = {
            1: 365, 2: 484, 3: 538, 4: 395, 5: 217, 6: 479, 7: 226, 8: 427, 9: 421,
            10: 550, 11: 450, 12: 438, 13: 388, 14: 465, 15: 179, 16: 434, 17: 175, 18: 592
        }
    else:
        # Riviera Country Club Defaults (Par 71)
        pars = {
            1: 5, 2: 4, 3: 4, 4: 3, 5: 4, 6: 3, 7: 4, 8: 4, 9: 4,
            10: 4, 11: 5, 12: 4, 13: 4, 14: 3, 15: 4, 16: 3, 17: 5, 18: 4
        }
        base_yards = {
            1: 503, 2: 471, 3: 434, 4: 236, 5: 434, 6: 199, 7: 408, 8: 433, 9: 458,
            10: 315, 11: 583, 12: 479, 13: 459, 14: 192, 15: 487, 16: 166, 17: 590, 18: 475
        }

    data = []

    current_year = 2026 # Based on date check
    start_year = current_year - years

    for year in range(start_year, current_year):
        # Generate 4 rounds per year
        for round_num in range(1, 5):
            # Daily yardage variation
            daily_yards = {}
            for h in range(1, 19):
                # Yardage varies by +/- 15 yards
                variation = random.randint(-15, 15)
                daily_yards[h] = base_yards.get(h, 400) + variation

            # Generate player scores (simulating ~60 players making cut)
            for player_id in range(1, 61):
                player_name = f"Player {player_id}"

                for hole in range(1, 19):
                    par = pars.get(hole, 4)
                    yards = daily_yards[hole]

                    # Score simulation logic:
                    difficulty_factor = 0

                    if "Cognizant" in tournament_name:
                        # Bear Trap (15, 16, 17) is notoriously hard
                        if hole in [15, 16, 17]:
                            difficulty_factor = 0.3 # Harder
                        # Water hazards on many holes
                        if hole in [6, 10, 11, 14, 18]:
                            difficulty_factor += 0.1
                    else:
                        # Riviera logic
                        if hole == 10: difficulty_factor = -0.2 # Drivable par 4
                        if hole == 1: difficulty_factor = -0.4 # Easy par 5

                    score_prob = random.random() + difficulty_factor

                    if score_prob < 0.2: score = par - 1 # Birdie
                    elif score_prob < 0.7: score = par # Par
                    elif score_prob < 0.9: score = par + 1 # Bogey
                    else: score = par + 2 # Double+

                    # Occasional Eagle on Par 5s
                    if par == 5 and random.random() < 0.05:
                        score = par - 2

                    data.append({
                        "Year": year,
                        "Round": round_num,
                        "Player": player_name,
                        "Hole": hole,
                        "Par": par,
                        "Yardage": yards,
                        "Score": score
                    })

    return data

# --- Analysis ---

def analyze_data(data):
    """
    Analyzes the hole-by-hole data.
    """
    print("Analyzing data...", file=sys.stderr)

    # Aggregation by Hole
    hole_stats = {}

    for entry in data:
        hole = entry['Hole']
        if hole not in hole_stats:
            hole_stats[hole] = {
                'total_score': 0,
                'count': 0,
                'par': entry['Par'],
                'total_yards': 0,
                'birdies_or_better': 0,
                'bogeys_or_worse': 0,
                'rounds_data': {} # Key: (Year, Round), Value: yards
            }

        stats = hole_stats[hole]
        stats['total_score'] += entry['Score']
        stats['count'] += 1
        stats['total_yards'] += entry['Yardage']

        if entry['Score'] < entry['Par']:
            stats['birdies_or_better'] += 1
        elif entry['Score'] > entry['Par']:
            stats['bogeys_or_worse'] += 1

        # Track daily yardage for variation analysis
        key = (entry['Year'], entry['Round'])
        stats['rounds_data'][key] = entry['Yardage']

    # Finalize stats
    results = []
    for hole in sorted(hole_stats.keys()):
        stats = hole_stats[hole]
        count = stats['count']
        avg_score = stats['total_score'] / count
        avg_yards = stats['total_yards'] / count
        birdie_pct = (stats['birdies_or_better'] / count) * 100
        bogey_pct = (stats['bogeys_or_worse'] / count) * 100

        # Yardage variation (min/max)
        yards_values = list(stats['rounds_data'].values())
        min_yards = min(yards_values)
        max_yards = max(yards_values)

        results.append({
            "Hole": hole,
            "Par": stats['par'],
            "Avg Yardage": round(avg_yards, 1),
            "Min Yardage": min_yards,
            "Max Yardage": max_yards,
            "Avg Score": round(avg_score, 3),
            "Birdie+ %": round(birdie_pct, 1),
            "Bogey+ %": round(bogey_pct, 1)
        })

    return results

# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Golf Hole Performance and Daily Yardage Analysis")
    parser.add_argument("--tournament", help="Tournament name (optional)", default=None)
    parser.add_argument("--years", help="Years of historical data to analyze", type=int, default=5)
    parser.add_argument("--output", help="Output CSV file", default="hole_performance_analysis.csv")
    args = parser.parse_args()

    print("Starting Golf Hole Performance and Daily Yardage Analysis...", file=sys.stderr)

    # 1. Identify Tournament
    tournament_name = args.tournament
    if not tournament_name:
        tournament_name = get_upcoming_tournament()

    print(f"Target Tournament: {tournament_name}")

    # 2. Fetch Data (Mock/Real)
    # In a real scenario, we would try to scrape here.
    # Due to anti-bot measures, we default to mock data with a warning.
    print("WARNING: Live historical data scraping is restricted. Using simulated data for demonstration.", file=sys.stderr)
    data = generate_mock_data(tournament_name, args.years)

    # 3. Analyze
    results = analyze_data(data)

    # 4. Output
    print("\n" + "="*80)
    print(f"Hole Performance Analysis: {tournament_name} (Last {args.years} Years Simulated)")
    print("="*80)
    print(f"{'Hole':<5} | {'Par':<3} | {'Avg Yds':<8} | {'Range (Yds)':<12} | {'Avg Score':<10} | {'Birdie+ %':<10} | {'Bogey+ %':<10}")
    print("-" * 80)

    for r in results:
        yard_range = f"{r['Min Yardage']}-{r['Max Yardage']}"
        print(f"{r['Hole']:<5} | {r['Par']:<3} | {r['Avg Yardage']:<8} | {yard_range:<12} | {r['Avg Score']:<10} | {r['Birdie+ %']:<10} | {r['Bogey+ %']:<10}")

    # CSV Output
    if args.output:
        try:
            with open(args.output, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["Hole", "Par", "Avg Yardage", "Min Yardage", "Max Yardage", "Avg Score", "Birdie+ %", "Bogey+ %"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
            print(f"\nAnalysis saved to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing to CSV: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
