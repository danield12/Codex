import unittest
from scrapers.draftkings import parse_dk_odds

class TestDraftKingsParsing(unittest.TestCase):
    def test_parse_simple_odds(self):
        text = """
Daniel Berger Hole Score - Hole 10 - Round 3
Par
−240
Bogey or Worse
+360
Birdie or Better
+495

Jhonattan Vegas Hole Score - Hole 10 - Round 3
Par
-205
Bogey or Worse
+265
Birdie or Better
+560
"""
        data = parse_dk_odds(text)
        self.assertEqual(len(data), 2)

        self.assertEqual(data[0]['player'], "Daniel Berger")
        self.assertEqual(data[0]['hole'], "10")
        self.assertEqual(data[0]['round'], "3")
        self.assertEqual(data[0]['odds']['Par'], "-240")
        self.assertEqual(data[0]['odds']['Bogey or Worse'], "+360")
        self.assertEqual(data[0]['odds']['Birdie or Better'], "+495")

        self.assertEqual(data[1]['player'], "Jhonattan Vegas")
        self.assertEqual(data[1]['odds']['Par'], "-205")

if __name__ == '__main__':
    unittest.main()
