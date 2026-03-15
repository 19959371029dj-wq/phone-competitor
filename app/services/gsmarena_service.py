"""
GSMArena 爬虫服务：搜索机型、抓取详情页并解析为结构化参数。
使用 httpx + BeautifulSoup4 + lxml，带限流与异常处理。
"""
import json
import re
import time
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings

# 限流：请求间隔（秒），过短易触发 429
REQUEST_DELAY = getattr(settings, "gsmarena_request_delay_seconds", 20.0)
TIMEOUT = getattr(settings, "gsmarena_timeout_seconds", 30)
BASE_URL = "https://www.gsmarena.com"
# 模拟浏览器请求头，降低被限流概率
GSMARENA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.gsmarena.com/",
}
# 搜索结果缓存：同一关键词 10 分钟内不重复请求
_SEARCH_CACHE: dict[str, tuple[float, bool, list, str | None]] = {}
_SEARCH_CACHE_TTL = 600
_RETRY_WAIT_SEC = 120

# 规格表字段到 Product 主字段的映射（用于填充 products 表）
SPEC_KEY_TO_PRODUCT_FIELD = {
    "network technology": "network",
    "announced": "launch",
    "status": "status",
    "dimensions": "dimensions",
    "weight": "weight",
    "build": "build",
    "sim": "sim",
    "display type": "display_type",
    "size": "display_size",
    "resolution": "resolution",
    "os": "os",
    "chipset": "chipset",
    "cpu": "cpu",
    "gpu": "gpu",
    "card slot": "card_slot",
    "internal": "memory",
    "main camera": "main_camera",
    "selfie camera": "single",
    "loudspeaker": "loudspeaker",
    "3.5mm jack": "audio_jack",
    "wlan": "wlan",
    "bluetooth": "bluetooth",
    "positioning": "positioning",
    "nfc": "nfc",
    "infrared port": "infrared",
    "usb": "usb",
    "sensors": "sensors",
    "battery type": "battery",
    "charging": "charging",
    "colors": "colors",
    "models": "models",
    "sar": "sar",
    "price": "price",
    "protection": "protection",
    "video": "video",
    "features": "camera_features",
}


def _normalize_key(text: str) -> str:
    """规格键转小写、去多余空白。"""
    if not text:
        return ""
    return " ".join(text.lower().strip().split())


def _extract_slug_from_url(url: str) -> str | None:
    """从详情页 URL 提取 slug，如 xiaomi_14-12626.php。"""
    path = urlparse(url).path
    if not path or path == "/":
        return None
    return path.lstrip("/").split("/")[-1] if "/" in path else path


def search_phones(keyword: str) -> tuple[bool, list[dict], str | None]:
    """
    根据关键词搜索 GSMArena，返回候选机型列表。
    返回: (success, results, error_message)
    results 每项: { "name", "url", "img_src" }
    同一关键词 10 分钟内使用缓存，避免重复请求触发 429。
    """
    if not keyword or not keyword.strip():
        return False, [], "请输入搜索关键词"
    keyword = keyword.strip()
    cache_key = keyword.lower()
    now = time.time()
    if cache_key in _SEARCH_CACHE:
        expiry, ok, results, err = _SEARCH_CACHE[cache_key]
        if now < expiry:
            return ok, results, err
    search_url = f"{BASE_URL}/results.php3?sQuickSearch=yes&sName={keyword.replace(' ', '+')}"
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=GSMARENA_HEADERS) as client:
            time.sleep(REQUEST_DELAY)
            resp = client.get(search_url)
            if resp.status_code == 429:
                time.sleep(_RETRY_WAIT_SEC)
                resp = client.get(search_url)
            if resp.status_code == 429:
                msg = "GSMArena 请求过于频繁(429)。请等待 3～5 分钟后再试；或在 .env 中设置 GSMARENA_REQUEST_DELAY_SECONDS=30 并重启后端。"
                return False, [], msg
            if resp.status_code == 403:
                return False, [], "GSMArena 拒绝访问(403)，可能被临时限制，请稍后再试或更换网络。"
            resp.raise_for_status()
    except httpx.TimeoutException:
        return False, [], "请求 GSMArena 超时，请稍后重试"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return False, [], "GSMArena 请求过于频繁(429)，请等待 3～5 分钟后再试。"
        if e.response.status_code == 403:
            return False, [], "GSMArena 拒绝访问(403)，可能被临时限制，请稍后再试。"
        return False, [], f"请求失败: {str(e)}"
    except httpx.HTTPError as e:
        return False, [], f"请求失败: {str(e)}"

    soup = BeautifulSoup(resp.text, "lxml")
    results = []
    # 搜索页：结果在 div 内链接，指向机型详情页（含 -数字.php）
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if not re.search(r"-\d+\.php$", href):
            continue
        full_url = urljoin(BASE_URL, href)
        if "gsmarena.com" not in full_url or "results.php3" in full_url:
            continue
        name = (a.get_text() or "").strip()
        if not name:
            continue
        img = a.find("img")
        img_src = img.get("src") if img else None
        if img_src and not img_src.startswith("http"):
            img_src = urljoin(BASE_URL, img_src)
        results.append({"name": name, "url": full_url, "img_src": img_src})

    # 去重：同一 URL 只保留第一次
    seen = set()
    unique = []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    if not unique:
        out_err = "未找到匹配机型，请换关键词重试"
        _SEARCH_CACHE[cache_key] = (now + _SEARCH_CACHE_TTL, False, [], out_err)
        return False, [], out_err
    result_list = unique[:50]
    _SEARCH_CACHE[cache_key] = (now + _SEARCH_CACHE_TTL, True, result_list, None)
    return True, result_list, None


def fetch_phone_specs(url: str) -> tuple[bool, dict | None, str | None]:
    """
    抓取单机型详情页，解析为结构化数据，用于写入 Product + ProductSpecItem。
    返回: (success, data, error_message)
    data 结构:
      - 主字段与 Product 表一致（brand, model, full_name, display_type, ...）
      - raw_specs_json: 完整规格 JSON
      - raw_html: 可选，整页 HTML 或仅 specs 区域
      - spec_items: [ { spec_group, spec_key, spec_value, sort_order } ]
    """
    if not url or "gsmarena.com" not in url:
        return False, None, "无效的 GSMArena 链接"
    full_url = url if url.startswith("http") else urljoin(BASE_URL, url)
    try:
        with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=GSMARENA_HEADERS) as client:
            time.sleep(REQUEST_DELAY)
            resp = client.get(full_url)
            if resp.status_code == 429:
                time.sleep(_RETRY_WAIT_SEC)
                resp = client.get(full_url)
            if resp.status_code == 429:
                return False, None, "GSMArena 请求过于频繁(429)，请等待 3～5 分钟后再试。"
            if resp.status_code == 403:
                return False, None, "GSMArena 拒绝访问(403)，可能被临时限制，请稍后再试。"
            resp.raise_for_status()
            html = resp.text
    except httpx.TimeoutException:
        return False, None, "抓取详情页超时，请稍后重试"
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return False, None, "GSMArena 请求过于频繁(429)，请等待 3～5 分钟后再试。"
        if e.response.status_code == 403:
            return False, None, "GSMArena 拒绝访问(403)，可能被临时限制，请稍后再试。"
        return False, None, f"抓取失败: {str(e)}"
    except httpx.HTTPError as e:
        return False, None, f"抓取失败: {str(e)}"

    soup = BeautifulSoup(html, "lxml")
    # 标题：如 "Xiaomi 14 - Full phone specifications"
    title_el = soup.find("h1") or soup.find("title")
    full_name = (title_el.get_text() if title_el else "").replace(" - Full phone specifications", "").strip()
    if not full_name:
        full_name = (soup.find("title") or soup.find("h1") or "").get_text() if hasattr(soup.find("title"), "get_text") else ""
    # 简单推断 brand / model：取第一个词为 brand，其余为 model
    parts = full_name.split(None, 1)
    brand = parts[0] if parts else None
    model = parts[1] if len(parts) > 1 else (parts[0] if parts else None)

    slug = _extract_slug_from_url(full_url)
    out = {
        "brand": brand,
        "model": model,
        "full_name": full_name or None,
        "slug": slug,
        "source_type": "gsmarena",
        "source_url": full_url,
        "source_site": "GSMArena",
        "launch_date": None,
        "status": None,
        "os": None,
        "chipset": None,
        "cpu": None,
        "gpu": None,
        "display_type": None,
        "display_size": None,
        "resolution": None,
        "refresh_rate": None,
        "battery": None,
        "charging": None,
        "main_camera": None,
        "selfie_camera": None,
        "memory_summary": None,
        "price": None,
        "currency": None,
        "market_region": None,
        "sales_channel": None,
        "raw_specs_json": None,
        "raw_html": None,
        "spec_items": [],
    }

    # 解析 div#specs-list 下的所有 table
    specs_list = soup.find("div", id="specs-list")
    if not specs_list:
        # 部分页面可能用其他结构，尝试全页 table
        specs_list = soup

    all_specs = []
    current_group = ""
    sort_order = 0
    for table in (specs_list.find_all("table") if specs_list else []):
        for tr in table.find_all("tr"):
            th = tr.find("th")
            if th:
                current_group = (th.get_text() or "").strip()
            tds = tr.find_all("td")
            if len(tds) >= 2:
                ttl = tds[0]
                nfo = tds[1]
                key = _normalize_key(ttl.get_text() or "")
                val = (nfo.get_text() or "").strip()
                if not key:
                    continue
                all_specs.append({
                    "spec_group": current_group,
                    "spec_key": key,
                    "spec_value": val,
                    "sort_order": sort_order,
                })
                sort_order += 1
                # 映射到主字段
                key_lower = key.lower()
                if key_lower in ("display type", "type") and "display" in current_group.lower():
                    out["display_type"] = val or out["display_type"]
                elif key_lower == "size" and "display" in current_group.lower():
                    out["display_size"] = val or out["display_size"]
                elif key_lower == "resolution":
                    out["resolution"] = val or out["resolution"]
                elif key_lower == "os":
                    out["os"] = val or out["os"]
                elif key_lower == "chipset":
                    out["chipset"] = val or out["chipset"]
                elif key_lower == "cpu":
                    out["cpu"] = val or out["cpu"]
                elif key_lower == "gpu":
                    out["gpu"] = val or out["gpu"]
                elif key_lower in ("announced", "launch"):
                    out["launch_date"] = val or out["launch_date"]
                elif key_lower == "status":
                    out["status"] = val or out["status"]
                elif key_lower in ("internal", "memory"):
                    out["memory_summary"] = val or out["memory_summary"]
                elif "main camera" in current_group.lower() and key_lower in ("triple", "dual", "single", "quad", "main camera", "features"):
                    if "camera" in key_lower or key_lower in ("triple", "dual", "single", "quad"):
                        out["main_camera"] = val or out["main_camera"]
                elif "selfie" in current_group.lower() and (key_lower in ("single", "dual", "selfie camera") or "camera" in key_lower):
                    out["selfie_camera"] = val or out["selfie_camera"]
                elif key_lower in ("battery type", "type") and "battery" in current_group.lower():
                    out["battery"] = val or out["battery"]
                elif key_lower == "charging":
                    out["charging"] = val or out["charging"]
                elif key_lower == "price":
                    out["price"] = val  # 可能是字符串如 "€ 377.59"，先存字符串，入库时可解析
    out["spec_items"] = all_specs
    out["raw_specs_json"] = json.dumps(all_specs, ensure_ascii=False)
    # 可选：只存 specs 区域 HTML 减小体积
    out["raw_html"] = str(specs_list)[:50000] if specs_list else None

    # 从 raw 中补全 launch_date 等（若上面未填）
    for s in all_specs:
        g, k, v = (s.get("spec_group") or "").lower(), (s.get("spec_key") or "").lower(), s.get("spec_value")
        if not v:
            continue
        if "launch" in g and k in ("announced",):
            out["launch_date"] = out["launch_date"] or v
        if "display" in g and "refresh" in k:
            out["refresh_rate"] = out["refresh_rate"] or v

    return True, out, None
