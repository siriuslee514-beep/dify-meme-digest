from datetime import datetime, timedelta, timezone


def main(brand_brief: str) -> dict:
    now = datetime.now(timezone.utc)

    return {
        "query_meme": "meme|funny skit",
        "query_brand": "creative commercial|funny advertisement",

        "published_after_meme": (
            now - timedelta(days=3)
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),

        "published_after_brand": (
            now - timedelta(days=30)
        ).strftime("%Y-%m-%dT%H:%M:%SZ"),

        "region_code": "US",
        "relevance_language": "en",

        "snapshot_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),

        "report_date": now.astimezone(
            timezone(timedelta(hours=8))
        ).strftime("%Y-%m-%d"),

        "brand_brief": (brand_brief or "").strip()
        or "品牌信息未提供，仅提出通用创意方向。"
    }
