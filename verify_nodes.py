"""Offline behavioral checks using synthetic data; no network or email calls."""
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parent
config = runpy.run_path(str(ROOT / "01_config.py"))["main"]
collect = runpy.run_path(str(ROOT / "02_collect_ids.py"))["main"]
normalize = runpy.run_path(str(ROOT / "03_normalize.py"))["main"]
render = runpy.run_path(str(ROOT / "04_render.py"))["main"]


class PipelineChecks(unittest.TestCase):
    def setUp(self):
        self.video_id = "TEST0000001"
        self.search = json.dumps({"items": [{"id": {"videoId": self.video_id}}]})
        self.ids = collect(self.search, self.search)
        self.details = json.dumps({"items": [{
            "id": self.video_id,
            "snippet": {"title": "Synthetic <script>alert(1)</script>",
                        "description": "A fictional test fixture, not a real video.",
                        "channelTitle": "Test channel", "publishedAt": "2026-10-25T01:00:00Z"},
            "statistics": {"viewCount": "0"}, "contentDetails": {"duration": "PT1M"}
        }]})
        self.normalized = normalize(self.details, self.ids["sources_json"], "2026-10-26T01:00:00Z")
        self.analysis = {"themes": [], "recommendations": [{
            "video_id": self.video_id, "category": "meme", "topic": "测试",
            "summary": "仅作合成测试", "recommendation_reason": "测试输入校验",
            "adaptation_idea": "可尝试测试", "confidence": "low"
        }]}

    def report(self, analysis):
        return render(analysis, self.normalized["candidates_json"], "2026-10-26", "2026-10-26T01:00:00Z")

    def test_duplicate_sources_merge(self):
        self.assertEqual(self.ids["count"], 1)
        self.assertEqual(json.loads(self.ids["sources_json"])[self.video_id], ["meme", "brand"])

    def test_missing_statistics_are_not_zero(self):
        row = json.loads(self.normalized["candidates_json"])[0]
        self.assertEqual(row["view_count"], 0)
        self.assertIsNone(row["like_count"])

    def test_links_come_from_api_and_html_is_escaped(self):
        self.analysis["recommendations"][0]["url"] = "https://attacker.invalid"
        result = self.report(self.analysis)
        self.assertNotIn("attacker.invalid", result["body_html"])
        self.assertIn("https://www.youtube.com/watch?v=" + self.video_id, result["body_html"])
        self.assertNotIn("<script>", result["body_html"])
        self.assertIn("&lt;script&gt;", result["body_html"])

    def test_hallucinated_or_duplicate_ids_fail(self):
        self.analysis["recommendations"][0]["video_id"] = "OTHER000001"
        with self.assertRaises(ValueError):
            self.report(self.analysis)
        self.analysis["recommendations"][0]["video_id"] = self.video_id
        self.analysis["recommendations"].append(dict(self.analysis["recommendations"][0]))
        with self.assertRaises(ValueError):
            self.report(self.analysis)

    def test_empty_results_are_valid_but_api_errors_fail(self):
        self.assertEqual(collect('{"items":[]}', '{"items":[]}')["count"], 0)
        self.assertEqual(self.report({"themes": [], "recommendations": []})["selected_count"], 0)
        with self.assertRaises(ValueError):
            collect('{"error":{"code":403}}', self.search)

    def test_theme_cannot_cite_missing_sources(self):
        self.analysis["themes"] = [{"name": "Test", "observation": "Test",
                                    "evidence_video_ids": [self.video_id, "OTHER000001"]}]
        with self.assertRaises(ValueError):
            self.report(self.analysis)

    def test_category_limit_preserves_order_and_validates_excess_rows(self):
        template = json.loads(self.normalized["candidates_json"])[0]
        candidates = []
        rows = []
        for i in range(10):
            video_id = "TEST" + str(i + 1).zfill(7)
            candidates.append(dict(template, video_id=video_id,
                                   url="https://www.youtube.com/watch?v=" + video_id))
            rows.append(dict(self.analysis["recommendations"][0], video_id=video_id,
                             category="meme" if i < 6 else "brand"))
        self.normalized["candidates_json"] = json.dumps(candidates)
        self.analysis["recommendations"] = rows
        result = self.report(self.analysis)
        selected = json.loads(result["report_json"])["recommendations"]
        self.assertEqual(result["selected_count"], 9)
        self.assertEqual([r["video_id"] for r in selected],
                         [r["video_id"] for r in rows[:5] + rows[6:]])
        rows[5]["video_id"] = "OTHER000001"
        with self.assertRaises(ValueError):
            self.report(self.analysis)


if __name__ == "__main__":
    json.loads((ROOT / "output_schema.json").read_text(encoding="utf-8"))
    result = config("")
    assert result["published_after_meme"].endswith("Z")
    unittest.main(verbosity=2)
