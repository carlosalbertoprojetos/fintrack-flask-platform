(function (window, document) {
  'use strict';

  if (typeof window.Chart !== 'undefined') {
    return;
  }

  var DEFAULT_COLORS = [
    '#4e73df',
    '#1cc88a',
    '#36b9cc',
    '#f6c23e',
    '#e74a3b',
    '#858796',
    '#5a5c69',
    '#fd7e14',
    '#20c997',
    '#6610f2'
  ];

  function themeColor(varName, fallback) {
    try {
      var value = getComputedStyle(document.documentElement)
        .getPropertyValue(varName)
        .trim();
      return value || fallback;
    } catch (e) {
      return fallback;
    }
  }

  function isNumber(value) {
    return typeof value === 'number' && !isNaN(value) && isFinite(value);
  }

  function toNumber(value) {
    var parsed = Number(value);
    return isNumber(parsed) ? parsed : 0;
  }

  function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function getCanvas(target) {
    if (!target) return null;
    if (target.canvas) return target.canvas;
    if (target instanceof window.HTMLCanvasElement) return target;
    return null;
  }

  function getContext(target) {
    var canvas = getCanvas(target);
    return canvas ? canvas.getContext('2d') : target;
  }

  function getLegendOptions(config) {
    return (((config || {}).options || {}).plugins || {}).legend || {};
  }

  function getCutoutValue(config) {
    return ((config || {}).options || {}).cutout;
  }

  function getTickCallback(config) {
    var ticks = (((config || {}).options || {}).scales || {}).y;
    ticks = ticks && ticks.ticks;
    return ticks && typeof ticks.callback === 'function' ? ticks.callback : null;
  }

  function getDevicePixelRatio() {
    return Math.max(window.devicePixelRatio || 1, 1);
  }

  function resolveCssSize(canvas) {
    var computed = window.getComputedStyle(canvas);
    var parent = canvas.parentElement;
    var width = canvas.clientWidth || parseFloat(computed.width) || (parent ? parent.clientWidth : 0) || 400;
    var height = canvas.clientHeight || parseFloat(computed.height) || (parent ? parent.clientHeight : 0) || parseFloat(canvas.getAttribute('height')) || 320;

    if (height < 180) {
      height = 320;
    }

    return {
      width: Math.round(width),
      height: Math.round(height)
    };
  }

  function prepareCanvas(chart) {
    var size = resolveCssSize(chart.canvas);
    var dpr = getDevicePixelRatio();

    chart.width = size.width;
    chart.height = size.height;

    chart.canvas.width = size.width * dpr;
    chart.canvas.height = size.height * dpr;
    chart.canvas.style.width = size.width + 'px';
    chart.canvas.style.height = size.height + 'px';

    chart.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    chart.ctx.clearRect(0, 0, size.width, size.height);
  }

  function getDatasetColor(dataset, index, type) {
    if (type === 'doughnut') {
      var bg = dataset.backgroundColor;
      if (Array.isArray(bg) && bg.length) {
        return bg;
      }
    }

    return dataset.borderColor || dataset.backgroundColor || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
  }

  function formatTick(value, callback) {
    if (callback) {
      try {
        return String(callback(value));
      } catch (error) {
        return String(value);
      }
    }
    return String(value);
  }

  function drawLegend(ctx, chart, items) {
    var legendOptions = getLegendOptions(chart.config);
    if (legendOptions.display === false || !items.length) {
      return { top: 0, bottom: 0 };
    }

    var position = legendOptions.position === 'bottom' ? 'bottom' : 'top';
    var y = position === 'bottom' ? chart.height - 18 : 18;
    var x = 16;

    ctx.save();
    ctx.font = '12px sans-serif';
    ctx.textBaseline = 'middle';

    items.forEach(function (item, index) {
      var label = item.label || ('Serie ' + (index + 1));
      var color = item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
      var textWidth = ctx.measureText(label).width;

      if (x + textWidth + 36 > chart.width - 16) {
        x = 16;
        y += position === 'bottom' ? -18 : 18;
      }

      ctx.fillStyle = color;
      ctx.fillRect(x, y - 5, 14, 10);
      ctx.fillStyle = themeColor('--app-chart-text', '#5a5c69');
      ctx.fillText(label, x + 20, y);
      x += textWidth + 36;
    });

    ctx.restore();

    return position === 'bottom' ? { top: 0, bottom: 34 } : { top: 34, bottom: 0 };
  }

  function getChartArea(chart, legendPadding) {
    return {
      left: 56,
      top: 20 + (legendPadding.top || 0),
      right: chart.width - 20,
      bottom: chart.height - 42 - (legendPadding.bottom || 0)
    };
  }

  function computeScale(values, beginAtZero) {
    if (!values.length) {
      return { min: 0, max: 1, range: 1 };
    }

    var min = Math.min.apply(null, values);
    var max = Math.max.apply(null, values);

    if (beginAtZero || min > 0) {
      min = 0;
    }

    if (min === max) {
      if (max === 0) {
        max = 1;
      } else {
        min = Math.min(0, min * 0.9);
        max = max * 1.1;
      }
    }

    return {
      min: min,
      max: max,
      range: max - min
    };
  }

  function valueToY(value, scale, area) {
    var ratio = (value - scale.min) / scale.range;
    return area.bottom - (ratio * (area.bottom - area.top));
  }

  function drawAxes(ctx, area, labels, scale, tickCallback) {
    var tickCount = 5;
    var xStep = labels.length > 1 ? (area.right - area.left) / (labels.length - 1) : 0;

    ctx.save();
    ctx.strokeStyle = themeColor('--app-chart-grid', '#e3e6f0');
    ctx.fillStyle = themeColor('--app-chart-text', '#858796');
    ctx.lineWidth = 1;
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (var i = 0; i <= tickCount; i += 1) {
      var value = scale.min + (scale.range * (i / tickCount));
      var y = area.bottom - ((area.bottom - area.top) * (i / tickCount));
      ctx.beginPath();
      ctx.moveTo(area.left, y);
      ctx.lineTo(area.right, y);
      ctx.stroke();
      ctx.fillText(formatTick(value, tickCallback), area.left - 8, y);
    }

    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    labels.forEach(function (label, index) {
      var x = labels.length === 1 ? (area.left + area.right) / 2 : area.left + (xStep * index);
      ctx.fillText(String(label), x, area.bottom + 10);
    });

    ctx.restore();
  }

  function fillLineArea(ctx, points, baselineY, color) {
    if (points.length < 2) return;

    ctx.save();
    ctx.beginPath();
    ctx.moveTo(points[0].x, baselineY);
    points.forEach(function (point) {
      ctx.lineTo(point.x, point.y);
    });
    ctx.lineTo(points[points.length - 1].x, baselineY);
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.restore();
  }

  function drawLineSeries(ctx, points, dataset) {
    if (!points.length) return;

    ctx.save();
    ctx.beginPath();
    ctx.lineWidth = 2;
    ctx.strokeStyle = dataset.borderColor || '#4e73df';
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';

    points.forEach(function (point, index) {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    });

    ctx.stroke();

    points.forEach(function (point) {
      ctx.beginPath();
      ctx.fillStyle = dataset.borderColor || '#4e73df';
      ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
      ctx.fill();
    });

    ctx.restore();
  }

  function drawLineChart(chart) {
    var data = chart.config.data || {};
    var labels = data.labels || [];
    var datasets = data.datasets || [];
    if (!labels.length || !datasets.length) return;

    var ctx = chart.ctx;
    var legendPadding = drawLegend(ctx, chart, datasets.map(function (dataset, index) {
      return { label: dataset.label, color: getDatasetColor(dataset, index, 'line') };
    }));
    var area = getChartArea(chart, legendPadding);
    var values = [];
    var baseline = 0;
    var tickCallback = getTickCallback(chart.config);

    datasets.forEach(function (dataset) {
      (dataset.data || []).forEach(function (value) {
        values.push(toNumber(value));
      });
    });

    var scale = computeScale(values, ((((chart.config || {}).options || {}).scales || {}).y || {}).beginAtZero !== false);
    baseline = valueToY(0, scale, area);

    drawAxes(ctx, area, labels, scale, tickCallback);

    datasets.forEach(function (dataset, datasetIndex) {
      var series = dataset.data || [];
      var xStep = labels.length > 1 ? (area.right - area.left) / (labels.length - 1) : 0;
      var points = series.map(function (value, index) {
        return {
          x: labels.length === 1 ? (area.left + area.right) / 2 : area.left + (xStep * index),
          y: valueToY(toNumber(value), scale, area)
        };
      });

      if (dataset.fill) {
        fillLineArea(ctx, points, baseline, dataset.backgroundColor || 'rgba(78, 115, 223, 0.12)');
      }
      drawLineSeries(ctx, points, {
        borderColor: getDatasetColor(dataset, datasetIndex, 'line')
      });
    });
  }

  function drawBarChart(chart) {
    var data = chart.config.data || {};
    var labels = data.labels || [];
    var datasets = data.datasets || [];
    if (!labels.length || !datasets.length) return;

    var ctx = chart.ctx;
    var legendPadding = drawLegend(ctx, chart, datasets.map(function (dataset, index) {
      return { label: dataset.label, color: getDatasetColor(dataset, index, 'bar') };
    }));
    var area = getChartArea(chart, legendPadding);
    var values = [];
    var tickCallback = getTickCallback(chart.config);

    datasets.forEach(function (dataset) {
      (dataset.data || []).forEach(function (value) {
        values.push(toNumber(value));
      });
    });

    var scale = computeScale(values, ((((chart.config || {}).options || {}).scales || {}).y || {}).beginAtZero !== false);
    drawAxes(ctx, area, labels, scale, tickCallback);

    var groupWidth = (area.right - area.left) / Math.max(labels.length, 1);
    var barGroupWidth = groupWidth * 0.72;
    var barWidth = barGroupWidth / Math.max(datasets.length, 1);
    var zeroY = valueToY(0, scale, area);

    datasets.forEach(function (dataset, datasetIndex) {
      ctx.save();
      ctx.fillStyle = dataset.backgroundColor || getDatasetColor(dataset, datasetIndex, 'bar');

      (dataset.data || []).forEach(function (value, index) {
        var x = area.left + (groupWidth * index) + ((groupWidth - barGroupWidth) / 2) + (barWidth * datasetIndex);
        var y = valueToY(toNumber(value), scale, area);
        var top = Math.min(y, zeroY);
        var height = Math.abs(zeroY - y);
        ctx.fillRect(x, top, Math.max(barWidth - 6, 8), Math.max(height, 1));
      });

      ctx.restore();
    });
  }

  function parseCutout(cutout) {
    if (typeof cutout === 'string' && cutout.indexOf('%') > -1) {
      return clamp(parseFloat(cutout) / 100, 0, 0.9);
    }
    if (typeof cutout === 'number') {
      return clamp(cutout / 100, 0, 0.9);
    }
    return 0.6;
  }

  function drawDoughnutChart(chart) {
    var data = chart.config.data || {};
    var labels = data.labels || [];
    var dataset = (data.datasets || [])[0];
    if (!labels.length || !dataset) return;

    var values = (dataset.data || []).map(toNumber);
    var total = values.reduce(function (acc, value) {
      return acc + Math.max(value, 0);
    }, 0);
    if (!total) return;

    var ctx = chart.ctx;
    var legendOptions = getLegendOptions(chart.config);
    var colors = Array.isArray(dataset.backgroundColor) && dataset.backgroundColor.length ? dataset.backgroundColor : DEFAULT_COLORS;
    var legendItems = labels.map(function (label, index) {
      return {
        label: label,
        color: colors[index % colors.length]
      };
    });
    var legendPadding = legendOptions.display === false ? { top: 0, bottom: 0 } : drawLegend(ctx, chart, legendItems);
    var availableTop = 20 + (legendPadding.top || 0);
    var availableBottom = chart.height - 20 - (legendPadding.bottom || 0);
    var centerX = chart.width / 2;
    var centerY = (availableTop + availableBottom) / 2;
    var radius = Math.max(Math.min(chart.width - 40, availableBottom - availableTop) / 2, 40);
    var innerRadius = radius * parseCutout(getCutoutValue(chart.config));
    var startAngle = -Math.PI / 2;

    values.forEach(function (value, index) {
      var slice = (Math.max(value, 0) / total) * Math.PI * 2;
      var endAngle = startAngle + slice;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();
      ctx.fillStyle = colors[index % colors.length];
      ctx.fill();
      ctx.restore();

      startAngle = endAngle;
    });

    ctx.save();
    ctx.globalCompositeOperation = 'destination-out';
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }

  function render(chart) {
    prepareCanvas(chart);

    if (!chart.config || !chart.ctx) {
      return;
    }

    var type = chart.config.type;
    if (type === 'line') {
      drawLineChart(chart);
      return;
    }

    if (type === 'bar') {
      drawBarChart(chart);
      return;
    }

    if (type === 'doughnut') {
      drawDoughnutChart(chart);
    }
  }

  function SimpleChart(target, config) {
    this.canvas = getCanvas(target);
    this.ctx = getContext(target);
    this.config = config || {};
    this._resizeHandler = null;

    if (!this.canvas || !this.ctx) {
      throw new Error('Canvas de grafico nao encontrado.');
    }

    if (this.canvas.__simpleChartInstance) {
      this.canvas.__simpleChartInstance.destroy();
    }
    this.canvas.__simpleChartInstance = this;

    this._bindResize();
    this.update();
  }

  SimpleChart.prototype._bindResize = function () {
    var self = this;
    this._resizeHandler = function () {
      window.clearTimeout(self._resizeTimer);
      self._resizeTimer = window.setTimeout(function () {
        self.update();
      }, 80);
    };
    window.addEventListener('resize', this._resizeHandler);
  };

  SimpleChart.prototype.update = function () {
    render(this);
    return this;
  };

  SimpleChart.prototype.destroy = function () {
    if (this._resizeHandler) {
      window.removeEventListener('resize', this._resizeHandler);
    }
    if (this._resizeTimer) {
      window.clearTimeout(this._resizeTimer);
    }
    if (this.ctx) {
      this.ctx.clearRect(0, 0, this.width || 0, this.height || 0);
    }
    if (this.canvas && this.canvas.__simpleChartInstance === this) {
      delete this.canvas.__simpleChartInstance;
    }
  };

  window.Chart = SimpleChart;
})(window, document);
