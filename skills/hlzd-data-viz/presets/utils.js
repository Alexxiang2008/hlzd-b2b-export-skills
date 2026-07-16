// HLZD 共享工具
(function() {
  'use strict';

  // HLZD 图表初始化器
  window.HLZDChart = {
    /**
     * 初始化 SVG 容器（带 HLZD 品牌色 + 响应式）
     * @param {string} containerId - 容器 DOM ID
     * @param {object} options - { width, height, margin, title }
     * @returns {object} { svg, g, width, height, innerWidth, innerHeight }
     */
    init: function(containerId, options) {
      options = options || {};
      const margin = options.margin || { top: 40, right: 30, bottom: 50, left: 60 };
      const width = options.width || 800;
      const height = options.height || 400;
      const innerWidth = width - margin.left - margin.right;
      const innerHeight = height - margin.top - margin.bottom;

      // 清理旧内容
      const container = d3.select('#' + containerId);
      container.selectAll('*').remove();

      // 创建 SVG
      const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('display', 'block')
        .style('background', HLZD_COLORS.background);

      // 标题
      if (options.title) {
        svg.append('text')
          .attr('x', width / 2)
          .attr('y', 25)
          .attr('text-anchor', 'middle')
          .style('font-size', '16px')
          .style('font-weight', 'bold')
          .style('fill', HLZD_COLORS.text)
          .text(options.title);
      }

      // 主 group（带 margin）
      const g = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top + (options.title ? 10 : 0)})`);

      return { svg: svg, g: g, width: width, height: height,
               innerWidth: innerWidth, innerHeight: innerHeight,
               margin: margin };
    },

    /**
     * 创建标准 tooltip（所有图表共用）
     * @returns {object} tooltip 选择器 + show/hide 函数
     */
    createTooltip: function() {
      // 移除已有 tooltip
      d3.selectAll('.hlzd-tooltip').remove();

      const tooltip = d3.select('body').append('div')
        .attr('class', 'hlzd-tooltip')
        .style('position', 'absolute')
        .style('visibility', 'hidden')
        .style('background', 'white')
        .style('border', `1px solid ${HLZD_COLORS.border}`)
        .style('padding', '8px 12px')
        .style('border-radius', '4px')
        .style('font-size', '12px')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
        .style('pointer-events', 'none')
        .style('z-index', '1000');

      return {
        el: tooltip,
        show: function(html, event) {
          tooltip
            .html(html)
            .style('visibility', 'visible')
            .style('top', (event.pageY - 10) + 'px')
            .style('left', (event.pageX + 10) + 'px');
        },
        hide: function() {
          tooltip.style('visibility', 'hidden');
        }
      };
    },

    /**
     * 添加底部来源说明（HLZD 品牌规范）
     */
    addSource: function(svg, text, width) {
      svg.append('text')
        .attr('x', width - 10)
        .attr('y', svg.attr('height') - 5)
        .attr('text-anchor', 'end')
        .style('font-size', '10px')
        .style('fill', HLZD_COLORS.textSecondary)
        .text(text || '数据来源：HLZD-B2B工业品调研');
    }
  };
})();
