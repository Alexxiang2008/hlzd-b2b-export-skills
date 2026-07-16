# D3.js 核心工作流（fork 自 chrisvoncsefalvay/claude-d3js-skill）

> 来源：https://github.com/chrisvoncsefalvay/claude-d3js-skill

## Overview

D3.js（Data-Driven Documents）通过将数据绑定到 DOM 元素并应用数据驱动的转换，创建定制、发布质量的可视化，提供对每个视觉元素的精确控制。技术适用于任何 JavaScript 环境（vanilla JS / React / Vue / Svelte）。

## When to use D3.js

**Use D3.js for**:
- 需要独特视觉编码或布局的自定义可视化
- 复杂的 pan/zoom/brush 交互
- 网络/图可视化（force-directed、tree、hierarchies、chord）
- 自定义投影的地理可视化
- 平滑、协调的过渡动画
- 发布质量图形

**Consider alternatives for**:
- 3D 可视化（用 Three.js）

## Core Workflow

### 1. Setup
```html
<script src="https://d3js.org/d3.v7.min.js"></script>
```

### 2. Standard Structure
```javascript
function drawVisualization(data) {
  if (!data || data.length === 0) return;

  const svg = d3.select('#chart');
  svg.selectAll("*").remove();

  // 1. Define dimensions
  const width = 800;
  const height = 400;
  const margin = { top: 20, right: 30, bottom: 40, left: 50 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // 2. Create main group
  const g = svg.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // 3. Create scales
  const xScale = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.x)])
    .range([0, innerWidth]);

  // 4. Axes
  g.append("g")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(xScale));

  // 5. Bind data
  g.selectAll("circle")
    .data(data)
    .join("circle")
    .attr("cx", d => xScale(d.x))
    .attr("cy", d => yScale(d.y))
    .attr("r", 5)
    .attr("fill", "steelblue");
}
```

### 3. Responsive Sizing
```javascript
function setupResponsiveChart(containerId, data) {
  const container = document.getElementById(containerId);
  const svg = d3.select(`#${containerId}`).append('svg');

  function updateChart() {
    const { width, height } = container.getBoundingClientRect();
    svg.attr('width', width).attr('height', height);
    drawChart(data, svg, width, height);
  }

  updateChart();
  window.addEventListener('resize', updateChart);

  return () => window.removeEventListener('resize', updateChart);
}
```

## Common Patterns

### Bar Chart
```javascript
const xScale = d3.scaleBand()
  .domain(data.map(d => d.category))
  .range([0, innerWidth])
  .padding(0.1);

const yScale = d3.scaleLinear()
  .domain([0, d3.max(data, d => d.value)])
  .range([innerHeight, 0]);

g.selectAll("rect")
  .data(data)
  .join("rect")
  .attr("x", d => xScale(d.category))
  .attr("y", d => yScale(d.value))
  .attr("width", xScale.bandwidth())
  .attr("height", d => innerHeight - yScale(d.value))
  .attr("fill", "steelblue");
```

### Line Chart
```javascript
const line = d3.line()
  .x(d => xScale(d.date))
  .y(d => yScale(d.value))
  .curve(d3.curveMonotoneX);

g.append("path")
  .datum(data)
  .attr("fill", "none")
  .attr("stroke", "steelblue")
  .attr("stroke-width", 2)
  .attr("d", line);
```

### Pie Chart
```javascript
const pie = d3.pie()
  .value(d => d.value)
  .sort(null);

const arc = d3.arc()
  .innerRadius(0)
  .outerRadius(Math.min(width, height) / 2 - 20);

const colourScale = d3.scaleOrdinal(d3.schemeCategory10);

const g = svg.append("g")
  .attr("transform", `translate(${width / 2},${height / 2})`);

g.selectAll("path")
  .data(pie(data))
  .join("path")
  .attr("d", arc)
  .attr("fill", (d, i) => colourScale(i))
  .attr("stroke", "white")
  .attr("stroke-width", 2);
```

### Heatmap
```javascript
const xScale = d3.scaleBand()
  .domain(columns)
  .range([0, innerWidth])
  .padding(0.01);

const yScale = d3.scaleBand()
  .domain(rows)
  .range([0, innerHeight])
  .padding(0.01);

const colourScale = d3.scaleSequential(d3.interpolateYlOrRd)
  .domain([0, d3.max(data, d => d.value)]);

g.selectAll("rect")
  .data(data)
  .join("rect")
  .attr("x", d => xScale(d.column))
  .attr("y", d => yScale(d.row))
  .attr("width", xScale.bandwidth())
  .attr("height", yScale.bandwidth())
  .attr("fill", d => colourScale(d.value));
```

## Interactivity

### Tooltips
```javascript
const tooltip = d3.select("body").append("div")
  .attr("class", "tooltip")
  .style("position", "absolute")
  .style("visibility", "hidden");

circles
  .on("mouseover", function(event, d) {
    tooltip
      .style("visibility", "visible")
      .html(`<b>${d.label}</b><br>Value: ${d.value}`);
  })
  .on("mousemove", function(event) {
    tooltip
      .style("top", (event.pageY - 10) + "px")
      .style("left", (event.pageX + 10) + "px");
  })
  .on("mouseout", function() {
    tooltip.style("visibility", "hidden");
  });
```

### Zoom and Pan
```javascript
const zoom = d3.zoom()
  .scaleExtent([0.5, 10])
  .on("zoom", (event) => {
    g.attr("transform", event.transform);
  });

svg.call(zoom);
```

## Transitions
```javascript
circles
  .transition()
  .duration(750)
  .attr("r", 10);
```

## Scales Reference

### Quantitative
```javascript
d3.scaleLinear()    // 线性
d3.scaleLog()       // 对数
d3.scalePow()       // 幂
d3.scaleTime()      // 时间
```

### Ordinal
```javascript
d3.scaleBand()       // 柱状图
d3.scalePoint()      // 散点
d3.scaleOrdinal()    // 颜色
```

### Sequential
```javascript
d3.scaleSequential(d3.interpolateBlues)
d3.scaleDiverging(d3.interpolateRdBu)
```

## Best Practices

- 数据准备：filter NaN、parse dates、sort
- 性能：>1000 元素用 canvas
- 可访问性：ARIA labels + 键盘导航
- 样式：定义颜色 palette、统一字体

## Resources

- D3.js 官方：https://d3js.org/
- d3-geo：https://github.com/d3/d3-geo
- TopoJSON：https://github.com/topojson/topojson
- Observable Gallery：https://observablehq.com/@d3/gallery