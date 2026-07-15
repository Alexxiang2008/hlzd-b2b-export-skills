"""hlzd-buyer-finder.sources package.

三个 source adapter：
- alibaba: 搜供应商公司名（链路 A 第一阶段）
- volza: 搜竞对 → 找买家（链路 A 第二阶段 + 链路 B）
- keyword: 不经竞对，关键词直接搜进口商（链路 C）

每个 adapter 都设计为：
1. 可注入 `http_get` 函数用于 mock
2. 不依赖 Playwright / browser（v0.1 用 urllib + regex）
3. 自动处理 Volza blocked / 阿里 captcha 等边缘情况
4. 返回 (records, warnings) tuple
"""
