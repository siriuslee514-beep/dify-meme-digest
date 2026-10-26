import html
import json
import re


def main(videos_body: str, sources_json: str, snapshot_at: str) -> dict:
    data = json.loads(videos_body)
    sources = json.loads(sources_json)

    if not isinstance(data, dict) or "error" in data:
        raise ValueError("YouTube 视频详情请求异常")

    if not isinstance(data.get("items"), list):
        raise ValueError("返回结果缺少视频列表")

    # 将统计数据转为数字；缺失的数据保留为空
    def number(value):
        if value is None:
            return None
        try:
            parsed = int(value)
            return parsed if parsed >= 0 else None
        except (TypeError, ValueError):
            return None

    candidates = []
    seen = set()

    for item in data["items"]:
        video_id = item.get("id", "")

        if video_id not in sources or video_id in seen:
            continue

        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            continue

        snippet = item.get("snippet", {})

        # 排除正在直播或预约直播的视频
        if snippet.get("liveBroadcastContent", "none") != "none":
            continue

        statistics = item.get("statistics", {})
        seen.add(video_id)

        candidates.append({
            "video_id": video_id,
            "source_lanes": sources[video_id],
            "title": html.unescape(snippet.get("title", ""))[:300],
            "description": html.unescape(
                snippet.get("description", "")
            )[:1200],
            "channel": html.unescape(
                snippet.get("channelTitle", "")
            )[:200],
            "published_at": snippet.get("publishedAt", ""),
            "duration": item.get("contentDetails", {}).get("duration", ""),
            "view_count": number(statistics.get("viewCount")),
            "like_count": number(statistics.get("likeCount")),
            "comment_count": number(statistics.get("commentCount")),
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "snapshot_at": snapshot_at,
            "analysis_basis": "title_description_statistics",
        })

    return {
        "candidates_json": json.dumps(candidates, ensure_ascii=False),
        "count": len(candidates),
    }
