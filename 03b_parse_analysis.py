import json
import re


def main(text: str) -> dict:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("模型没有返回正文，请检查 LLM 的 text 输出")

    content = text.strip()
    # 兼容某些插件在正文前追加的完整思考标签。
    if content.startswith("<think>"):
        prefix = re.match(r"^<think>.*?</think>\s*", content, flags=re.DOTALL)
        if prefix is None:
            raise ValueError("模型输出的思考标签不完整，请检查输出是否被截断")
        content = content[prefix.end():].strip()

    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        content = fence.group(1)

    def reject_constant(value):
        raise ValueError("JSON 中不能出现非标准数字：" + value)

    try:
        data = json.loads(content, parse_constant=reject_constant)
    except json.JSONDecodeError as exc:
        raise ValueError("模型正文不是完整 JSON，请检查 text 是否为空、被截断或包含额外说明") from exc

    if not isinstance(data, dict):
        raise ValueError("模型应返回 JSON 对象")
    for field in ("themes", "recommendations"):
        if not isinstance(data.get(field), list):
            raise ValueError("模型输出缺少数组字段：" + field)

    # 这里只做 JSON 解析和顶层结构检查。
    # 视频 ID、字段类型、重复推荐等由后续 04_render.py 校验。
    return {"analysis": data}
