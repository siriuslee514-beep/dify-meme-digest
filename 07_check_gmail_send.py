import json


def main(body: str, status_code: int) -> dict:
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        raise ValueError("Gmail send response is not valid JSON; check Sent before retrying") from None
    if not isinstance(data, dict):
        raise ValueError("Gmail send response must be a JSON object")
    if not 200 <= status_code < 300 or "error" in data:
        raise ValueError("Gmail send failed: HTTP " + str(status_code))
    message_id = data.get("id")
    if not isinstance(message_id, str) or not message_id.strip():
        raise ValueError("Gmail returned no message ID; check Sent before retrying")
    thread_id = data.get("threadId", "")
    if not isinstance(thread_id, str):
        thread_id = ""
    return {
        "send_status": "accepted_by_gmail",
        "gmail_message_id": message_id,
        "gmail_thread_id": thread_id,
    }
