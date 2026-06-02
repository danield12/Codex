import unittest
from hole_performance_analysis import generate_mock_data, analyze_data

class TestHoleAnalysis(unittest.TestCase):
    def test_mock_data_generation(self):
        data = generate_mock_data("Test Tournament", years=1)
        self.assertTrue(len(data) > 0)
        entry = data[0]
        self.assertIn("Hole", entry)
        self.assertIn("Score", entry)
        self.assertIn("Yardage", entry)
        self.assertIn("Par", entry)

    def test_cognizant_data_generation(self):
        data = generate_mock_data("Cognizant Classic in The Palm Beaches", years=1)
        self.assertTrue(len(data) > 0)
        # Verify Par 71 logic (sum of pars for 1 round should be 71)
        # Note: data contains many rounds/players. Let's check hole 15 par is 3.
        hole_15 = next(d for d in data if d['Hole'] == 15)
        self.assertEqual(hole_15['Par'], 3)
        hole_3 = next(d for d in data if d['Hole'] == 3)
        self.assertEqual(hole_3['Par'], 5)

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
