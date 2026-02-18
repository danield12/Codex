import os
import unittest
from playwright.sync_api import sync_playwright

class TestPinExtractionWithPlaywright(unittest.TestCase):
    def test_extract_pin_from_mock(self):
        # Assuming the test is run from the root directory
        filepath = os.path.abspath("tests/mock_dk_page.html")
        url = f"file://{filepath}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)

            # Find all card containers
            # In mock, they are .sportsbook-outcome-cell
            cards = page.locator(".sportsbook-outcome-cell").all()
            self.assertEqual(len(cards), 2)

            # Logic to extract pin
            results = []
            for card in cards:
                # 1. Get header text
                header = card.locator(".header").inner_text()

                # 2. Extract pin info using evaluate
                # We assume the "green" is the immediate parent of the pin, or we calculate relative to a known container.
                # Let's say we want relative to the "green" element.
                # Heuristic: Find pin (small circle), then find its parent as the green.

                pin_data = card.evaluate("""(element) => {
                    function isPin(el) {
                        const style = window.getComputedStyle(el);
                        const w = parseFloat(style.width);
                        const h = parseFloat(style.height);
                        const r = style.borderRadius;
                        const bg = style.backgroundColor;

                        // Check size (mock pin is 10px or 8px)
                        if (w > 0 && w <= 20 && h > 0 && h <= 20) {
                            // simplistic check for circle
                            if (r.includes('50%') || parseFloat(r) >= w/2 - 1) {
                                // check color - red(ish) or black(ish)
                                // mock: red -> rgb(255, 0, 0), black -> rgb(0, 0, 0)
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

                    const relX = (pinCenterX - greenRect.left) / greenRect.width;
                    const relY = (pinCenterY - greenRect.top) / greenRect.height;

                    return { x: relX, y: relY };
                }""")

                results.append({
                    "header": header,
                    "pin": pin_data
                })

            browser.close()

            # Verify results
            # Card 1: Green 160x160 at (20,20). Pin 10x10 at (40,40) relative to green container (which is at 20,20).
            # Wait, mock HTML:
            # .green { top: 20px; left: 20px; width: 160px; height: 160px; } (relative to .visualization-container)
            # .pin { top: 40px; left: 40px; width: 10px; height: 10px; } (relative to .green)
            # So pin center relative to green:
            # pin left: 40, width: 10 -> center x = 45
            # pin top: 40, height: 10 -> center y = 45
            # relative x = 45 / 160 = 0.28125
            # relative y = 45 / 160 = 0.28125

            p1 = results[0]['pin']
            self.assertIsNotNone(p1)
            self.assertAlmostEqual(p1['x'], 45/160, places=2)
            self.assertAlmostEqual(p1['y'], 45/160, places=2)

            # Card 2: Green 180x180. Pin 8x8 at (90, 90).
            # Center x = 90 + 4 = 94
            # Center y = 90 + 4 = 94
            # Rel x = 94 / 180 = 0.522
            # Rel y = 94 / 180 = 0.522

            p2 = results[1]['pin']
            self.assertIsNotNone(p2)
            self.assertAlmostEqual(p2['x'], 94/180, places=2)
            self.assertAlmostEqual(p2['y'], 94/180, places=2)

if __name__ == '__main__':
    unittest.main()
