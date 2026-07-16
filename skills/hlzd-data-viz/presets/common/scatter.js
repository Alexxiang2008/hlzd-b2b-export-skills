// 通用散点图（fork 自 chrisvoncsefalvay + HLZD 品牌色适配）
// 数据格式：[{ x, y, label, category?, size? }, ...]
// 用途：相关性分析（询盘量 vs 成交率）、价格 vs 数量、产能 vs 销量等
(function() {
  'use strict';

  /**
   * 散点图
   * @param {string} containerId - 容器 DOM ID
   * @param {Array<object>} data - 数据点数组 [{ x, y, label, category?, size? }]
   * @param {object} options - { title, xLabel, yLabel, xField, yField, showLabels }
   */
  window.HLZD_SCATTER = {
    draw: function(containerId, data, options) {
      options = options || {};
      if (!data || data.length === 0) return;

      // 数据归一化（支持 {x, y} 或 {val1, val2} 自定义字段名）
      const xField = options.xField || 'x';
      const yField = options.yField || 'y';
      const points = data.map(function(d) {
        return {
          x: typeof d[xField] === 'number' ? d[xField] : Number(d[xField]),
          y: typeof d[yField] === 'number' ? d[yField] : Number(d[yField]),
          label: d.label || d.name || '',
          category: d.category || d.group || 'default',
          size: typeof d.size === 'number' ? d.size : (Number(d.size) || 5)
        };
      }).filter(function(d) {
        return !isNaN(d.x) && !isNaN(d.y);
      });

      if (points.length === 0) return;

      const ctx = HLZDChart.init(containerId, {
        width: 800,
        height: 500,
        title: options.title || '散点图（相关性分析）'
      });
      const svg = ctx.svg;
      const g = ctx.g;
      const innerWidth = ctx.innerWidth;
      const innerHeight = ctx.innerHeight;

      // 提取唯一的 category（用于颜色分组）
      const categories = Array.from(new Set(points.map(function(d) { return d.category; })));

      // 配色：HLZD 品牌色 + schemeCategory10 备选
      const colorScale = categories.length <= 5
        ? d3.scaleOrdinal([
            HLZD_COLORS.primary,
            HLZD_COLORS.secondary,
            HLZD_COLORS.accent,
            HLZD_COLORS.warning,
            HLZD_COLORS.danger
          ]).domain(categories)
        : d3.scaleOrdinal(d3.schemeCategory10).domain(categories);

      // 比例尺
      const xExtent = d3.extent(points, function(d) { return d.x; });
      const yExtent = d3.extent(points, function(d) { return d.y; });
      const xScale = d3.scaleLinear()
        .domain([xExtent[0], xExtent[1]])
        .range([0, innerWidth])
        .nice();
      const yScale = d3.scaleLinear()
        .domain([yExtent[0], yExtent[1]])
        .range([innerHeight, 0])
        .nice();
      const sizeScale = d3.scaleSqrt()
        .domain([0, d3.max(points, function(d) { return d.size; }) || 10])
        .range([4, 20]);

      // 坐标轴
      g.append('g')
        .attr('transform', 'translate(0,' + innerHeight + ')')
        .call(d3.axisBottom(xScale).ticks(6));
      g.append('g').call(d3.axisLeft(yScale).ticks(6));

      // 轴标签
      if (options.xLabel) {
        svg.append('text')
          .attr('x', ctx.margin.left + innerWidth / 2)
          .attr('y', ctx.height - 10)
          .attr('text-anchor', 'middle')
          .style('font-size', '12px')
          .style('fill', HLZD_COLORS.text)
          .text(options.xLabel);
      }
      if (options.yLabel) {
        svg.append('text')
          .attr('transform', 'rotate(-90)')
          .attr('x', -(ctx.margin.top + innerHeight / 2))
          .attr('y', 15)
          .attr('text-anchor', 'middle')
          .style('font-size', '12px')
          .style('fill', HLZD_COLORS.text)
          .text(options.yLabel);
      }

      // Tooltip
      const tooltip = HLZDChart.createTooltip();

      // 散点圆
      g.selectAll('circle.point')
        .data(points)
        .join('circle')
        .attr('class', 'point')
        .attr('cx', function(d) { return xScale(d.x); })
        .attr('cy', function(d) { return yScale(d.y); })
        .attr('r', function(d) { return sizeScale(d.size); })
        .attr('fill', function(d) { return colorScale(d.category); })
        .attr('fill-opacity', 0.75)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          d3.select(this).attr('fill-opacity', 1).attr('stroke', HLZD_COLORS.text).attr('stroke-width', 2);
          tooltip.show(
            '<strong>' + (d.label || '点') + '</strong><br>' +
            (options.xLabel || 'X') + ': ' + d.x + '<br>' +
            (options.yLabel || 'Y') + ': ' + d.y + '<br>' +
            '分类: ' + d.category,
            event
          );
        })
        .on('mousemove', function(event) {
          tooltip.el
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 10) + 'px');
        })
        .on('mouseout', function() {
          d3.select(this).attr('fill-opacity', 0.75).attr('stroke', '#fff').attr('stroke-width', 1.5);
          tooltip.hide();
        });

      // 可选：点标签
      if (options.showLabels) {
        g.selectAll('text.point-label')
          .data(points.filter(function(d) { return d.label; }))
          .join('text')
          .attr('class', 'point-label')
          .attr('x', function(d) { return xScale(d.x); })
          .attr('y', function(d) { return yScale(d.y) - sizeScale(d.size) - 4; })
          .attr('text-anchor', 'middle')
          .style('font-size', '10px')
          .style('fill', HLZD_COLORS.text)
          .text(function(d) { return d.label; });
      }

      // 图例（多分类时显示）
      if (categories.length > 1 && categories.length <= 8) {
        const legend = svg.append('g')
          .attr('class', 'scatter-legend')
          .attr('transform', 'translate(' + (ctx.width - 130) + ', ' + (ctx.margin.top + 10) + ')');

        categories.forEach(function(cat, i) {
          const row = legend.append('g')
            .attr('transform', 'translate(0,' + (i * 18) + ')');
          row.append('circle')
            .attr('cx', 6).attr('cy', 6).attr('r', 6)
            .attr('fill', colorScale(cat));
          row.append('text')
            .attr('x', 18).attr('y', 10)
            .style('font-size', '11px')
            .style('fill', HLZD_COLORS.text)
            .text(cat);
        });
      }

      // 品牌来源
      HLZDChart.addSource(svg, options.source, ctx.width);
    }
  };
})();