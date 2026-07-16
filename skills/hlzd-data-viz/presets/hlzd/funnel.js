// HLZD 销售漏斗图 ⭐
// 数据：[{stage, value, conversion_rate}, ...]
(function() {
  'use strict';

  window.HLZD_FUNNEL = {
    /**
     * 绘制销售漏斗图
     * @param {string} containerId - 容器 DOM ID
     * @param {object} data - { stages: [...], total_inquiries, total_deals, overall_conversion, period }
     */
    draw: function(containerId, data) {
      if (!data || !data.stages || data.stages.length === 0) {
        console.error('[HLZD Funnel] 数据为空');
        return;
      }

      const stages = data.stages;
      const maxValue = stages[0].value;
      const width = 800;
      const height = 500;
      const margin = { top: 60, right: 100, bottom: 60, left: 100 };
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;
      const stageHeight = innerHeight / stages.length;

      // 初始化
      const ctx = HLZDChart.init(containerId, { width, height, margin, title: '销售漏斗图' });
      const { svg, g } = ctx;
      const tooltip = HLZDChart.createTooltip();

      // 绘制梯形
      const trapezoids = g.selectAll('.funnel-segment')
        .data(stages)
        .join('g')
        .attr('class', 'funnel-segment')
        .attr('transform', (d, i) => `translate(0, ${i * stageHeight})`);

      // 计算每段梯形的上宽和下宽
      trapezoids.each(function(d, i) {
        const topWidth = (d.value / maxValue) * innerWidth;
        const nextValue = i < stages.length - 1 ? stages[i + 1].value : d.value * 0.5;
        const bottomWidth = (nextValue / maxValue) * innerWidth;
        const xTop = (innerWidth - topWidth) / 2;
        const xBottom = (innerWidth - bottomWidth) / 2;
        const yTop = 0;
        const yBottom = stageHeight - 2;

        const path = d3.path();
        path.moveTo(xTop, yTop);
        path.lineTo(xTop + topWidth, yTop);
        path.lineTo(xBottom + bottomWidth, yBottom);
        path.lineTo(xBottom, yBottom);
        path.closePath();

        d3.select(this).append('path')
          .attr('d', path.toString())
          .attr('fill', HLZD_COLORS.gradients.sequential[i % 3])
          .attr('stroke', 'white')
          .attr('stroke-width', 2)
          .style('cursor', 'pointer');

        // 阶段名（左侧）
        d3.select(this).append('text')
          .attr('x', -10)
          .attr('y', stageHeight / 2)
          .attr('text-anchor', 'end')
          .attr('dy', '0.35em')
          .style('font-size', '14px')
          .style('font-weight', 'bold')
          .style('fill', HLZD_COLORS.text)
          .text(d.stage);

        // 数值 + 转化率（右侧）
        d3.select(this).append('text')
          .attr('x', innerWidth + 10)
          .attr('y', stageHeight / 2 - 8)
          .attr('dy', '0.35em')
          .style('font-size', '14px')
          .style('font-weight', 'bold')
          .style('fill', HLZD_COLORS.text)
          .text(d.value);

        d3.select(this).append('text')
          .attr('x', innerWidth + 10)
          .attr('y', stageHeight / 2 + 10)
          .attr('dy', '0.35em')
          .style('font-size', '11px')
          .style('fill', HLZD_COLORS.textSecondary)
          .text(d.conversion_rate ? `${(d.conversion_rate * 100).toFixed(1)}%` : '');

        // 交互
        d3.select(this).select('path')
          .on('mouseover', function(event) {
            d3.select(this).attr('opacity', 0.8);
            const next = i < stages.length - 1 ? stages[i + 1] : null;
            const html = `
              <b>${d.stage}</b><br>
              数量: <b style="color:${HLZD_COLORS.primary}">${d.value}</b><br>
              占比: ${(d.value / maxValue * 100).toFixed(1)}%<br>
              ${next ? `转化率: ${(next.value / d.value * 100).toFixed(1)}%` : ''}
            `;
            tooltip.show(html, event);
          })
          .on('mouseout', function() {
            d3.select(this).attr('opacity', 1);
            tooltip.hide();
          });
      });

      // 底部统计
      if (data.total_inquiries && data.total_deals) {
        const summary = svg.append('g')
          .attr('transform', `translate(0, ${height - 25})`);

        summary.append('text')
          .attr('x', 10)
          .attr('y', 0)
          .style('font-size', '12px')
          .style('fill', HLZD_COLORS.textSecondary)
          .text(`总询盘: ${data.total_inquiries} | 成交: ${data.total_deals} | 整体转化: ${(data.overall_conversion * 100).toFixed(2)}%`);
      }

      HLZDChart.addSource(svg, `期间: ${data.period || 'N/A'} | HLZD-D3可视化`, width);
    }
  };
})();
