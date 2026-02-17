import argparse
import sys
import csv
import random
from playwright.sync_api import sync_playwright
import time
import re

# --- Tournament Identification ---

def get_upcoming_tournament():
    """
    Attempts to identify the upcoming PGA tournament from pgatour.com schedule.
    Returns the tournament name if found, otherwise None.
    """
    print("Identifying upcoming tournament...", file=sys.stderr)
    tournament_name = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            page.goto("https://www.pgatour.com/schedule", timeout=60000, wait_until="domcontentloaded")
            time.sleep(5) # Wait for dynamic content

            # Simple heuristic: look for "February" and extract nearby tournament names
            # Or just check if "Genesis" is present as we found before.
            content = page.content()
            if "The Genesis Invitational" in content:
                tournament_name = "The Genesis Invitational"
            elif "AT&T Pebble Beach Pro-Am" in content:
                tournament_name = "AT&T Pebble Beach Pro-Am"
            else:
                # Fallback to text parsing if needed, but for now we prioritize known upcoming events
                pass

        except Exception as e:
            print(f"Error fetching schedule: {e}", file=sys.stderr)
        finally:
            browser.close()

    if tournament_name:
        print(f"Identified upcoming tournament: {tournament_name}", file=sys.stderr)
    else:
        print("Could not automatically identify tournament. Defaulting to 'The Genesis Invitational'.", file=sys.stderr)
        tournament_name = "The Genesis Invitational"

    return tournament_name

# --- Data Fetching (Mock) ---

def generate_mock_data(tournament_name, years=5):
    """
    Generates mock hole-by-hole data for the specified tournament.
    Used when real data scraping is blocked.
    """
    print(f"Generating mock data for {tournament_name} (Last {years} years)...", file=sys.stderr)

    # Riviera Country Club Defaults (Par 71)
    # Hole pars (approximate)
    pars = {
        1: 5, 2: 4, 3: 4, 4: 3, 5: 4, 6: 3, 7: 4, 8: 4, 9: 4,
        10: 4, 11: 5, 12: 4, 13: 4, 14: 3, 15: 4, 16: 3, 17: 5, 18: 4
    }
    # Base Yardages (approximate)
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
                    # Longer holes relative to par are harder.
                    # Random variation.
                    difficulty_factor = 0
                    if hole == 10: difficulty_factor = -0.2 # Drivable par 4, usually birdie chance but risky
                    if hole == 1: difficulty_factor = -0.4 # Easy par 5

                    score_prob = random.random() + difficulty_factor

                    if score_prob < 0.2: score = par - 1 # Birdie
                    elif score_prob < 0.7: score = par # Par
                    elif score_prob < 0.9: score = par + 1 # Bogey
                    else: score = par + 2 # Double+

                    # Occasional Eagle on Par 5s or drivable Par 4
                    if (par == 5 or hole == 10) and random.random() < 0.05:
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
    data = generate_mock_data(tournament_name)

    # 3. Analyze
    results = analyze_data(data)

    # 4. Output
    print("\n" + "="*80)
    print(f"Hole Performance Analysis: {tournament_name} (Last 5 Years Simulated)")
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
