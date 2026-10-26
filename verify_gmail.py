"""Offline Gmail checks with synthetic addresses and tokens. No email is sent."""
import base64
import json
from email import policy
from email.parser import BytesParser
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parent
build = runpy.run_path(str(ROOT / "05_build_gmail_message.py"))["main"]
parse_token = runpy.run_path(str(ROOT / "06_parse_gmail_token.py"))["main"]
check_send = runpy.run_path(str(ROOT / "07_check_gmail_send.py"))["main"]


class GmailChecks(unittest.TestCase):
    def setUp(self):
        self.inputs = dict(sender="sender@example.com", recipient="recipient@example.com",
                           subject="Meme 选题日报 | 中文 😂", body_text="中文推荐\nhttps://www.youtube.com/watch?v=TEST0000001",
                           body_html='<h1>中文推荐 😂</h1><a href="https://www.youtube.com/watch?v=TEST0000001">原视频</a>')

    def test_unicode_multipart_round_trip(self):
        output = build(**self.inputs)
        self.assertEqual(json.loads(output["request_body"])["raw"], output["raw"])
        message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(output["raw"]))
        self.assertEqual(str(message["Subject"]), self.inputs["subject"])
        self.assertEqual(str(message["To"]), self.inputs["recipient"])
        self.assertEqual(str(message["From"]), self.inputs["sender"])
        self.assertEqual(message.get_content_type(), "multipart/alternative")
        for subtype, field in [("plain", "body_text"), ("html", "body_html")]:
            actual = message.get_body(preferencelist=(subtype,)).get_content().replace("\r\n", "\n").rstrip("\n")
            self.assertEqual(actual, self.inputs[field])

    def test_headers_cannot_add_recipients(self):
        for field, value in [("subject", "Hello\r\nBcc: other@example.com"),
                             ("recipient", "first@example.com,second@example.com"),
                             ("recipient", "name <first@example.com>"),
                             ("sender", "first@example.com\n"), ("recipient", "invalid")]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                build(**dict(self.inputs, **{field: value}))

    def test_token_requires_success_and_bearer(self):
        self.assertEqual(parse_token('{"access_token":"synthetic-token","token_type":"Bearer"}', 200),
                         {"access_token": "synthetic-token", "authorization": "Bearer synthetic-token"})
        for body, status in [("{}", 200), ('{"error":"invalid_grant"}', 400),
                              ('{"access_token":"synthetic-token","token_type":"Bearer"}', 500),
                              ('{"access_token":"synthetic-token","token_type":"other"}', 200),
                              ("not JSON", 200)]:
            with self.subTest(body=body, status=status), self.assertRaises(ValueError):
                parse_token(body, status)

    def test_send_success_preserves_message_id(self):
        output = check_send('{"id":"synthetic-id","threadId":"synthetic-thread"}', 200)
        self.assertEqual(output, {"send_status": "accepted_by_gmail", "gmail_message_id": "synthetic-id",
                                  "gmail_thread_id": "synthetic-thread"})

    def test_send_failure_never_claims_success(self):
        for body, status in [("{}", 200), ('{"id":"synthetic-id"}', 403),
                              ('{"error":{"code":403}}', 200), ('{"id":""}', 200), ("[]", 200),
                              ("not JSON", 502)]:
            with self.subTest(body=body, status=status), self.assertRaises(ValueError):
                check_send(body, status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
