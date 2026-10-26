import json
from pathlib import Path
import runpy
import unittest

parse = runpy.run_path(str(Path(__file__).with_name("03b_parse_analysis.py")))["main"]


class ParserChecks(unittest.TestCase):
    def test_plain_and_wrapped_json(self):
        obj = {"themes": [], "recommendations": []}
        raw = json.dumps(obj)
        for content in (raw, "```json\n" + raw + "\n```", "<think>test</think>\n" + raw):
            with self.subTest(content=content):
                self.assertEqual(parse(content), {"analysis": obj})

    def test_invalid_output_fails_without_fabricating_empty_result(self):
        for content in ("", "{}", "[]", "{", '{"themes": [], "recommendations": {}}',
                        '<think>unfinished', '{"themes": [], "recommendations": [], "n": NaN}'):
            with self.subTest(content=content):
                with self.assertRaises(ValueError):
                    parse(content)

    def test_json_strings_are_preserved(self):
        obj = {"themes": [], "recommendations": [{"summary": "literal </think> and ``` marks"}]}
        self.assertEqual(parse(json.dumps(obj))["analysis"], obj)


if __name__ == "__main__":
    unittest.main(verbosity=2)
