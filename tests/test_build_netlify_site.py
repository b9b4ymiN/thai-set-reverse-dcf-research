import unittest
import pandas as pd
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock

# Add scripts directory to path
sys.path.append(str(Path(__file__).resolve().parents[1] / "scripts"))

import build_netlify_site as bns

class TestBuildNetlifySite(unittest.TestCase):
    def test_pct_formatting(self):
        self.assertEqual(bns.pct(0.12345), "12.35%")
        self.assertEqual(bns.pct(0.12345, 1), "12.3%")

    def test_safe_float(self):
        self.assertEqual(bns.safe_float("1.23"), 1.23)
        self.assertEqual(bns.safe_float(None), 0.0)
        self.assertEqual(bns.safe_float("invalid"), 0.0)

    def test_format_baht(self):
        # Step 1: will be implemented in build_netlify_site
        if hasattr(bns, "format_baht"):
            self.assertEqual(bns.format_baht(1.5e9), "1.5 พันล้านบาท")
            self.assertEqual(bns.format_baht(500000), "0.5 ล้านบาท")
            self.assertEqual(bns.format_baht(-1e9), "-1.0 พันล้านบาท")

    def test_calc_margin_of_safety(self):
        # Step 1: will be implemented in build_netlify_site
        if hasattr(bns, "calc_margin_of_safety"):
            self.assertAlmostEqual(bns.calc_margin_of_safety(110, 100), 10.0)
            self.assertAlmostEqual(bns.calc_margin_of_safety(90, 100), -10.0)

    def test_build_reason_sentences_basic(self):
        rows = [
            {
                "Ticker": "TEST.BK",
                "Period_Type": "quarterly",
                "Statement_Date": "2024-09-30",
                "Availability_Date": "2024-11-14",
                "Signal_Score": "0.1",
                "Actual_Revenue_Growth": "0.15",
                "Implied_Growth_Rate": "0.05",
                "FCF": "1000000",
                "Intrinsic_Value": "110",
                "Price": "100"
            }
        ]
        sentences = bns.build_reason_sentences(rows, {"TEST.BK"})
        self.assertGreater(len(sentences), 0)
        self.assertIn("TEST", sentences[0])
        # After Step 1, it should have FCF or MoS info

    def test_render_guide_toc_uses_toc_card(self):
        body_html = '<h2 id="section1">Section 1</h2>'
        toc = bns.render_guide_toc(body_html)
        self.assertIn("toc-card", toc)
        self.assertIn("#section1", toc)

    def test_thesis_page_metadata_is_thai(self):
        html = bns.render_thesis_page("<h2 id='x'>หัวข้อ</h2>", [{"level": 2, "text": "หัวข้อ", "id": "x"}], "https://example.com")
        self.assertIn('"inLanguage": "th"', html)
        self.assertIn("กรอบการลงทุนเชิงคุณค่าด้วย Reverse DCF", html)
        self.assertEqual(bns.THESIS_SOURCE_DISPLAY, "docs/thesis-damodaran-wacc-thai.md")

    def test_slugify_preserves_thai_headings(self):
        self.assertEqual(bns.slugify("3. ระเบียบวิธีวิจัย"), "3-ระเบียบวิธีวิจัย")
        self.assertEqual(bns.slugify("บทคัดย่อ (Abstract)"), "บทคัดย่อ-abstract")

if __name__ == "__main__":
    unittest.main()
