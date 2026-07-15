#!/usr/bin/env python3
"""
HLZD-B2B工业品调研 - Google Trends 关键词趋势查询
用法: python keyword_trends.py --kw "container house" "prefabricated house" --geo US --delay 12
"""

import argparse
import json
import sys
import time
import warnings
import io

warnings.filterwarnings('ignore')

# Windows GBK 兼容 — module-level wrap 在 pytest capture 等已关闭 buffer 场景会失败，
# 加 try/except 优雅降级；真正写 main() 时再 wrap 一次更稳。
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass  # buffer 可能已被 pytest 等关闭；不阻断导入

try:
    from pytrends.request import TrendReq
    from pytrends.exceptions import TooManyRequestsError
except ImportError:
    print("ERROR: pytrends 未安装，运行: pip install pytrends")
    sys.exit(1)


DEFAULT_DELAY = 12  # 默认查询间隔（秒）
MAX_RETRIES = 3   # 最大重试次数
RETRY_WAIT = 90    # 触发429后等待时间（秒）


def safe_sleep(seconds):
    """安全的延迟"""
    print(f"  等待 {seconds}秒...", file=sys.stderr)
    time.sleep(seconds)


def fetch_keyword_trends(pytrends, keyword, geo='US', timeframe='today 12-m', delay=DEFAULT_DELAY):
    """
    获取单个关键词的Google Trends数据，包含重试和延迟保护

    Returns:
        dict: 包含 interest_over_time, related_queries, interest_by_region
    """
    result = {
        'keyword': keyword,
        'geo': geo,
        'timeframe': timeframe,
        'interest_over_time': None,
        'related_queries': [],
        'interest_by_region': None,
        'error': None
    }

    # 1. 搜索热度时序
    for attempt in range(MAX_RETRIES):
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
            time.sleep(delay)

            trend_data = pytrends.interest_over_time()
            if not trend_data.empty:
                result['interest_over_time'] = trend_data.drop('isPartial', axis=1, errors='ignore').to_dict()
            break
        except TooManyRequestsError:
            if attempt < MAX_RETRIES - 1:
                print(f"  [!] 触发429限流，等待{RETRY_WAIT}秒后重试（第{attempt+1}次）...", file=sys.stderr)
                safe_sleep(RETRY_WAIT)
            else:
                result['error'] = 'TooManyRequestsError after retries'
        except Exception as e:
            result['error'] = str(e)
            break

    # 2. 相关查询词
    if not result['error']:
        try:
            related = pytrends.related_queries()
            key = list(related.keys())[0] if related else None
            if key and related[key]:
                if related[key].get('rising') is not None and not related[key]['rising'].empty:
                    result['related_queries'] = related[key]['rising'].head(20).to_dict('records')
        except Exception:
            pass  # 相关词不是关键，忽略错误

    safe_sleep(delay)

    # 3. 分地区热度（仅对全球查询）
    if geo == '' and not result['error']:
        try:
            pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo='')
            time.sleep(delay)
            regions = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True)
            if not regions.empty:
                top_regions = regions[regions[keyword] > 0].sort_values(keyword, ascending=False).head(10)
                result['interest_by_region'] = {r: int(v[keyword]) for r, v in top_regions.iterrows()}
        except Exception:
            pass

    return result


def fetch_multiple_keywords(keywords, geo='US', timeframe='today 12-m', delay=DEFAULT_DELAY):
    """
    批量查询多个关键词，自动处理延迟

    Args:
        keywords: 关键词列表
        geo: 地区代码（US/AE/''等）
        timeframe: 时间范围
        delay: 查询间隔（秒）

    Returns:
        list of dict
    """
    print(f"开始批量查询 {len(keywords)} 个关键词（间隔{delay}秒）...", file=sys.stderr)

    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 15))
    results = []

    for i, kw in enumerate(keywords):
        print(f"[{i+1}/{len(keywords)}] 查询: {kw}", file=sys.stderr)
        result = fetch_keyword_trends(pytrends, kw, geo, timeframe, delay)
        results.append(result)
        if i < len(keywords) - 1 and not result['error']:
            print(f"  完成，等待{delay}秒...", file=sys.stderr)

    return results


def format_trend_summary(results):
    """格式化输出"""
    lines = []
    lines.append("Google Trends 关键词趋势报告")
    lines.append("=" * 60)

    for res in results:
        kw = res['keyword']
        geo = res['geo'] or '全球'
        error = res['error']

        lines.append(f"\n关键词: {kw} | 地区: {geo}")

        if error:
            lines.append(f"  [错误] {error}")
            continue

        # 平均热度
        trend = res.get('interest_over_time')
        if trend:
            try:
                values = next(iter(trend.values()))
                if isinstance(values, dict):
                    numeric_vals = [v for v in values.values() if isinstance(v, (int, float))]
                    if numeric_vals:
                        avg = sum(numeric_vals) / len(numeric_vals)
                        mx = max(numeric_vals)
                        mn = min(numeric_vals)
                        lines.append(f"  平均热度: {avg:.1f} | 峰值: {mx:.0f} | 低值: {mn:.0f} (0-100标准化)")
            except Exception:
                pass

        # 相关上升词
        queries = res.get('related_queries', [])
        if queries:
            lines.append(f"  相关上升词 (搜索量增长最快):")
            for item in queries[:10]:
                query = item.get('query', 'N/A')
                value = item.get('value', 'N/A')
                lines.append(f"    + {query}: {value}")

        # 分地区
        regions = res.get('interest_by_region')
        if regions:
            lines.append(f"  热度最高地区:")
            for region, score in list(regions.items())[:5]:
                lines.append(f"    {region}: {score}")

    return '\n'.join(lines)


def export_json(results, output_path):
    """导出为JSON"""
    export_data = {
        'query_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_keywords': len(results),
        'results': results
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    print(f"JSON已保存: {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description='HLZD-B2B工业品调研 - Google Trends关键词趋势查询'
    )
    parser.add_argument('--kw', nargs='+', required=True, help='关键词列表，如 "container house" "prefabricated house"')
    parser.add_argument('--geo', default='US',
                        help='地区代码（US/AE/ZA空值代表全球），默认US')
    parser.add_argument('--timeframe', default='today 12-m',
                        help='时间范围，默认 today 12-m（12个月）')
    parser.add_argument('--delay', type=int, default=DEFAULT_DELAY,
                        help=f'查询间隔秒数（防429），默认{DEFAULT_DELAY}')
    parser.add_argument('--output', help='JSON输出文件路径（可选）')

    args = parser.parse_args()

    # 强制最小延迟
    if args.delay < 10:
        print(f"[警告] 延迟{args.delay}秒过短，易触发429，自动调整为10秒", file=sys.stderr)
        args.delay = 10

    print(f"配置: 关键词={args.kw}, 地区={args.geo or '全球'}, 延迟={args.delay}秒", file=sys.stderr)

    try:
        results = fetch_multiple_keywords(args.kw, args.geo, args.timeframe, args.delay)

        # 打印报告
        summary = format_trend_summary(results)
        print('\n' + summary)

        # JSON导出
        if args.output:
            export_json(results, args.output)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
