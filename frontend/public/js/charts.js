/** LexChain Sovereign - Pure Canvas Charts */
class Chart {
  constructor(canvas, options = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.options = {
      colors: {
        primary: '#3b82f6',
        secondary: '#10b981',
        tertiary: '#f59e0b',
        quaternary: '#ef4444',
        background: '#ffffff',
        text: '#475467',
        grid: '#e4e7ec'
      },
      animation: true,
      responsive: true,
      ...options
    };
    this.data = [];
    this.animationProgress = 0;
    this.init();
  }

  init() {
    this.resize();
    if (this.options.responsive) {
      window.addEventListener('resize', () => this.resize());
    }
  }

  resize() {
    const container = this.canvas.parentElement;
    this.canvas.width = container.clientWidth;
    this.canvas.height = this.options.height || 300;
    this.draw();
  }

  setData(data) {
    this.data = data;
    if (this.options.animation) {
      this.animate();
    } else {
      this.draw();
    }
  }

  animate() {
    const duration = 1000;
    const start = performance.now();
    const animateFrame = (timestamp) => {
      this.animationProgress = Math.min((timestamp - start) / duration, 1);
      this.animationProgress = this.easeOut(this.animationProgress);
      this.draw();
      if (this.animationProgress < 1) {
        requestAnimationFrame(animateFrame);
      }
    };
    requestAnimationFrame(animateFrame);
  }

  easeOut(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  draw() {}
}

class BarChart extends Chart {
  constructor(canvas, options = {}) {
    super(canvas, { height: 300, ...options });
    this.barWidth = 40;
    this.barGap = 20;
  }

  draw() {
    const ctx = this.ctx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    if (!this.data.length) {
      this.drawEmptyState('No data available');
      return;
    }

    const maxValue = Math.max(...this.data.map(d => d.value));
    const barCount = this.data.length;
    const totalBarWidth = barCount * (this.barWidth + this.barGap) - this.barGap;
    const startX = padding.left + (chartWidth - totalBarWidth) / 2;

    this.data.forEach((item, index) => {
      const x = startX + index * (this.barWidth + this.barGap);
      const barHeight = (item.value / maxValue) * chartHeight * this.animationProgress;
      const y = padding.top + chartHeight - barHeight;

      ctx.fillStyle = item.color || this.options.colors.primary;
      ctx.beginPath();
      ctx.roundRect(x, y, this.barWidth, barHeight, [4, 4, 0, 0]);
      ctx.fill();

      ctx.fillStyle = this.options.colors.text;
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(item.label, x + this.barWidth / 2, height - padding.bottom + 20);

      if (item.value > 0) {
        ctx.fillText(item.value.toLocaleString(), x + this.barWidth / 2, y - 8);
      }
    });

    this.drawGrid(padding, chartHeight);
  }

  drawGrid(padding, chartHeight) {
    const ctx = this.ctx;
    ctx.strokeStyle = this.options.colors.grid;
    ctx.lineWidth = 1;

    for (let i = 0; i <= 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(this.canvas.width - padding.right, y);
      ctx.stroke();
    }
  }

  drawEmptyState(message) {
    const ctx = this.ctx;
    ctx.fillStyle = this.options.colors.text;
    ctx.font = '14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(message, this.canvas.width / 2, this.canvas.height / 2);
  }
}

class LineChart extends Chart {
  constructor(canvas, options = {}) {
    super(canvas, { height: 300, ...options });
    this.points = [];
  }

  draw() {
    const ctx = this.ctx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, width, height);

    if (!this.data.length) {
      this.drawEmptyState('No data available');
      return;
    }

    const maxValue = Math.max(...this.data.map(d => d.value));
    const minValue = Math.min(...this.data.map(d => d.value));
    const valueRange = maxValue - minValue || 1;

    this.points = this.data.map((item, index) => ({
      x: padding.left + (index / (this.data.length - 1)) * chartWidth,
      y: padding.top + chartHeight - ((item.value - minValue) / valueRange) * chartHeight * this.animationProgress,
      value: item.value,
      label: item.label
    }));

    ctx.strokeStyle = this.options.colors.primary;
    ctx.lineWidth = 2;
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    ctx.beginPath();

    this.points.forEach((point, index) => {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        const prev = this.points[index - 1];
        const cpX = (prev.x + point.x) / 2;
        ctx.bezierCurveTo(cpX, prev.y, cpX, point.y, point.x, point.y);
      }
    });
    ctx.stroke();

    ctx.fillStyle = this.options.colors.primary;
    this.points.forEach(point => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    this.drawAxes(padding, chartHeight, minValue, maxValue);
  }

  drawAxes(padding, chartHeight, minValue, maxValue) {
    const ctx = this.ctx;
    ctx.fillStyle = this.options.colors.text;
    ctx.font = '12px Inter, sans-serif';

    ctx.textAlign = 'right';
    ctx.fillText(maxValue.toLocaleString(), padding.left - 10, padding.top + 10);
    ctx.fillText(minValue.toLocaleString(), padding.left - 10, padding.top + chartHeight);

    this.data.forEach((item, index) => {
      if (this.points[index]) {
        ctx.textAlign = 'center';
        ctx.fillText(item.label || '', this.points[index].x, this.canvas.height - padding.bottom + 20);
      }
    });
  }

  drawEmptyState(message) {
    const ctx = this.ctx;
    ctx.fillStyle = this.options.colors.text;
    ctx.font = '14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(message, this.canvas.width / 2, this.canvas.height / 2);
  }
}

class DonutChart extends Chart {
  constructor(canvas, options = {}) {
    super(canvas, { height: 300, ...options });
    this.defaultColors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
  }

  draw() {
    const ctx = this.ctx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;
    const innerRadius = radius * 0.6;

    ctx.clearRect(0, 0, width, height);

    if (!this.data.length) {
      this.drawEmptyState('No data available');
      return;
    }

    const total = this.data.reduce((sum, item) => sum + item.value, 0);
    let startAngle = -Math.PI / 2;

    this.data.forEach((item, index) => {
      const sliceAngle = (item.value / total) * 2 * Math.PI * this.animationProgress;
      const endAngle = startAngle + sliceAngle;

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
      ctx.closePath();

      ctx.fillStyle = item.color || this.defaultColors[index % this.defaultColors.length];
      ctx.fill();

      startAngle = endAngle;
    });

    ctx.fillStyle = this.options.colors.background;
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius - 2, 0, Math.PI * 2);
    ctx.fill();

    const totalValue = total.toLocaleString();
    ctx.fillStyle = this.options.colors.text;
    ctx.font = 'bold 24px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(totalValue, centerX, centerY - 10);
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText('Total', centerX, centerY + 15);
  }

  drawEmptyState(message) {
    const ctx = this.ctx;
    ctx.fillStyle = this.options.colors.text;
    ctx.font = '14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(message, this.canvas.width / 2, this.canvas.height / 2);
  }
}

class PieChart extends DonutChart {
  draw() {
    const ctx = this.ctx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 20;

    ctx.clearRect(0, 0, width, height);

    if (!this.data.length) {
      this.drawEmptyState('No data available');
      return;
    }

    const total = this.data.reduce((sum, item) => sum + item.value, 0);
    let startAngle = -Math.PI / 2;

    this.data.forEach((item, index) => {
      const sliceAngle = (item.value / total) * 2 * Math.PI * this.animationProgress;
      const endAngle = startAngle + sliceAngle;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();

      ctx.fillStyle = item.color || this.defaultColors[index % this.defaultColors.length];
      ctx.fill();

      const midAngle = startAngle + sliceAngle / 2;
      const labelRadius = radius * 1.2;
      const labelX = centerX + Math.cos(midAngle) * labelRadius;
      const labelY = centerY + Math.sin(midAngle) * labelRadius;

      if (sliceAngle > 0.3) {
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const percentage = Math.round((item.value / total) * 100);
        ctx.fillText(`${percentage}%`, labelX, labelY);
      }

      startAngle = endAngle;
    });
  }
}

window.Chart = Chart;
window.BarChart = BarChart;
window.LineChart = LineChart;
window.DonutChart = DonutChart;
window.PieChart = PieChart;