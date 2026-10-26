import base64
import json
from datetime import datetime, timezone
from email import policy
from email.headerregistry import Address
from email.message import EmailMessage
from email.utils import format_datetime


def main(sender: str, recipient: str, subject: str,
         body_text: str, body_html: str) -> dict:
    def mailbox(value, label):
        if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError(label + " must be one plain email address")
        value = value.strip()
        if not value.isascii() or any(c in value for c in " ,;<>\t"):
            raise ValueError(label + " must be one plain ASCII email address")
        try:
            address = Address(addr_spec=value)
        except ValueError:
            raise ValueError(label + " is not a valid email address") from None
        if not address.username or not address.domain or "." not in address.domain:
            raise ValueError(label + " is not a valid email address")
        return value

    sender = mailbox(sender, "sender")
    recipient = mailbox(recipient, "recipient")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 250:
        raise ValueError("subject must be non-empty text of at most 250 characters")
    if any(ord(c) < 32 or ord(c) == 127 for c in subject):
        raise ValueError("subject must not contain control characters")
    if not isinstance(body_text, str) or not body_text.strip():
        raise ValueError("body_text must be non-empty text")
    if not isinstance(body_html, str) or not body_html.strip():
        raise ValueError("body_html must be non-empty HTML")

    message = EmailMessage(policy=policy.SMTP)
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject.strip()
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message.set_content(body_text, charset="utf-8")
    message.add_alternative(body_html, subtype="html", charset="utf-8")
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    return {"raw": raw, "request_body": json.dumps({"raw": raw})}
