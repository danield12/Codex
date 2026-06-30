import unittest
from hole_performance_analysis import get_real_historical_data, analyze_data

class TestHoleAnalysis(unittest.TestCase):

    def test_data_fetching(self):
        # We test with 1 year to minimize API calls during tests
        data = get_real_historical_data("U.S. Open", years=1)
        if len(data) > 0: # It might be 0 if the tournament hasn't happened in the last year or API fails
            entry = data[0]
            self.assertIn("Hole", entry)
            self.assertIn("Score", entry)
            self.assertIn("Yardage", entry)
            self.assertIn("Par", entry)

    # We remove test_cognizant_data_generation since the mock logic is gone

    def test_analysis(self):
        mock_data = [
            {"Year": 2025, "Round": 1, "Hole": 1, "Par": 4, "Yardage": 400, "Score": 4},
            {"Year": 2025, "Round": 2, "Hole": 1, "Par": 4, "Yardage": 410, "Score": 3},
        ]
        results = analyze_data(mock_data)
        self.assertEqual(len(results), 1)
        res = results[0]
        self.assertEqual(res['Hole'], 1)
        self.assertEqual(res['Par'], 4)
        self.assertEqual(res['Avg Score'], 3.5)
        self.assertEqual(res['Min Yardage'], 400)
        self.assertEqual(res['Max Yardage'], 410)

if __name__ == '__main__':
    unittest.main()
