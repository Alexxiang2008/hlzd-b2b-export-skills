// 通用折线图
(function() {
  'use strict';

  window.HLZD_LINE = {
    draw: function(containerId, data, options) {
      options = options || {};
      const ctx = HLZDChart.init(containerId, { width: 800, height: 400, title: options.title || '折线图' });
      const { g, innerWidth, innerHeight } = ctx;
      const xScale = d3.scaleLinear().domain([0, data.length - 1]).range([0, innerWidth]);
      const yScale = d3.scaleLinear()
        .domain([0, d3.max(data, d => d.value) * 1.1])
        .range([innerHeight, 0]);

      const line = d3.line()
        .x((d, i) => xScale(i))
        .y(d => yScale(d.value))
        .curve(d3.curveMonotoneX);

      g.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', HLZD_COLORS.primary)
        .attr('stroke-width', 2)
        .attr('d', line);

      g.selectAll('.dot')
        .data(data)
        .join('circle')
        .attr('class', 'dot')
        .attr('cx', (d, i) => xScale(i))
        .attr('cy', d => yScale(d.value))
        .attr('r', 4)
        .attr('fill', HLZD_COLORS.primary);

      g.append('g').attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(xScale).ticks(data.length).tickFormat((d, i) => data[i]?.date || ''));
      g.append('g').call(d3.axisLeft(yScale));
    }
  };
})();
