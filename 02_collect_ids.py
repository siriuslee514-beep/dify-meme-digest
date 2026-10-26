import json
import re


def main(meme_body: str, brand_body: str) -> dict:
    sources = {}

    responses = [
        ("meme", meme_body),
        ("brand", brand_body),
    ]

    for lane, body in responses:
        data = json.loads(body)

        if not isinstance(data, dict) or "error" in data:
            raise ValueError("YouTube 请求结果异常：" + lane)

        if not isinstance(data.get("items"), list):
            raise ValueError("返回结果缺少视频列表：" + lane)

        for item in data["items"]:
            video_id = item.get("id", {}).get("videoId", "")

            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
                continue

            # 相同视频 ID 只保留一次
            sources.setdefault(video_id, [])

            # 记录这个视频来自哪一路搜索
            if lane not in sources[video_id]:
                sources[video_id].append(lane)

    if len(sources) > 40:
        raise ValueError("候选超过 40 条，需要增加分批处理")

    return {
        "video_ids": ",".join(sources.keys()),
        "sources_json": json.dumps(sources, ensure_ascii=False),
        "count": len(sources),
    }
