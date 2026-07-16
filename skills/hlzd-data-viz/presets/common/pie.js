// 通用饼图
(function() {
  'use strict';

  window.HLZD_PIE = {
    draw: function(containerId, data, options) {
      options = options || {};
      const ctx = HLZDChart.init(containerId, { width: 600, height: 400, title: options.title || '饼图' });
      const { svg, innerWidth, innerHeight } = ctx;
      const radius = Math.min(innerWidth, innerHeight) / 2 - 20;
      const pie = d3.pie().value(d => d.value).sort(null);
      const arc = d3.arc().innerRadius(0).outerRadius(radius);
      const color = d3.scaleOrdinal(HLZD_COLORS.categorical);

      const g = svg.append('g')
        .attr('transform', `translate(${innerWidth / 2 + 30}, ${innerHeight / 2 + 30})`);

      g.selectAll('path')
        .data(pie(data))
        .join('path')
        .attr('d', arc)
        .attr('fill', (d, i) => color(i))
        .attr('stroke', 'white')
        .attr('stroke-width', 2);

      // 图例
      const legend = svg.append('g').attr('transform', `translate(${innerWidth - 100}, 60)`);
      data.forEach((d, i) => {
        const row = legend.append('g').attr('transform', `translate(0, ${i * 20})`);
        row.append('rect').attr('width', 12).attr('height', 12).attr('fill', color(i));
        row.append('text').attr('x', 18).attr('y', 6).attr('dy', '0.35em')
          .style('font-size', '11px').text(`${d.category}: ${d.value}`);
      });
    }
  };
})();
