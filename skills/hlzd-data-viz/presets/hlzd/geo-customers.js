// HLZD 客户地理分布 ⭐
// 数据：[{country, count, lat, lng}, ...]
(function() {
  'use strict';

  window.HLZD_GEO = {
    /**
     * 绘制客户地理分布（世界地图 + 气泡）
     * @param {string} containerId
     * @param {object} data - { points: [{country, count, lat, lng}], title }
     */
    draw: function(containerId, data) {
      if (!data || !data.points || data.points.length === 0) {
        console.error('[HLZD Geo] 数据为空');
        return;
      }

      const width = 800;
      const height = 450;

      const ctx = HLZDChart.init(containerId, {
        width, height,
        margin: { top: 30, right: 30, bottom: 40, left: 30 },
        title: data.title || '客户地理分布'
      });

      const { svg, g } = ctx;
      const tooltip = HLZDChart.createTooltip();

      // 检测 world-110m.json 是否可用
      const worldDataUrl = (typeof HLZD_CONFIG !== 'undefined' && HLZD_CONFIG.WORLD_GEOJSON_PATH)
        || 'assets/world-110m.json';

      // 尝试加载世界地图
      d3.json(worldDataUrl).then(function(world) {
        if (!world) throw new Error('世界地图数据为空');

        // 简化版：直接用 d3.geoMercator + topojson
        const countries = topojson.feature(world, world.objects.countries).features;

        // 投影
        const projection = d3.geoMercator()
          .fitSize([ctx.innerWidth, ctx.innerHeight], { type: 'Sphere' });
        const path = d3.geoPath().projection(projection);

        // 绘制国家
        g.selectAll('.country')
          .data(countries)
          .join('path')
          .attr('class', 'country')
          .attr('d', path)
          .attr('fill', HLZD_COLORS.background)
          .attr('stroke', HLZD_COLORS.border)
          .attr('stroke-width', 0.5);

        // 客户气泡
        const maxCount = d3.max(data.points, d => d.count) || 1;
        const radiusScale = d3.scaleSqrt()
          .domain([0, maxCount])
          .range([3, 20]);

        g.selectAll('.customer-bubble')
          .data(data.points)
          .join('circle')
          .attr('class', 'customer-bubble')
          .attr('cx', d => projection([d.lng, d.lat])[0])
          .attr('cy', d => projection([d.lng, d.lat])[1])
          .attr('r', d => radiusScale(d.count))
          .attr('fill', HLZD_COLORS.primary)
          .attr('fill-opacity', 0.7)
          .attr('stroke', 'white')
          .attr('stroke-width', 1.5)
          .style('cursor', 'pointer')
          .on('mouseover', function(event, d) {
            d3.select(this).attr('fill-opacity', 1);
            tooltip.show(`
              <b>${d.country}</b><br>
              客户数: <b style="color:${HLZD_COLORS.primary}">${d.count}</b>
            `, event);
          })
          .on('mouseout', function() {
            d3.select(this).attr('fill-opacity', 0.7);
            tooltip.hide();
          });

        // 客户数标签
        g.selectAll('.customer-label')
          .data(data.points.filter(d => d.count > maxCount * 0.3))
          .join('text')
          .attr('class', 'customer-label')
          .attr('x', d => projection([d.lng, d.lat])[0])
          .attr('y', d => projection([d.lng, d.lat])[1] - radiusScale(d.count) - 4)
          .attr('text-anchor', 'middle')
          .style('font-size', '10px')
          .style('font-weight', 'bold')
          .style('fill', HLZD_COLORS.text)
          .text(d => `${d.country} ${d.count}`);

        HLZDChart.addSource(svg, '数据来源：HLZD-B2B工业品调研', width);
      }).catch(function(err) {
        // 地图加载失败 → 降级为简单散点图
        console.warn('[HLZD Geo] 世界地图加载失败，使用降级散点图:', err.message);
        this._renderFallbackScatter(g, data, ctx, width, tooltip);
      }.bind(this));
    },

    _renderFallbackScatter: function(g, data, ctx, width, tooltip) {
      const points = data.points;
      const margin = 20;
      const xs = points.map(p => p.lng);
      const ys = points.map(p => p.lat);
      const xScale = d3.scaleLinear()
        .domain([Math.min(...xs) - 5, Math.max(...xs) + 5])
        .range([margin, ctx.innerWidth - margin]);
      const yScale = d3.scaleLinear()
        .domain([Math.min(...ys) - 5, Math.max(...ys) + 5])
        .range([ctx.innerHeight - margin, margin]);
      const r = d3.scaleSqrt().domain([0, d3.max(points, d => d.count)]).range([5, 30]);

      g.selectAll('.pt')
        .data(points)
        .join('circle')
        .attr('class', 'pt')
        .attr('cx', d => xScale(d.lng))
        .attr('cy', d => yScale(d.lat))
        .attr('r', d => r(d.count))
        .attr('fill', HLZD_COLORS.primary)
        .attr('fill-opacity', 0.7)
        .on('mouseover', function(event, d) {
          d3.select(this).attr('fill-opacity', 1);
          tooltip.show(`<b>${d.country}</b><br>客户数: ${d.count}<br>(${d.lat}, ${d.lng})`, event);
        })
        .on('mouseout', function() {
          d3.select(this).attr('fill-opacity', 0.7);
          tooltip.hide();
        });

      // 注释：地图数据缺失
      g.append('text')
        .attr('x', ctx.innerWidth / 2)
        .attr('y', 20)
        .attr('text-anchor', 'middle')
        .style('font-size', '11px')
        .style('fill', HLZD_COLORS.textSecondary)
        .text('⚠️ 世界地图未加载，使用经纬度散点（请将 world-110m.json 放到 assets/）');
    }
  };
})();
