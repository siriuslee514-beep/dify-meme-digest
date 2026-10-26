import json


def main(body: str, status_code: int) -> dict:
    try:
        data = json.loads(body)
    except (TypeError, ValueError):
        raise ValueError("令牌响应不是有效 JSON") from None

    if not isinstance(data, dict):
        raise ValueError("令牌响应必须是 JSON 对象")

    if not 200 <= status_code < 300 or "error" in data:
        raise ValueError(f"Gmail 授权失败：HTTP {status_code}")

    token = data.get("access_token")

    if not isinstance(token, str) or not token:
        raise ValueError("响应中缺少 access_token")

    if any(c.isspace() for c in token):
        raise ValueError("access_token 中包含异常空白字符")

    if str(data.get("token_type", "")).lower() != "bearer":
        raise ValueError("令牌类型不是 Bearer")

    return {
        "access_token": token,
        "authorization": "Bearer " + token,
    }
