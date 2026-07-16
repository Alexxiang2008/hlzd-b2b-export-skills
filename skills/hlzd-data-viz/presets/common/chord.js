// 通用弦图（fork 自 chrisvoncsefalvay + HLZD 品牌色适配）
// 数据格式：[{ source, target, value }, ...]（流向关系）
// 用途：客户-产品关系、市场间贸易流向、产品-类别关联
(function() {
  'use strict';

  /**
   * 弦图
   * @param {string} containerId - 容器 DOM ID
   * @param {Array<object>} data - 关系数组 [{ source, target, value }]
   * @param {object} options - { title, source }
   */
  window.HLZD_CHORD = {
    draw: function(containerId, data, options) {
      options = options || {};
      if (!data || data.length === 0) return;

      // 收集所有唯一节点
      const nodes = Array.from(new Set(
        data.flatMap(function(d) { return [d.source, d.target]; })
      ));
      if (nodes.length < 2) return;

      // 构造成方矩阵（无向图，对称矩阵）
      const matrix = Array.from({ length: nodes.length }, function() {
        return Array(nodes.length).fill(0);
      });
      data.forEach(function(d) {
        const i = nodes.indexOf(d.source);
        const j = nodes.indexOf(d.target);
        if (i >= 0 && j >= 0 && i !== j) {
          matrix[i][j] += Number(d.value) || 0;
          matrix[j][i] += Number(d.value) || 0; // 对称
        }
      });

      // 检查矩阵非空
      const maxVal = d3.max(matrix.flat());
      if (!maxVal || maxVal === 0) return;

      const width = 600;
      const height = 600;
      const innerRadius = Math.min(width, height) * 0.32;
      const outerRadius = innerRadius + 28;

      const ctx = HLZDChart.init(containerId, {
        width: width,
        height: height,
        margin: { top: 40, right: 30, bottom: 50, left: 30 },
        title: options.title || '弦图（关系网络）'
      });
      const svg = ctx.svg;
      const g = ctx.g;

      // 中心化
      const cx = innerRadius + 30;
      const cy = innerRadius + 10;
      const chordG = g.append('g').attr('transform', 'translate(' + cx + ',' + cy + ')');

      // 配色
      const colorScale = nodes.length <= 5
        ? d3.scaleOrdinal([
            HLZD_COLORS.primary,
            HLZD_COLORS.secondary,
            HLZD_COLORS.accent,
            HLZD_COLORS.warning,
            HLZD_COLORS.danger
          ]).domain(nodes)
        : d3.scaleOrdinal(d3.schemeCategory10).domain(nodes);

      // Chord layout
      const chord = d3.chord()
        .padAngle(0.05)
        .sortSubgroups(d3.descending);
      const chords = chord(matrix);

      const arc = d3.arc()
        .innerRadius(innerRadius)
        .outerRadius(outerRadius);
      const ribbon = d3.ribbon()
        .radius(innerRadius - 2);

      // Tooltip
      const tooltip = HLZDChart.createTooltip();

      // 绘制弦（ribbons）
      const ribbonGroup = chordG.append('g')
        .attr('fill-opacity', 0.72);
      ribbonGroup.selectAll('path.ribbon')
        .data(chords)
        .join('path')
        .attr('class', 'ribbon')
        .attr('d', ribbon)
        .attr('fill', function(d) { return colorScale(nodes[d.source.index]); })
        .attr('stroke', function(d) { return d3.rgb(colorScale(nodes[d.source.index])).darker(0.5); })
        .style('cursor', 'pointer')
        .on('mouseover', function(event, d) {
          d3.select(this).attr('fill-opacity', 1);
          const sName = nodes[d.source.index];
          const tName = nodes[d.target.index];
          const sVal = d.source.value;
          const tVal = d.target.value;
          tooltip.show(
            '<strong>' + sName + ' ↔ ' + tName + '</strong><br>' +
            sName + ' → ' + tName + ': ' + sVal + '<br>' +
            tName + ' → ' + sName + ': ' + tVal,
            event
          );
        })
        .on('mousemove', function(event) {
          tooltip.el
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 10) + 'px');
        })
        .on('mouseout', function() {
          d3.select(this).attr('fill-opacity', 0.72);
          tooltip.hide();
        });

      // 绘制组（外环弧）
      const group = chordG.append('g').selectAll('g.group')
        .data(chords.groups)
        .join('g')
        .attr('class', 'group');
      group.append('path')
        .attr('d', arc)
        .attr('fill', function(d) { return colorScale(nodes[d.index]); })
        .attr('stroke', function(d) { return d3.rgb(colorScale(nodes[d.index])).darker(0.5); });

      // 标签
      group.append('text')
        .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
        .attr('dy', '0.31em')
        .attr('transform', function(d) {
          return 'rotate(' + ((d.angle * 180 / Math.PI) - 90) + ')' +
                 'translate(' + (outerRadius + 8) + ')' +
                 (d.angle > Math.PI ? 'rotate(180)' : '');
        })
        .attr('text-anchor', function(d) { return d.angle > Math.PI ? 'end' : null; })
        .text(function(d, i) { return nodes[d.index]; })
        .style('font-size', '12px')
        .style('fill', HLZD_COLORS.text);

      // 品牌来源
      HLZDChart.addSource(svg, options.source, ctx.width);
    }
  };
})();