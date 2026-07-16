// 通用柱状图（fork 自 chrisvoncsefalvay）
(function() {
  'use strict';

  window.HLZD_BAR = {
    draw: function(containerId, data, options) {
      options = options || {};
      const ctx = HLZDChart.init(containerId, { width: 800, height: 400, title: options.title || '柱状图' });
      const { g, innerWidth, innerHeight } = ctx;
      const xScale = d3.scaleBand()
        .domain(data.map(d => d.category))
        .range([0, innerWidth])
        .padding(0.1);
      const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value)])
        .range([innerHeight, 0]);

      g.selectAll('rect')
        .data(data)
        .join('rect')
        .attr('x', d => xScale(d.category))
        .attr('y', d => yScale(d.value))
        .attr('width', xScale.bandwidth())
        .attr('height', d => innerHeight - yScale(d.value))
        .attr('fill', HLZD_COLORS.primary);

      g.append('g').attr('transform', `translate(0,${innerHeight})`).call(d3.axisBottom(xScale));
      g.append('g').call(d3.axisLeft(yScale));
    }
  };
})();
