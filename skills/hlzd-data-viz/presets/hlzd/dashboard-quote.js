// HLZD 询盘分析看板（6 图组合）⭐
(function() {
  'use strict';

  window.HLZD_DASHBOARD_QUOTE = {
    /**
     * 绘制询盘分析看板
     * @param {string} containerId - 容器 DOM ID
     * @param {object} data - { funnel, kpi, trend, source, conversion, geo, period }
     */
    draw: function(containerId, data) {
      const container = d3.select('#' + containerId);
      container.selectAll('*').remove();
      container.style('font-family', 'Inter, sans-serif')
        .style('background', HLZD_COLORS.backgroundAlt)
        .style('padding', '20px');

      // 标题
      container.append('h2')
        .style('color', HLZD_COLORS.text)
        .style('margin', '0 0 20px 0')
        .text('📊 询盘分析看板 — ' + (data.period || '近 30 天'));

      // 网格布局
      const grid = container.append('div')
        .style('display', 'grid')
        .style('grid-template-columns', '1fr 1fr')
        .style('gap', '16px');

      // 1. 漏斗图（占 1 列）
      this._renderFunnel(grid.append('div').node(), data.funnel);

      // 2. KPI 卡片（占 1 列）
      this._renderKPIs(grid.append('div').node(), data.kpi);

      // 3. 询盘趋势（占 2 列）
      this._renderTrend(grid.append('div').node()
        .style('grid-column', '1 / span 2'), data.trend);

      // 4. 来源分布 + 转化率（占 1 列）
      this._renderSource(grid.append('div').node(), data.source);

      // 5. 转化率（占 1 列）
      this._renderConversion(grid.append('div').node(), data.conversion);

      // 6. 地理（占 2 列）
      if (data.geo) {
        this._renderGeo(grid.append('div').node()
          .style('grid-column', '1 / span 2'), data.geo);
      }
    },

    _renderFunnel: function(container, data) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('div').attr('id', 'dash-funnel');
      HLZD_FUNNEL.draw('dash-funnel', data);
    },

    _renderKPIs: function(container, kpis) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('h3').text('📈 KPI 总览').style('margin', '0 0 12px 0');

      const grid = div.append('div')
        .style('display', 'grid')
        .style('grid-template-columns', '1fr')
        .style('gap', '12px');

      (kpis || []).forEach(kpi => {
        const card = grid.append('div')
          .style('background', HLZD_COLORS.background)
          .style('padding', '12px')
          .style('border-radius', '6px')
          .style('border-left', `4px solid ${kpi.color || HLZD_COLORS.primary}`);

        card.append('div')
          .style('font-size', '12px')
          .style('color', HLZD_COLORS.textSecondary)
          .text(kpi.label);

        card.append('div')
          .style('font-size', '24px')
          .style('font-weight', 'bold')
          .style('color', kpi.color || HLZD_COLORS.primary)
          .text(kpi.value);

        if (kpi.trend) {
          card.append('div')
            .style('font-size', '11px')
            .style('color', kpi.trend > 0 ? HLZD_COLORS.accent : HLZD_COLORS.danger)
            .text((kpi.trend > 0 ? '↑ +' : '↓ ') + kpi.trend + '%');
        }
      });
    },

    _renderTrend: function(container, data) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('div').attr('id', 'dash-trend');

      // 简化折线图
      const ctx = HLZDChart.init('dash-trend', { width: 800, height: 250, title: '询盘趋势' });
      const lineData = data || [];
      const xScale = d3.scaleLinear()
        .domain([0, lineData.length - 1])
        .range([0, ctx.innerWidth]);
      const yMax = d3.max(lineData, d => d.value) || 100;
      const yScale = d3.scaleLinear()
        .domain([0, yMax * 1.1])
        .range([ctx.innerHeight, 0]);

      const line = d3.line()
        .x((d, i) => xScale(i))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

      ctx.g.append('path')
        .datum(lineData)
        .attr('fill', 'none')
        .attr('stroke', HLZD_COLORS.primary)
        .attr('stroke-width', 2)
        .attr('d', line);

      ctx.g.selectAll('.dot')
        .data(lineData)
        .join('circle')
        .attr('class', 'dot')
        .attr('cx', (d, i) => xScale(i))
        .attr('cy', d => yScale(d.value))
        .attr('r', 4)
        .attr('fill', HLZD_COLORS.primary);

      ctx.g.append('g')
        .attr('transform', `translate(0,${ctx.innerHeight})`)
        .call(d3.axisBottom(xScale).ticks(lineData.length).tickFormat((d, i) => lineData[i]?.date || ''));
      ctx.g.append('g').call(d3.axisLeft(yScale));
    },

    _renderSource: function(container, data) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('div').attr('id', 'dash-source');

      const ctx = HLZDChart.init('dash-source', { width: 380, height: 250, title: '询盘来源' });
      const pieData = data || [];
      const pie = d3.pie().value(d => d.value).sort(null);
      const arc = d3.arc().innerRadius(0).outerRadius(100);
      const color = d3.scaleOrdinal(HLZD_COLORS.categorical);

      const g = ctx.svg.append('g')
        .attr('transform', `translate(80, ${(ctx.height + 30) / 2})`);
      g.selectAll('path')
        .data(pie(pieData))
        .join('path')
        .attr('d', arc)
        .attr('fill', (d, i) => color(i))
        .attr('stroke', 'white')
        .attr('stroke-width', 2);

      // 图例
      const legend = ctx.svg.append('g')
        .attr('transform', `translate(220, 60)`);
      pieData.forEach((d, i) => {
        const row = legend.append('g').attr('transform', `translate(0, ${i * 20})`);
        row.append('rect').attr('width', 12).attr('height', 12).attr('fill', color(i));
        row.append('text').attr('x', 18).attr('y', 6).attr('dy', '0.35em')
          .style('font-size', '11px').text(`${d.source}: ${d.value}`);
      });
    },

    _renderConversion: function(container, data) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('div').attr('id', 'dash-conversion');

      const ctx = HLZDChart.init('dash-conversion', { width: 380, height: 250, title: '各阶段转化率' });
      const xScale = d3.scaleBand()
        .domain(data.map(d => d.stage))
        .range([0, ctx.innerWidth])
        .padding(0.2);
      const yScale = d3.scaleLinear()
        .domain([0, 1])
        .range([ctx.innerHeight, 0]);

      ctx.g.selectAll('rect')
        .data(data)
        .join('rect')
        .attr('x', d => xScale(d.stage))
        .attr('y', d => yScale(d.rate))
        .attr('width', xScale.bandwidth())
        .attr('height', d => ctx.innerHeight - yScale(d.rate))
        .attr('fill', (d, i) => HLZD_COLORS.gradients.sequential[i % 3]);

      ctx.g.append('g')
        .attr('transform', `translate(0,${ctx.innerHeight})`)
        .call(d3.axisBottom(xScale));
      ctx.g.append('g').call(d3.axisLeft(yScale).tickFormat(d => `${(d * 100).toFixed(0)}%`));
    },

    _renderGeo: function(container, data) {
      const div = d3.select(container)
        .style('background', 'white')
        .style('border-radius', '8px')
        .style('padding', '16px');
      div.append('div').attr('id', 'dash-geo');
      HLZD_GEO.draw('dash-geo', data);
    }
  };
})();
