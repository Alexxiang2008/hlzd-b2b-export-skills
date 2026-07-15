#!/usr/bin/env python3
"""
HLZD-B2B工业品调研 - 买家线索搜索（开源方案）
用法: python buyer_search.py --query "container house mining camp" --max 20
依赖: pip install ddgs  # 包名已从duckduckgo-search重命名
"""

import argparse
import json
import sys
import time
import warnings
import io
import re

warnings.filterwarnings('ignore')

# Windows GBK 兼容：输出 UTF-8，避免阿拉伯/中文乱码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


try:
    from ddgs import DDGS  # pip install ddgs（新版，包名已重命名）
except ImportError:
    try:
        from duckduckgo_search import DDGS  # pip install duckduckgo-search（旧版）
        import warnings as _w
        _w.filterwarnings('ignore', message='.*renamed to.*')
    except ImportError:
        print("请安装: pip install ddgs")
        sys.exit(1)


# B2B买家线索分类关键词（用于过滤和识别买家类型）
BUYER_TYPE_KEYWORDS = {
    '矿业/油田营地': [
        'mining', 'oil', 'gas', 'camp', 'accommodation', 'worker',
        'labor camp', 'oilfield', 'upstream', 'drilling', 'exploration',
        'petroleum', 'hydrocarbon', 'extraction', 'seismic', 'rig',
        'oil terminal', 'refinery', 'downstream', 'energy',
    ],
    'EPC/总包': [
        'EPC', 'contractor', 'construction', 'engineering',
        'project developer', 'builder', 'general contractor',
        'turnkey', 'civil works', 'fabrication',
    ],
    '酒店/文旅': [
        'hotel', 'resort', 'tourism', 'hospitality', 'glamping',
        'campground', 'lodge', 'guesthouse', 'safari',
    ],
    '政府/NGO': [
        'government', 'municipal', 'UN', 'NGO', 'humanitarian',
        'refugee', 'UNDP', 'USAID', 'World Bank', 'ADB', 'IFC',
        'public works', 'public sector', 'ministry',
    ],
    '贸易商/进口商': [
        'importer', 'trader', 'distributor', 'wholesaler',
        'trading house', 'trading company', 'importexport',
        'middle east trader', 'Gulf trader',
    ],
    '房地产/开发商': [
        'developer', 'real estate', 'property', 'housing',
        'residential', 'commercial development', 'infrastructure',
    ],
    '石油设备商': [
        'OCTG', 'casing', 'tubing', 'drill pipe',
        'API 5CT', 'API 5L', 'line pipe', 'pipeline',
        'oilfield equipment', 'petroleum machinery', 'wellhead',
        'completion', 'subsurface',
    ],
}


# 硬性过滤URL模式（完全不返回）
HARD_SKIP_URL_PATTERNS = [
    'alibaba.com', 'made-in-china.com', 'globalsources.com',
    'indiamart.com', 'ec21.com', 'tradekey.com', 'ecplaza.net',
    'supplier', '/manufacturer', '/products/', '/b2b/',
    'containerstore.com', 'amazon.com', 'ebay.com',
    '/locations/', '/sale', '/rent/', '/buy/', '/price/',
    '/shop/', '/store/', '/order/',
    '404', 'error', 'login', 'signin', 'register',
]

# 软性过滤关键词（同时出现在URL+内容才跳过）
SOFT_SKIP_PATTERNS = [
    'shipping container', 'sea container', 'cargo container',
    'container shipping', 'container for sale',
    'MDF', 'molding', 'door casing', 'architectural molding',
    'fluted casing', 'casing trim', 'base molding',
    'computer casing', 'PC case', 'chassis', 'server rack',
    'oil filter housing', 'water filter housing',
    'solar panel mounting', 'curtain wall',
    'youtube.com/watch', 'tiktok.com',
]


def classify_buyer(url, title, snippet):
    """根据URL和内容判断买家类型"""
    text = f"{url} {title} {snippet}".lower()

    # 优先匹配石油设备类型（专用品类，非通用casing）
    for keyword in BUYER_TYPE_KEYWORDS['石油设备商']:
        if keyword.lower() in text:
            return '石油设备商'

    for buyer_type, keywords in BUYER_TYPE_KEYWORDS.items():
        if buyer_type == '石油设备商':
            continue
        for kw in keywords:
            if kw.lower() in text:
                return buyer_type
    return '其他'


def is_noise(url, title, snippet):
    """
    判断结果是否为噪音（来自供应商或无关内容）

    Returns: True = 噪音应跳过, False = 有效结果
    """
    url_lower = url.lower()
    text_lower = f"{url_lower} {title} {snippet}".lower()

    # 硬性：URL直接匹配
    for p in HARD_SKIP_URL_PATTERNS:
        if p in url_lower:
            return True

    # 软性：URL+内容同时匹配
    matched_soft = any(p in text_lower for p in SOFT_SKIP_PATTERNS)
    # 如果URL是石油/建筑类B2B平台，也要过滤
    b2b_noise = any(p in url_lower for p in [
        'globalsources', 'ecplaza', 'ec21', 'tradekey',
        'homedepot.com', 'lowes.com',  # 建材零售
        'pinterest.com',  # 装饰图
        'hackernoon.com',  # 技术博客
        'libyanjobs',  # 求职非采购
    ])
    if matched_soft and b2b_noise:
        return True

    # 过滤YouTube/社交媒体（采购参考价值低）
    if 'youtube.com' in url_lower and (
        'OCTG' not in text_lower and 'casing' not in text_lower
    ):
        return True

    return False


def search_buyers(product_keywords, market=None, max_results=20, delay=2):
    """
    搜索B2B买家线索

    Args:
        product_keywords: 产品关键词列表（支持短语，如 ["OCTG casing", "prefab"]）
        market: 市场关键词（国家/地区）
        max_results: 最大结果数
        delay: 查询间隔（秒）

    Returns:
        list of dict: 买家线索列表
    """
    results = []
    seen_urls = set()

    # 构建搜索查询：产品关键词 + 市场 + B2B角色词
    b2b_intents = [
        'importer buyer',
        'procurement purchaser',
        'project developer',
    ]

    queries = []
    for kw in product_keywords:
        if market:
            for intent in b2b_intents:
                queries.append(f'"{kw}" {market} {intent} 2024')
        else:
            for intent in b2b_intents:
                queries.append(f'"{kw}" {intent} 2024')

    # 去重，限制查询数量防止过度延迟
    queries = list(dict.fromkeys(queries))
    max_queries = min(len(queries), 12)
    queries = queries[:max_queries]

    print(f"开始搜索 {len(queries)} 个查询（间隔{delay}秒）...", file=sys.stderr)

    for qi, query in enumerate(queries):
        print(f"[{qi+1}/{len(queries)}] 查询: {query[:70]}...", file=sys.stderr)
        try:
            ddgs = DDGS()
            try:
                # 每个查询取少量结果，控制总量
                per_query = max(3, max_results // min(len(queries), 1))
                for r in ddgs.text(query, max_results=per_query):
                    url = r.get('href', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = r.get('title', '')
                    snippet = r.get('body', '')

                    if is_noise(url, title, snippet):
                        continue

                    buyer_type = classify_buyer(url, title, snippet)
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet[:200],
                        'buyer_type': buyer_type,
                        'query': query
                    })
            finally:
                try:
                    del ddgs
                except Exception:
                    pass
        except Exception as e:
            print(f"  [错误] {e}", file=sys.stderr)
            time.sleep(delay)

        time.sleep(delay)

    return results


def search_procurement_tenders(product_keywords, market=None, max_results=15, delay=3):
    """
    搜索项目招标信息（开源招标平台）
    """
    results = []
    seen_urls = set()

    queries = []
    for kw in product_keywords:
        if market:
            queries.append(f'"{kw}" {market} tender EOI expression of interest 2024')
            queries.append(f'site:go4worldbusiness.com "{kw}" {market} buyer')
        else:
            queries.append(f'"{kw}" tender expression of interest')
            queries.append(f'site:go4worldbusiness.com "{kw}" buyer')

    queries = list(dict.fromkeys(queries))[:6]

    print(f"搜索招标信息 {len(queries)} 个查询（间隔{delay}秒）...", file=sys.stderr)

    for query in queries:
        try:
            ddgs = DDGS()
            try:
                for r in ddgs.text(query, max_results=5):
                    url = r.get('href', '')
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    title = r.get('title', '')
                    if '404' in title or not title:
                        continue
                    # 过滤非招标类页面
                    if any(p in url.lower() for p in ['login', 'signup', '/ads/', 'tracking']):
                        continue

                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': r.get('body', '')[:200],
                        'type': '招标'
                    })
            finally:
                try:
                    del ddgs
                except Exception:
                    pass
        except Exception as e:
            print(f"  [错误] {e}", file=sys.stderr)

        time.sleep(delay)

    return results


def format_results(buyer_results, tender_results):
    """格式化输出"""
    lines = []
    lines.append("B2B买家线索 + 招标信息报告")
    lines.append("=" * 60)

    # 买家线索汇总
    if buyer_results:
        by_type = {}
        for r in buyer_results:
            bt = r['buyer_type']
            if bt not in by_type:
                by_type[bt] = []
            by_type[bt].append(r)

        lines.append(f"\n买家线索 ({len(buyer_results)} 条，按类型分组）")

        for buyer_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            lines.append(f"\n  【{buyer_type}】({len(items)}条）")
            for item in items[:5]:
                lines.append(f"    {item['title'][:65]}")
                lines.append(f"    → {item['url'][:75]}")

    # 招标信息
    if tender_results:
        lines.append(f"\n\n招标信息 ({len(tender_results)} 条）")
        for t in tender_results[:10]:
            lines.append(f"  {t['title'][:65]}")
            lines.append(f"  → {t['url'][:75]}")

    if not buyer_results and not tender_results:
        lines.append("\n[无结果] 请尝试更换产品关键词，使用引号短语减少噪音")

    return '\n'.join(lines)


def export_json(buyer_results, tender_results, output_path):
    """导出JSON"""
    data = {
        'query_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_buyers': len(buyer_results),
        'total_tenders': len(tender_results),
        'buyers': buyer_results,
        'tenders': tender_results
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON已保存: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='HLZD-B2B工业品调研 - 买家线索搜索（开源DuckDuckGo方案）'
    )
    parser.add_argument('--query', required=True,
                        help='产品关键词，多个用空格分隔，支持引号短语')
    parser.add_argument('--market', default='',
                        help='市场关键词列表（空格分隔），如 "UAE" "Saudi Arabia"')
    parser.add_argument('--max', type=int, default=20,
                        help='最大买家线索数（默认20）')
    parser.add_argument('--tenders', action='store_true',
                        help='同时搜索招标信息')
    parser.add_argument('--delay', type=int, default=3,
                        help='查询间隔秒数（默认3，ddgs较稳定）')
    parser.add_argument('--output', help='JSON输出文件路径（可选）')

    args = parser.parse_args()

    # 支持 --query "seamless pipe" "oilfield" 两种模式：
    # - 多个空格分隔的单词 → 各自独立关键词
    # - 引号包裹的短语 → 整体作为一个关键词
    tokens = re.findall(r'"[^"]+"|\S+', args.query)
    keywords = [t.strip('"') for t in tokens]
    markets = args.market.split() if args.market else []

    print(f"配置: 关键词={keywords}, 市场={markets or '全球'}, 延迟={args.delay}秒",
          file=sys.stderr)

    try:
        # 搜索买家线索（支持多市场轮询）
        if markets:
            buyers = []
            per_market = args.max // len(markets) + 3
            for mkt in markets:
                print(f"\n>> 市场: {mkt}", file=sys.stderr)
                b = search_buyers(keywords, mkt, per_market, args.delay)
                buyers.extend(b)
        else:
            buyers = search_buyers(keywords, None, args.max, args.delay)

        # 去重（URL唯一）
        seen_urls = set()
        buyers_dedup = []
        for b in buyers:
            if b['url'] not in seen_urls:
                seen_urls.add(b['url'])
                buyers_dedup.append(b)
        buyers = buyers_dedup

        # 搜索招标信息
        tenders = []
        if args.tenders:
            tenders = search_procurement_tenders(keywords, args.market, 15, args.delay)

        # 输出报告
        report = format_results(buyers, tenders)
        print('\n' + report)

        # JSON导出
        if args.output:
            export_json(buyers, tenders, args.output)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
