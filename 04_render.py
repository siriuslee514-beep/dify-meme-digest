import html
import json
import re


def main(analysis: dict, candidates_json: str, report_date: str, snapshot_at: str) -> dict:
    if not isinstance(analysis, dict):
        raise ValueError("Bind analysis to the parsed analysis object or LLM structured_output")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", report_date):
        raise ValueError("Invalid report date")
    candidates = json.loads(candidates_json)
    known = {v["video_id"]: v for v in candidates}
    rows = analysis.get("recommendations")
    themes = analysis.get("themes")
    if not isinstance(rows, list) or not isinstance(themes, list):
        raise ValueError("Missing recommendations or themes")
    if len(rows) > 10 or len(themes) > 5:
        raise ValueError("Too many recommendations or themes")

    def text_field(obj, name, limit):
        value = obj.get(name)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError("Invalid analysis field: " + name)
        return value.strip()

    selected = []
    seen = set()
    lane_counts = {"meme": 0, "brand": 0}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid recommendation")
        video_id = row.get("video_id")
        category = row.get("category")
        if video_id not in known or video_id in seen:
            raise ValueError("Unknown or duplicated recommended video ID")
        if category not in lane_counts or row.get("confidence") not in ("low", "medium", "high"):
            raise ValueError("Invalid category or confidence")
        seen.add(video_id)
        # 原始链接、标题及统计数据只从 API 数据回填。
        item = dict(known[video_id])
        item.update({"category": category, "confidence": row["confidence"]})
        for field in ("topic", "summary", "recommendation_reason", "adaptation_idea"):
            item[field] = text_field(row, field, 600)
        # 先校验每条结果，再按模型给出的顺序保留每类前五条。
        # 超额结果也必须通过来源与字段校验。
        if lane_counts[category] < 5:
            selected.append(item)
            lane_counts[category] += 1

    clean_themes = []
    for theme in themes:
        if not isinstance(theme, dict):
            raise ValueError("Invalid theme")
        ids = theme.get("evidence_video_ids")
        if not isinstance(ids, list) or not 2 <= len(ids) <= 10:
            raise ValueError("A recurring theme needs 2 to 10 supporting videos")
        if any(not isinstance(i, str) or i not in known for i in ids) or len(set(ids)) != len(ids):
            raise ValueError("Invalid theme evidence")
        clean_themes.append({
            "name": text_field(theme, "name", 100),
            "observation": text_field(theme, "observation", 600),
            "evidence_video_ids": ids,
        })

    subject = "Meme 与品牌创意选题日报 | " + report_date
    scope = "Meme：近 3 天；品牌创意：近 30 天。英文关键词；US 可观看地区筛选。"
    basis = "依据标题、简介和统计数据初筛；创意建议为策划推演，具体视频内容需点开核实。"
    plain = [subject, scope, "采集时间（UTC）：" + snapshot_at,
             "候选数：" + str(len(candidates)), basis, ""]
    esc = lambda s: html.escape(str(s), quote=True)
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><body>',
             "<h1>" + esc(subject) + "</h1>", "<p>" + esc(scope) + "</p>",
             "<p>采集时间（UTC）：" + esc(snapshot_at) + "；候选数：" + str(len(candidates)) + "</p>",
             "<p>" + esc(basis) + "</p>"]
    if clean_themes:
        parts.append("<h2>本次样本中的共同主题</h2>")
        plain.append("本次样本中的共同主题")
        for theme in clean_themes:
            plain.extend([theme["name"], theme["observation"]])
            parts.append("<h3>" + esc(theme["name"]) + "</h3><p>" + esc(theme["observation"]) + "</p>")
            for video_id in theme["evidence_video_ids"]:
                source = known[video_id]
                plain.append(source["title"] + " " + source["url"])
                parts.append('<p><a href="' + esc(source["url"]) + '">' + esc(source["title"]) + "</a></p>")
    for lane, label in [("meme", "Meme / 搞笑选题"), ("brand", "品牌创意参考")]:
        plain.extend(["", label])
        parts.append("<h2>" + label + "</h2>")
        lane_rows = [row for row in selected if row["category"] == lane]
        if not lane_rows:
            plain.append("本次样本暂无足够相关的推荐。")
            parts.append("<p>本次样本暂无足够相关的推荐。</p>")
        for row in lane_rows:
            count = lambda value: "未提供" if value is None else str(value)
            stats = "播放 " + count(row["view_count"]) + " / 点赞 " + count(row["like_count"]) + " / 评论 " + count(row["comment_count"])
            plain.extend([row["title"], row["url"], "频道：" + row["channel"],
                          "发布时间：" + row["published_at"], stats])
            parts.append('<h3><a href="' + esc(row["url"]) + '">' + esc(row["title"]) + "</a></h3>")
            parts.append("<p>频道：" + esc(row["channel"]) + "；发布时间：" + esc(row["published_at"]) + "</p>")
            parts.append("<p>" + esc(stats) + "</p>")
            for key, title in [("topic", "主题"), ("summary", "元数据摘要"),
                               ("recommendation_reason", "推荐理由"), ("adaptation_idea", "可尝试的创意")]:
                plain.append(title + "：" + row[key])
                parts.append("<p><b>" + title + "：</b>" + esc(row[key]) + "</p>")
            plain.append("元数据判断置信度：" + row["confidence"])
            parts.append("<p>元数据判断置信度：" + esc(row["confidence"]) + "</p>")
    parts.append("</body></html>")
    return {
        "subject": subject,
        "body_text": "\n".join(plain),
        "body_html": "\n".join(parts),
        "report_json": json.dumps({"date": report_date, "snapshot_at": snapshot_at,
                                   "candidate_count": len(candidates), "themes": clean_themes,
                                   "recommendations": selected}, ensure_ascii=False),
        "selected_count": len(selected),
    }
