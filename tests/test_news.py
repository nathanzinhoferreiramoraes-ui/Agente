import unittest
from datetime import datetime, timezone
from agente100.news import Headline, parse_rss, score_asset


class NewsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)

    def test_parse_recent_only(self):
        xml = b"""<rss><channel>
          <item><title>Bitcoin rally</title><pubDate>Sat, 10 Oct 2026 11:00:00 GMT</pubDate></item>
          <item><title>Old bitcoin crash</title><pubDate>Fri, 09 Oct 2026 01:00:00 GMT</pubDate></item>
          <item><title>Undated</title></item>
        </channel></rss>"""
        items = parse_rss(xml, now=self.now)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Bitcoin rally")

    def test_sentiment_per_asset(self):
        headlines = [Headline("Bitcoin rally and adoption", self.now),
                     Headline("Ethereum crash after hack", self.now)]
        self.assertEqual(score_asset(headlines, "BTC-USD"), 1.0)
        self.assertEqual(score_asset(headlines, "ETH-USD"), -1.0)
        self.assertEqual(score_asset(headlines, "SOL-USD"), 0.0)

    def test_no_headlines_neutral(self):
        self.assertEqual(score_asset([], "BTC-USD"), 0.0)

    def test_bad_xml(self):
        with self.assertRaises(Exception):
            parse_rss(b"<broken", now=self.now)

    def test_invalid_asset(self):
        with self.assertRaises(ValueError):
            score_asset([], "DOGE-USD")


if __name__ == "__main__":
    unittest.main()
