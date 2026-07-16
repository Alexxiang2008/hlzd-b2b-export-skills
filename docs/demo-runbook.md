# HLZD B2B 出海 Skill 集 · Demo Runbook

> 这份 runbook 给两类人：
> - **HLZD 内部销售 / 客户成功**：用 9 Skill 帮真实业务跑 demo
> - **GitHub 上看到项目的潜在客户**：clone 仓库 5 分钟跑一遍完整链路

---

## 1. 这套 Skill 是干什么的

把"中国工业品卖到全球"分 9 个 Skill，覆盖从询盘评估到让步推演：

```
hlzd-inquiry-qualify      →  询盘 5 维评分 (Grade A/B/C/D)
hlzd-b2b-research         →  HS 编码 + UN Comtrade + Google Trends + 买家
hlzd-buyer-finder         →  阿里 + Volza 找海外买家
hlzd-market-report        →  9 节 HTML/Markdown 报告
hlzd-customer-due-...     →  5 维评分 + OFAC 制裁粗筛
hlzd-cold-outreach        →  6 类模板 × 双语 + 跟进序列
hlzd-solution-match       →  3 套 SKU 方案 (best / alt / cost)
hlzd-quotation-gen        →  FOB/CIF/DDP 3 套报价
hlzd-negotiation-...      →  3 轮 × 3 维让步推演
```

完整闭环见 [HLZD-出海技能集规划.md](HLZD-出海技能集规划.md)。

---

## 2. 5 分钟跑全套 demo

### 2.1 前置条件

```bash
# Python 3.10+
py --version

# 仓库克隆
git clone https://github.com/Alexxiang2008/hlzd-b2b-export-skills.git
cd hlzd-b2b-export-skills

# (可选) 跑测试套件 - 验证环境
py -m pytest skills/*/tests/ -q   # 336 tests
```

### 2.2 跑 3 个内置场景

```bash
py skills-demo/run_full_demo.py --all
```

预期输出：

```
================================================================
  scenario-saudi-rfq
  Saudi Aramco Trading Co. - OCTG Casing tender inquiry
================================================================
[1/7] inquiry-qualify ... grade=B total=85
[2/7] buyer-finder ... 4 mock buyers loaded
[3/7] customer-due-diligence ... evaluated=4 A/B=3 halt=1
[4/7] cold-outreach ... generated=0
[5/7] solution-match ... SKIPPED (halt)
[6/7] quotation-gen ... SKIPPED (halt)
[7/7] negotiation-playbook ... SKIPPED (halt)

================================================================
  scenario-latam-solar
  Latin American solar EPC - 50MW utility-scale project in Chile
================================================================
[1/7] inquiry-qualify ... grade=D total=48
[2/7] buyer-finder ... 3 mock buyers loaded
[3/7] customer-due-diligence ... evaluated=3 A/B=3 halt=0
[4/7] cold-outreach ... generated=3
[5/7] solution-match ... best=PV-MODULE-450W-MONO
[6/7] quotation-gen ... FOB=$534100.0 margin=15.00%
[7/7] negotiation-playbook ... decision=accept_round_3

================================================================
  scenario-fraud-blocked
  Suspected fraud inquiry - demonstrates compliance halt
================================================================
[1/7] inquiry-qualify ... grade=D total=20
...
```

3 个场景覆盖 3 类典型路径：

| Scenario | 路径 | 价值 |
|---|---|---|
| **saudi-rfq** | 半真询盘 → OCTG 命中 → 合规命中 Hezbollah → halt | 演示"真询盘的合规拦截" |
| **latam-solar** | 真询盘 → 全链路 → 报价 → round 3 accept | 演示"happy path" |
| **fraud-blocked** | 假询盘 → grade D | 演示"假询盘自动淘汰" |

每个 scenario 的完整 trace JSON 写到 `skills-demo/outputs/`：

```bash
ls skills-demo/outputs/
# scenario-saudi-rfq-trace.json
# scenario-latam-solar-trace.json
# scenario-fraud-blocked-trace.json
```

---

## 3. 用真实场景怎么做（HLZD 内部使用）

### 3.1 找客户 / 拿询盘

| 来源 | 如何录入 |
|---|---|
| **Alibaba 国际站** | 复制 RFQ 邮件正文 → 粘贴到 `skills/hlzd-inquiry-qualify/scripts/inquiry_parser.py --input file.txt` |
| **Made-in-China / 展会名片** | 先 OCR 成文本 → 同上 |
| **客户邮件直发** | 直接 `.eml` 文件 → `inquiry_parser.py --input msg.eml` |
| **WhatsApp / LinkedIn** | 截图 OCR |

### 3.2 数据录入（一次一个询盘）

准备 3 个 JSON：

```json
// 1. enquiry.json (input to inquiry-qualify)
//    直接用 --input 跑，或者 codegen 自动提取

// 2. scenario-saudi-rfq.json (我们的 demo 模板)
//    拷一份，改 5 个字段：
//      - inquiry.raw_text       (邮件正文)
//      - product_context        (产品 + HS + 产能)
//      - redlines               (min_price / max_lead / min_advance)
//      - sender_context         (发件人)
//      - competitor_risk        (bool)

// 3. mock_buyers (可选)
//    通过 buyer-finder 跑出来；或从 Volza 导出 CSV 转 JSON
```

### 3.3 跑全流程

```bash
# 1. 询盘评分 (Step 1)
py skills/hlzd-inquiry-qualify/scripts/inquiry_parser.py \
    --input customer_mail.txt --pretty \
    | tee step1_inquiry.json

# 2. 找买家 (Step 2 - 真跑需要 Brave API)
py skills/hlzd-buyer-finder/scripts/cli.py \
    --product "OCTG casing" --country SA \
    --output-json step2_buyers.json

# 3. 背调 (Step 3)
py skills/hlzd-customer-due-diligence/scripts/cli.py \
    --input step2_buyers.json \
    --output step3_diligence.json

# 4. 邮件 (Step 4 - 自动 skip halt 的 buyer)
py skills/hlzd-cold-outreach/scripts/cli.py \
    --input step3_diligence.json \
    --product "OCTG casing" \
    --sender-company "HLZD" \
    --output step4_emails.json

# 5. 方案 (Step 5)
py skills/hlzd-solution-match/scripts/cli.py \
    --input step5_input.json \
    --output step5_plans.json

# 6. 报价 (Step 6)
py skills/hlzd-quotation-gen/scripts/cli.py \
    --sku-json '{"sku":"OCTG-L80","currency":"USD","unit_price_per_ton":1480}' \
    --quantity 500 --country SA --incoterm FOB \
    --output step6_quote.json

# 7. 让步 (Step 7)
py skills/hlzd-negotiation-playbook/scripts/cli.py \
    --quote step6_quote.json \
    --response "We can pay USD 1300 per ton" \
    --redline-price 1300 \
    --output step7_negotiation.json
```

### 3.4 给客户发什么

把每步产出的 JSON 喂给 `hlzd-market-report` 跑出完整 PDF / HTML 报告：

```bash
py skills/hlzd-market-report/scripts/pipeline.py \
    --topic "OCTG casing - Saudi Aramco opportunity" \
    --from-research step6_quote.json \
    --output-html final_report.html --output-md final_report.md
```

打开 `final_report.html` 直接给客户 / 上传 Lark / 邮件附件。

---

## 4. 给客户 / 老板的"电梯版"demo

```bash
# 3 秒能演示 "一个询盘 → 自动评分 + 找买家 + 背调"
py skills-demo/run_full_demo.py --scenario scenario-latam-solar
```

5 步带 stdout 中文 / 英文解释：

```
[1/7] 询盘评分 → Grade B, total 85 → 真询盘，可跟
[2/7] 找买家   → 阿里搜 + Volza 3 个 A/B 级买家
[3/7] 背调     → 5 维评分 + OFAC 制裁粗筛，0 hit，pass
[4/7] 邮件     → 自动选 EPC 模板 + 西语 + Day 7/14 跟进
[5/7] 方案     → PV-MODULE-450W-MONO (最佳匹配)
[6/7] 报价     → FOB $534K, margin 15% (健康)
[7/7] 让步     → 客户坚持出 $X, 3 轮曲线, 建议 accept_round_3 (因竞品)
```

3 句话总结：
- "**1 个询盘 → 10 步骤手工 vs AI 7 步自动**：HR 时间从 8 小时降到 8 分钟"
- "**合规拦截自动**：Hezbollah 命中 → halt 跳过邮件"
- "**全链路 JSON 输出**：直接喂给 hlzd-market-report 出客户级 PDF"

---

## 5. 怎么准备场景（给真实询盘做 demo）

### 5.1 最小数据集

```json
{
  "inquiry": {"raw_text": "<邮件正文>"},
  "mock_buyers": [],   // 允许空，跑 will show 0 buyers
  "product_context": {
    "product": "OCTG casing",
    "product_category": "OCTG",
    "hs_code": "730429"
  },
  "redlines": {
    "min_acceptable_price": 1320,   // USD per ton
    "max_lead_time_days": 30,
    "min_advance_pct": 30
  },
  "sender_context": {
    "sender_company": "HLZD",
    "sender_name": "Alex",
    "sender_title": "International Sales Manager",
    "sender_email": "alex.xiang@hlzd.example",
    "sender_phone": "+86 138 0001 9999"
  },
  "competitor_risk": false
}
```

### 5.2 怎么 mock 买家

3 种来源：

| 来源 | 步骤 |
|---|---|
| **手工录入** | 从客户名片 / LinkedIn 抄 2-3 家 |
| **Volza 导出** | 把 CSV 转 JSON |
| **生成** | 让 GPT-4 模拟 5 家行业典型买家 |

`mock_buyers` 字段示例：
```json
[{
  "importer_name": "Aramco Trading Co.",
  "country": "Saudi Arabia",
  "contact_email": "buyer@aramco-trading.example",
  "linkedin": "https://linkedin.com/company/aramco-trading",
  "snippet": "50,000 employees with USD 400B revenue.",
  "usd_history": 8500000,           // 历史采购记录
  "customer_type": "End User"        // 必填：Manufacturer / EPC / Distributor / OEM / End User / Trader
}]
```

### 5.3 给客户发哪个 demo

| 客户类型 | 用哪个场景 | 调整 |
|---|---|---|
| **油气田** | scenario-saudi-rfq | 替换 country_iso / mock_buyers |
| **新能源** | scenario-latam-solar | 同上 |
| **建材 / 通用** | 新建 scenario-construction.json | 拷模板改 product |
| **风控演示** | scenario-fraud-blocked | 不改，直接跑 |

---

## 6. 数据隐私

- 所有 `*.example` 域都不存在 — demo 数据是合成
- mock_buyers 可直接放真实公司名（如果有书面授权）
- 不要把客户邮件正文 commit 到 repo — 加 `.gitignore` 忽略

---

## 7. 常见错误与排查

| Error | 原因 | 修复 |
|---|---|---|
| `ModuleNotFoundError: No module named 'lib'` | Skill X 的 lib 文件名不是 `lib.py` | 用 `_load_lib(..., module_filename='inquiry_parser.py')` |
| `Volza body length ≈ 11055` | Volza 屏蔽页 | 升级付费 / 切 ImportGenius |
| `Inquiry score always D` | 询盘信息太少 | 让客户补 D3 (应用场景) / D4 (资质) / D5 (项目背景) |
| `quotation margin < 10%` | 报价太低 / 汇率错 | 调 `--margin` / 检查 FX_RATES_USD |
| `negotiation decision = walk_away` | 价格 + 交期双红线破 | 重新谈或 senior 决策 |

---

## 8. 接下来看什么

跑完 3 个 demo 觉得太顺：

- 上 GitHub 给同事 / 客户：https://github.com/Alexxiang2008/hlzd-b2b-export-skills
- 把 demo 跑出来的 trace JSON 摘要分享给团队
- 用真实询盘拷一个 scenario 跑：cp scenarios/scenario-saudi-rfq.json scenarios/scenario-XYZ.json
- 接 Volza Pro / ImportGenius 跑真实 buyer-finder

觉得有不足：

- 看 VERSIONS.md 找到对应版本的 limitations
- 留言开 Issue：哪个 step 输出不准 / 哪个字段想要 / 哪个 case 想支持
- PR 直接改脚本：所有 Skill 都是 stdlib + 一两个 pip 包

---

*Documented for HLZD Cross-Border B2B · 2026*
