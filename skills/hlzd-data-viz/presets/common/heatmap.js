// 通用热力图
(function() {
  'use strict';

  window.HLZD_HEATMAP = {
    draw: function(containerId, data, options) {
      options = options || {};
      const rows = Array.from(new Set(data.map(d => d.row)));
      const cols = Array.from(new Set(data.map(d => d.column)));
      const ctx = HLZDChart.init(containerId, { width: 800, height: 500, title: options.title || '热力图' });
      const { g, innerWidth, innerHeight } = ctx;

      const xScale = d3.scaleBand().domain(cols).range([0, innerWidth]).padding(0.01);
      const yScale = d3.scaleBand().domain(rows).range([0, innerHeight]).padding(0.01);
      const colourScale = d3.scaleSequential(d3.interpolateYlOrRd)
        .domain([0, d3.max(data, d => d.value) || 1]);

      g.selectAll('rect')
        .data(data)
        .join('rect')
        .attr('x', d => xScale(d.column))
        .attr('y', d => yScale(d.row))
        .attr('width', xScale.bandwidth())
        .attr('height', yScale.bandwidth())
        .attr('fill', d => colourScale(d.value));

      g.append('g').attr('transform', `translate(0,${innerHeight})`).call(d3.axisBottom(xScale));
      g.append('g').call(d3.axisLeft(yScale));
    }
  };
})();
