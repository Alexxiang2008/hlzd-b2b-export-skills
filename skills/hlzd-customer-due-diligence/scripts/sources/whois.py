"""Domain / website heuristic parsing (deterministic)."""
from __future__ import annotations

import re
from typing import Optional


URL_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?((?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z0-9-]{2,63})",
    re.IGNORECASE,
)


def extract_website(text: str) -> Optional[str]:
    """从 snippet / about 中提取公司主页（不含 LinkedIn / 1688 等平台）。

    匹配完整域名（含 acme.example.com），不止顶级域。
    """
    if not text:
        return None
    for m in URL_PATTERN.finditer(text):
        domain = m.group(1)
        if not domain or "." not in domain:
            continue
        full = f"https://{domain}"
        # 排除社交平台 / 已知买家目录
        skip_domains = ("linkedin.com", "facebook.com", "twitter.com",
                         "alibaba.com", "made-in-china.com", "globalsources.com",
                         "go4worldbusiness.com", "1688.com")
        if any(s in full.lower() for s in skip_domains):
            continue
        return full
    return None


def infer_email_domain(website: str) -> Optional[str]:
    """提取邮箱域名（用于检查业务邮箱 vs 个人邮箱时用）。"""
    if not website:
        return None
    m = re.search(r"https?://(?:www\.)?((?:[a-zA-Z0-9-]+\.)+[a-zA-Z0-9-]+)", website)
    return m.group(1).lower() if m else None
