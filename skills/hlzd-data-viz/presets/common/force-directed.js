// 通用力导向网络图（fork 自 chrisvoncsefalvay + HLZD 品牌色适配）
// 数据格式：{ nodes: [{id, group?, size?}, ...], links: [{source, target, value?}, ...] }
// 用途：客户-产品关系网络、供应商-采购商网络、品类关联图
(function() {
  'use strict';

  /**
   * 力导向网络图
   * @param {string} containerId - 容器 DOM ID
   * @param {object} data - { nodes, links } 结构
   * @param {object} options - { title, source }
   */
  window.HLZD_FORCE = {
    draw: function(containerId, data, options) {
      options = options || {};
      if (!data || !data.nodes || data.nodes.length === 0) return;

      // 深度复制（避免修改原始数据）
      const nodes = data.nodes.map(function(d) {
        return Object.assign({}, d);
      });
      const links = (data.links || []).map(function(d) {
        return Object.assign({}, d);
      });

      const width = 800;
      const height = 600;

      const ctx = HLZDChart.init(containerId, {
        width: width,
        height: height,
        margin: { top: 40, right: 30, bottom: 50, left: 30 },
        title: options.title || '力导向网络图'
      });
      const svg = ctx.svg;
      const g = ctx.g;

      // 提取唯一分组
      const groups = Array.from(new Set(nodes.map(function(d) { return d.group || 'default'; })));

      // 配色
      const colorScale = groups.length <= 5
        ? d3.scaleOrdinal([
            HLZD_COLORS.primary,
            HLZD_COLORS.secondary,
            HLZD_COLORS.accent,
            HLZD_COLORS.warning,
            HLZD_COLORS.danger
          ]).domain(groups)
        : d3.scaleOrdinal(d3.schemeCategory10).domain(groups);

      // 尺寸 scale（基于节点 size 属性）
      const maxNodeSize = d3.max(nodes, function(d) { return d.size || 10; }) || 10;
      const sizeScale = d3.scaleSqrt()
        .domain([0, maxNodeSize])
        .range([6, 24]);

      // Tooltip
      const tooltip = HLZDChart.createTooltip();

      // 力模拟
      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(function(d) { return d.id; }).distance(100))
        .force('charge', d3.forceManyBody().strength(-280))
        .force('center', d3.forceCenter(innerWidthFor(g) / 2, innerHeightFor(g) / 2))
        .force('collision', d3.forceCollide().radius(function(d) { return sizeScale(d.size || 10) + 4; }));

      // 内部辅助函数（获取当前 group 的实际尺寸）
      function innerWidthFor(grp) { return grp.node() ? grp.node().parentElement.getAttribute('viewBox') ? +grp.node().parentElement.getAttribute('viewBox').split(' ')[2] - 70 : width - 60 : width - 60; }
      function innerHeightFor(grp) { return grp.node() ? grp.node().parentElement.getAttribute('viewBox') ? +grp.node().parentElement.getAttribute('viewBox').split(' ')[3] - 90 : height - 90 : height - 90; }

      // 绘制连线（先画，被节点覆盖）
      const link = g.append('g')
        .attr('class', 'links')
        .attr('stroke', HLZD_COLORS.border || '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke-width', function(d) { return Math.sqrt(Number(d.value) || 1); });

      // 绘制节点
      const node = g.append('g')
        .attr('class', 'nodes')
        .selectAll('circle')
        .data(nodes)
        .join('circle')
        .attr('r', function(d) { return sizeScale(d.size || 10); })
        .attr('fill', function(d) { return colorScale(d.group || 'default'); })
        .attr('stroke', '#fff')
        .attr('stroke-width', 2)
        .style('cursor', 'pointer')
        .call(d3.drag()
          .on('start', function(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', function(event, d) {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', function(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }))
        .on('mouseover', function(event, d) {
          d3.select(this).attr('stroke', HLZD_COLORS.text).attr('stroke-width', 3);
          // 高亮相关连线
          link.attr('stroke-opacity', function(l) {
            return (l.source.id === d.id || l.target.id === d.id) ? 0.9 : 0.15;
          }).attr('stroke', function(l) {
            return (l.source.id === d.id || l.target.id === d.id) ? HLZD_COLORS.primary : (HLZD_COLORS.border || '#999');
          });
          tooltip.show(
            '<strong>' + (d.id || d.name || '节点') + '</strong><br>' +
            '分组: ' + (d.group || 'default') + '<br>' +
            (d.size ? '规模: ' + d.size + '<br>' : '') +
            '连接: ' + links.filter(function(l) { return l.source.id === d.id || l.target.id === d.id; }).length,
            event
          );
        })
        .on('mousemove', function(event) {
          tooltip.el
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 10) + 'px');
        })
        .on('mouseout', function() {
          d3.select(this).attr('stroke', '#fff').attr('stroke-width', 2);
          link.attr('stroke-opacity', 0.6).attr('stroke', HLZD_COLORS.border || '#999');
          tooltip.hide();
        });

      // 节点标签
      const label = g.append('g')
        .attr('class', 'labels')
        .selectAll('text')
        .data(nodes.filter(function(d) { return d.id; }))
        .join('text')
        .attr('dx', 12)
        .attr('dy', '0.35em')
        .style('font-size', '11px')
        .style('fill', HLZD_COLORS.text)
        .style('pointer-events', 'none')
        .text(function(d) { return d.id; });

      // Tick 更新位置
      simulation.on('tick', function() {
        link
          .attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });
        node
          .attr('cx', function(d) { return d.x; })
          .attr('cy', function(d) { return d.y; });
        label
          .attr('x', function(d) { return d.x; })
          .attr('y', function(d) { return d.y; });
      });

      // 品牌来源
      HLZDChart.addSource(svg, options.source, ctx.width);
    }
  };
})();