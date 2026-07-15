#!/usr/bin/env python3
"""
HLZD-B2B工业品调研 - UN Comtrade 贸易数据查询
用法: python trade_data.py --hs 9406 --reporter us --period 2023 [--output data.json]
"""

import argparse
import json
import sys
import io

# Windows GBK 兼容 — module-level wrap 在 pytest capture 等已关闭 buffer 场景会失败，
# 加 try/except 优雅降级；真正写 main() 时再 wrap 一次更稳。
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        pass  # buffer 可能已被 pytest 等关闭；不阻断导入

try:
    import comtradeapicall
except ImportError:
    print("ERROR: comtradeapicall 未安装，运行: pip install comtradeapicall")
    sys.exit(1)


# 国家代码简表（ISO3 -> UN Comtrade数字码，部分常用）
COUNTRY_CODE_MAP = {
    'us': '842', 'usa': '842',
    'cn': '156', 'chn': '156', 'china': '156',
    'de': '276', 'deu': '276', 'germany': '276',
    'gb': '826', 'gbr': '826', 'uk': '826',
    'ae': '784', 'are': '784', 'dubai': '784',
    'za': '710', 'zaf': '710', 'southafrica': '710',
    'au': '036', 'aus': '036', 'australia': '036',
    'sa': '682', 'sau': '682', 'saudi': '682', 'saudi arabia': '682',
    'qa': '634', 'qat': '634',
    'kw': '414', 'kwt': '414',
    'ng': '566', 'nga': '566', 'nigeria': '566',
    'ke': '404', 'ken': '404', 'kenya': '404',
    'gh': '288', 'gha': '288',
    'tz': '834', 'tza': '834',
    'sg': '702', 'sgp': '702',
    'my': '458', 'mys': '458',
    'id': '360', 'idn': '360',
    'vn': '704', 'vnm': '704',
    'br': '076', 'bra': '076',
    'mx': '484', 'mex': '484',
    'ca': '124', 'can': '124',
    'world': '0',
}

COUNTRY_NAME_MAP = {
    '842': 'United States',
    '156': 'China',
    '276': 'Germany',
    '826': 'United Kingdom',
    '784': 'United Arab Emirates',
    '710': 'South Africa',
    '036': 'Australia',
    '566': 'Nigeria',
    '404': 'Kenya',
    '288': 'Ghana',
    '834': 'Tanzania',
    '702': 'Singapore',
    '458': 'Malaysia',
    '360': 'Indonesia',
    '704': 'Viet Nam',
    '076': 'Brazil',
    '484': 'Mexico',
    '124': 'Canada',
    '392': 'Japan',
    '356': 'India',
    '380': 'Italy',
    '528': 'Netherlands',
    '616': 'Poland',
    '724': 'Spain',
    '752': 'Sweden',
    '756': 'Switzerland',
    '792': 'Turkey',
    '410': 'Korea',
    '702': 'Singapore',
}


def parse_reporter(code_str):
    """将 us/cn/UK 等简写转为UN Comtrade数字码"""
    code_str = code_str.strip().lower()
    if code_str in COUNTRY_CODE_MAP:
        return COUNTRY_CODE_MAP[code_str]
    # 尝试直接数字
    if code_str.isdigit():
        return code_str
    return None


def get_market_data(hs_code, reporter_str, period='2023', max_records=200):
    """
    查询UN Comtrade数据

    Args:
        hs_code: HS编码，如 9406
        reporter_str: 申报国简写，如 us/ae
        period: 年份，如 2023
        max_records: 最大记录数

    Returns:
        DataFrame
    """
    reporter = parse_reporter(reporter_str)
    if not reporter:
        raise ValueError(f"未知国家代码: {reporter_str}")

    print(f"查询: HS={hs_code}, 申报国={reporter}, 年份={period}", file=sys.stderr)

    df = comtradeapicall.previewFinalData(
        typeCode='C',          # 商品贸易
        freqCode='A',          # 年度
        clCode='HS',           # HS分类
        period=period,
        reporterCode=reporter,
        cmdCode=str(hs_code),
        flowCode='M',          # 进口
        partnerCode=None,       # 不过滤，看所有来源国
        partner2Code=None,
        customsCode=None,
        motCode=None,
        maxRecords=max_records,
        format_output='JSON',
        includeDesc=True
    )
    return df


def format_results(df, hs_code):
    """将DataFrame格式化为易读报告"""
    # 找World总计
    total_row = df[df['partnerDesc'] == 'World']
    if not total_row.empty:
        total_value = total_row['primaryValue'].values[0]
        total_qty = total_row['netWgt'].values[0]
        total_str = f"进口总额: ${total_value/1e6:.1f}M USD ({total_qty/1e6:.1f}M kg)"
    else:
        total_value = df['primaryValue'].sum()
        total_str = f"进口总额: ${total_value/1e6:.1f}M USD (合计)"

    # 排除World总计
    df_countries = df[df['partnerDesc'] != 'World'].copy()
    df_countries = df_countries.sort_values('primaryValue', ascending=False)

    total_pct = total_row['primaryValue'].values[0] if not total_row.empty else total_value

    lines = []
    lines.append(f"HS {hs_code} 调研报告")
    lines.append("=" * 50)
    lines.append(f"申报国市场: {df['reporterDesc'].iloc[0] if 'reporterDesc' in df.columns else 'N/A'}")
    lines.append(f"年份: {df['refYear'].iloc[0] if 'refYear' in df.columns else 'N/A'}")
    lines.append(f"数据来源: UN Comtrade (comtradeapi.un.org)")
    lines.append("-" * 50)
    lines.append(f"总记录数: {len(df_countries)} 个供应国")
    lines.append(f"{total_str}")
    lines.append("-" * 50)
    lines.append(f"{'排名':<4} {'供应国':<30} {'进口额':>15} {'重量(吨)':>12} {'占比':>7}")
    lines.append("-" * 70)

    china_rank = None
    for i, (_, row) in enumerate(df_countries.head(15).iterrows()):
        country = row.get('partnerDesc', row.get('partnerLabel', 'N/A'))
        value = row.get('primaryValue', 0)
        qty = row.get('netWgt', 0)
        pct = value / total_pct * 100 if total_pct else 0
        flag = ' <<<' if 'China' in country else ''
        if 'China' in country:
            china_rank = i + 1
        lines.append(
            f"{i+1:2d}. {country:<30} ${value/1e6:>10.1f}M "
            f"{qty/1000:>10,.0f}t {pct:>5.1f}%{flag}"
        )

    if china_rank:
        lines.append(f"\n中国排名: 第 {china_rank} 位")
    else:
        lines.append(f"\n中国市场数据: 未出现在Top15")

    return '\n'.join(lines)


def export_json(df, hs_code, reporter_str):
    """导出为结构化JSON"""
    total_row = df[df['partnerDesc'] == 'World']
    total_value = total_row['primaryValue'].values[0] if not total_row.empty else 0

    df_countries = df[df['partnerDesc'] != 'World'].copy()
    df_countries = df_countries.sort_values('primaryValue', ascending=False)

    countries = []
    for _, row in df_countries.iterrows():
        countries.append({
            'country': row.get('partnerDesc', 'N/A'),
            'code': row.get('partnerISO', 'N/A'),
            'import_value_usd': float(row.get('primaryValue', 0)),
            'import_weight_kg': float(row.get('netWgt', 0)),
            'share_pct': round(float(row.get('primaryValue', 0)) / total_value * 100, 2) if total_value else 0
        })

    return {
        'hs_code': hs_code,
        'reporter': reporter_str,
        'total_import_value_usd': float(total_value),
        'data_source': 'UN Comtrade (comtradeapi.un.org)',
        'countries': countries
    }


def main():
    parser = argparse.ArgumentParser(
        description='HLZD-B2B工业品调研 - UN Comtrade贸易数据查询'
    )
    parser.add_argument('--hs', required=True, help='HS编码，如 9406')
    parser.add_argument('--reporter', required=True, help='申报国简写，如 us/ae/cn')
    parser.add_argument('--period', default='2023', help='年份，如 2023')
    parser.add_argument('--output', help='JSON输出文件路径（可选）')
    parser.add_argument('--max', type=int, default=200, help='最大记录数（默认200）')

    args = parser.parse_args()

    try:
        df = get_market_data(args.hs, args.reporter, args.period, args.max)

        # 输出报告
        report = format_results(df, args.hs)
        print(report)

        # JSON导出
        if args.output:
            json_data = export_json(df, args.hs, args.reporter)
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"\nJSON已保存: {args.output}", file=sys.stderr)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
