"""
DeepSeek API：竞品分析报告生成、Profile 文档智能解析。
"""
import json
import os
import re

import httpx

from app.config import settings

# Profile 解析：主字段与数据库一致，便于写入
PROFILE_FIELD_KEYS = [
    "brand", "model", "full_name", "os", "chipset", "cpu", "gpu",
    "display_type", "display_size", "resolution", "refresh_rate",
    "battery", "charging", "main_camera", "selfie_camera", "memory_summary",
    "price", "launch_date", "weight", "dimensions",
]


def _call_chat(prompt: str, temperature: float = 0.3) -> tuple[bool, str | None, str | None]:
    """调用 DeepSeek 对话接口，返回 (success, content, error_message)。"""
    api_key = getattr(settings, "deepseek_api_key", None) or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return False, None, "未配置 DeepSeek API Key，请在 .env 或设置页配置 DEEPSEEK_API_KEY"
    base_url = getattr(settings, "deepseek_base_url", "https://api.deepseek.com").rstrip("/")
    model = getattr(settings, "deepseek_model", "deepseek-chat")
    timeout = getattr(settings, "deepseek_timeout_seconds", 120)
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                f"{base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            choice = data.get("choices")
            if not choice:
                return False, None, "API 返回格式异常"
            content = choice[0].get("message", {}).get("content") or ""
            return True, content.strip(), None
    except httpx.TimeoutException:
        return False, None, "请求 DeepSeek 超时，请稍后重试"
    except httpx.HTTPStatusError as e:
        return False, None, f"API 请求失败: {e.response.status_code} - {e.response.text[:200]}"
    except Exception as e:
        return False, None, f"调用失败: {str(e)}"


def build_profile_parse_prompt(raw_text: str) -> str:
    """构建让 AI 从 Profile 原文中抽取手机参数的 prompt。"""
    return (
        "你是一个手机产品参数提取助手。下面是一份手机产品 Profile 文档的原始文本（可能来自 PDF/Word/表格等），格式不统一。\n\n"
        "请仔细阅读全文，识别出所有与手机规格、参数相关的信息，并严格按照以下 JSON 格式输出（只输出这一份 JSON，不要其他说明）：\n\n"
        "{\n"
        '  "fields": {\n'
        '    "brand": "品牌名",\n'
        '    "model": "型号",\n'
        '    "full_name": "产品全称",\n'
        '    "os": "操作系统",\n'
        '    "chipset": "芯片/平台",\n'
        '    "cpu": "CPU",\n'
        '    "gpu": "GPU",\n'
        '    "display_type": "屏幕类型",\n'
        '    "display_size": "屏幕尺寸",\n'
        '    "resolution": "分辨率",\n'
        '    "refresh_rate": "刷新率",\n'
        '    "battery": "电池容量/续航",\n'
        '    "charging": "充电/快充",\n'
        '    "main_camera": "后摄/主摄",\n'
        '    "selfie_camera": "前摄/自拍",\n'
        '    "memory_summary": "内存/存储",\n'
        '    "price": "价格（仅数字或带单位）",\n'
        '    "launch_date": "发布时间",\n'
        '    "weight": "重量",\n'
        '    "dimensions": "尺寸"\n'
        "  },\n"
        '  "spec_items": [\n'
        '    {"spec_group": "分组名", "spec_key": "参数名", "spec_value": "参数值", "sort_order": 0},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "规则：\n"
        "1. 只填写从文档中明确出现或可合理推断出的字段，没有的键可省略或设为 null。\n"
        "2. spec_items 列出文档中出现的各项规格，spec_group 可用「显示」「性能」「电池」「相机」等分类。\n"
        "3. 价格若为区间或多种货币，取主要一种即可。\n"
        "4. 输出必须是合法 JSON，不要包含 markdown 代码块标记或多余文字。\n\n"
        "文档原文：\n"
        "---\n"
        f"{raw_text}\n"
        "---"
    )


def parse_profile_with_ai(raw_text: str) -> tuple[bool, dict[str, str | None], list[dict], str | None]:
    """
    使用 AI 从 Profile 原文中解析出结构化 fields 与 spec_items。
    返回: (success, fields_dict, spec_items_list, error_message)
    """
    if not (raw_text or raw_text.strip()):
        return False, {}, [], "文档无有效文本"
    # 限制长度，避免超出模型上下文
    max_chars = 22000
    text = raw_text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[后文已截断…]"
    prompt = build_profile_parse_prompt(text)
    ok, content, err = _call_chat(prompt, temperature=0.2)
    if not ok or not content:
        return False, {}, [], err or "AI 未返回内容"
    # 从回复中提取 JSON（可能被 markdown 包裹）
    json_str = content.strip()
    m = re.search(r"\{[\s\S]*\}", json_str)
    if m:
        json_str = m.group(0)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        return False, {}, [], f"AI 返回非合法 JSON: {e}"
    fields_raw = data.get("fields") or {}
    spec_items_raw = data.get("spec_items") or []
    # 只保留已知主字段
    fields = {}
    for k in PROFILE_FIELD_KEYS:
        v = fields_raw.get(k)
        if v is not None and str(v).strip():
            fields[k] = str(v).strip()
        else:
            fields[k] = None
    # 规范化 spec_items
    spec_items = []
    for i, item in enumerate(spec_items_raw):
        if not isinstance(item, dict):
            continue
        spec_items.append({
            "spec_group": str(item.get("spec_group") or "Imported").strip() or "Imported",
            "spec_key": str(item.get("spec_key") or "").strip() or "item",
            "spec_value": str(item.get("spec_value") or "").strip(),
            "sort_order": int(item.get("sort_order", i)),
        })
    return True, fields, spec_items, None


def build_compare_prompt(products_data: list[dict]) -> str:
    """
    根据多机型结构化参数构建发给 DeepSeek 的 prompt。
    要求 AI 输出：产品定位、目标用户、参数维度对比、价格带、优劣势、竞品关系、买点、风险、结论。
    """
    parts = [
        "你是一位专业的手机行业产品经理与市场分析师。请根据下面给出的多款手机机型参数，撰写一份「竞品分析报告」。",
        "要求：",
        "1. 使用专业、客观的口吻，避免空泛描述，必须结合给出的具体参数。",
        "2. 若某机型缺少价格或部分参数，请注明「基于现有数据分析」。",
        "3. 若存在发布时间差异，请考虑新老机型差异。",
        "4. 输出使用清晰小标题、项目符号和结论。",
        "",
        "报告必须包含以下部分：",
        "1. 产品定位判断",
        "2. 目标用户分析",
        "3. 参数维度对比（性能/屏幕/影像/续航/设计/通信）",
        "4. 市场价格带分析",
        "5. 每款机型的优势与短板",
        "6. 主要竞品关系判断",
        "7. 适合买点提炼",
        "8. 风险点与不足",
        "9. 最终结论与建议",
        "",
        "机型参数如下（JSON）：",
        json.dumps(products_data, ensure_ascii=False, indent=2),
    ]
    return "\n".join(parts)


def generate_competitor_report(products_data: list[dict]) -> tuple[bool, str | None, str | None]:
    """
    调用 DeepSeek API 生成竞品分析报告。
    products_data: 列表，每项为机型字段 dict（含 full_name, chipset, display_size, price 等）。
    返回: (success, report_markdown, error_message)
    """
    prompt = build_compare_prompt(products_data)
    ok, content, err = _call_chat(prompt, temperature=0.3)
    if not ok:
        return False, None, err
    return True, content, None
