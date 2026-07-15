"""LinkedIn URL extraction from free text (deterministic regex)."""
from __future__ import annotations

import re
from typing import Optional, Tuple

LINKEDIN_URL_PATTERNS = [
    r"(https?://)?(?:www\.)?linkedin\.com/(?:in|company)/[a-zA-Z0-9\-_/]+",
    r"(https?://)?(?:www\.)?linkedin\.com/pub/[a-zA-Z0-9\-_/]+",
]


def extract_linkedin(text: str) -> Optional[str]:
    """从 snippet / about 文本中提取 LinkedIn URL。未找到返回 None。

    返回 URL 标准化：去掉 www. 前缀。
    """
    if not text:
        return None
    for pat in LINKEDIN_URL_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            url = m.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            # 去掉 www. 前缀以统一
            url = re.sub(r"^(https?://)www\.", r"\1", url)
            return url
    return None


def infer_linkedin_from_name(company_name: str, country: str = "") -> Tuple[str, str]:
    """Name → LinkedIn 搜索 URL（确定性，不发请求）。

    Returns: (search_url, suggested_handle)
    """
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", company_name.strip().lower()).strip("-")
    search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    handle = f"https://www.linkedin.com/company/{clean}"
    if country:
        search_url += f"&geoRegion={country}"
    return search_url, handle
