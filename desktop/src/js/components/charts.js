/**
 * ResumeAI Desktop - Charts Component
 * Simple chart rendering without external dependencies
 */

class ChartsManager {
    constructor() {
        this.charts = new Map();
        this.colors = [
            '#2563eb', // primary
            '#10b981', // success
            '#f59e0b', // warning
            '#ef4444', // danger
            '#06b6d4', // info
            '#8b5cf6', // purple
            '#ec4899', // pink
            '#64748b', // slate
        ];
    }

    /**
     * Create a bar chart
     */
    createBarChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const { labels, values } = data;
        const {
            title = '',
            xLabel = '',
            yLabel = '',
            showValues = true,
            color = this.colors[0],
        } = options;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Calculate dimensions
        const padding = 60;
        const chartWidth = canvas.width - padding * 2;
        const chartHeight = canvas.height - padding * 2;
        const maxValue = Math.max(...values, 1);
        const barWidth = (chartWidth / labels.length) * 0.7;
        const barGap = (chartWidth / labels.length) * 0.3;

        // Draw title
        if (title) {
            ctx.fillStyle = '#0f172a';
            ctx.font = 'bold 14px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(title, canvas.width / 2, 25);
        }

        // Draw axes
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw bars and labels
        labels.forEach((label, index) => {
            const x = padding + index * (barWidth + barGap) + barGap / 2;
            const barHeight = (values[index] / maxValue) * chartHeight;
            const y = canvas.height - padding - barHeight;

            // Draw bar
            ctx.fillStyle = Array.isArray(color) ? color[index % color.length] : color;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw value
            if (showValues) {
                ctx.fillStyle = '#475569';
                ctx.font = '12px -apple-system, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(values[index].toString(), x + barWidth / 2, y - 5);
            }

            // Draw label
            ctx.fillStyle = '#64748b';
            ctx.font = '11px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.save();
            ctx.translate(x + barWidth / 2, canvas.height - padding + 15);
            ctx.rotate(-Math.PI / 6);
            ctx.fillText(label, 0, 0);
            ctx.restore();
        });

        // Draw Y-axis labels
        ctx.fillStyle = '#64748b';
        ctx.font = '11px -apple-system, sans-serif';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {
            const value = Math.round((maxValue / 4) * i);
            const y = canvas.height - padding - (chartHeight / 4) * i;
            ctx.fillText(value.toString(), padding - 5, y + 4);
        }

        // Store chart reference
        const chart = { type: 'bar', canvas, ctx, data, options };
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    /**
     * Create a pie/doughnut chart
     */
    createPieChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const { labels, values } = data;
        const {
            title = '',
            type = 'doughnut',
            showLegend = true,
            showLabels = true,
        } = options;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Calculate dimensions
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2 + 10;
        const radius = Math.min(centerX, centerY) - 60;
        const innerRadius = type === 'doughnut' ? radius * 0.5 : 0;
        const total = values.reduce((sum, val) => sum + val, 0);

        // Draw title
        if (title) {
            ctx.fillStyle = '#0f172a';
            ctx.font = 'bold 14px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(title, canvas.width / 2, 25);
        }

        // Draw segments
        let startAngle = -Math.PI / 2;
        const segments = [];

        values.forEach((value, index) => {
            const sliceAngle = (value / total) * 2 * Math.PI;
            const endAngle = startAngle + sliceAngle;

            // Draw segment
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = this.colors[index % this.colors.length];
            ctx.fill();

            // Calculate label position
            const midAngle = startAngle + sliceAngle / 2;
            const labelRadius = (radius + innerRadius) / 2;
            const labelX = centerX + Math.cos(midAngle) * labelRadius;
            const labelY = centerY + Math.sin(midAngle) * labelRadius;

            segments.push({
                label: labels[index],
                value: value,
                percentage: ((value / total) * 100).toFixed(1),
                color: this.colors[index % this.colors.length],
                x: labelX,
                y: labelY,
            });

            startAngle = endAngle;
        });

        // Draw labels
        if (showLabels) {
            segments.forEach((segment) => {
                if (segment.percentage > 5) {
                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 12px -apple-system, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(`${segment.percentage}%`, segment.x, segment.y);
                }
            });
        }

        // Draw legend
        if (showLegend) {
            const legendX = canvas.width - 150;
            const legendY = 50;
            const legendItemHeight = 25;

            segments.forEach((segment, index) => {
                const y = legendY + index * legendItemHeight;

                // Color box
                ctx.fillStyle = segment.color;
                ctx.fillRect(legendX, y, 15, 15);

                // Label
                ctx.fillStyle = '#475569';
                ctx.font = '11px -apple-system, sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(`${segment.label}: ${segment.value}`, legendX + 20, y + 12);
            });
        }

        // Store chart reference
        const chart = { type: 'pie', canvas, ctx, data, options, segments };
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    /**
     * Create a line chart
     */
    createLineChart(canvasId, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        const { labels, values } = data;
        const {
            title = '',
            xLabel = '',
            yLabel = '',
            showPoints = true,
            color = this.colors[0],
            fill = false,
        } = options;

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Calculate dimensions
        const padding = 60;
        const chartWidth = canvas.width - padding * 2;
        const chartHeight = canvas.height - padding * 2;
        const maxValue = Math.max(...values, 1);
        const minValue = Math.min(...values, 0);
        const valueRange = maxValue - minValue || 1;

        // Draw title
        if (title) {
            ctx.fillStyle = '#0f172a';
            ctx.font = 'bold 14px -apple-system, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(title, canvas.width / 2, 25);
        }

        // Draw axes
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();

        // Draw grid lines
        ctx.strokeStyle = '#f1f5f9';
        for (let i = 0; i <= 4; i++) {
            const y = padding + (chartHeight / 4) * i;
            ctx.beginPath();
            ctx.moveTo(padding, y);
            ctx.lineTo(canvas.width - padding, y);
            ctx.stroke();
        }

        // Calculate points
        const points = values.map((value, index) => ({
            x: padding + (index / (labels.length - 1)) * chartWidth,
            y: canvas.height - padding - ((value - minValue) / valueRange) * chartHeight,
            value,
            label: labels[index],
        }));

        // Draw fill
        if (fill) {
            ctx.fillStyle = `${color}20`;
            ctx.beginPath();
            ctx.moveTo(points[0].x, canvas.height - padding);
            points.forEach((point) => ctx.lineTo(point.x, point.y));
            ctx.lineTo(points[points.length - 1].x, canvas.height - padding);
            ctx.closePath();
            ctx.fill();
        }

        // Draw line
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach((point) => ctx.lineTo(point.x, point.y));
        ctx.stroke();

        // Draw points
        if (showPoints) {
            points.forEach((point) => {
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        // Draw X-axis labels
        ctx.fillStyle = '#64748b';
        ctx.font = '10px -apple-system, sans-serif';
        ctx.textAlign = 'center';
        const labelStep = Math.ceil(labels.length / 10);
        labels.forEach((label, index) => {
            if (index % labelStep === 0 || index === labels.length - 1) {
                const x = padding + (index / (labels.length - 1)) * chartWidth;
                ctx.save();
                ctx.translate(x, canvas.height - padding + 15);
                ctx.rotate(-Math.PI / 6);
                ctx.fillText(label, 0, 0);
                ctx.restore();
            }
        });

        // Draw Y-axis labels
        ctx.fillStyle = '#64748b';
        ctx.font = '11px -apple-system, sans-serif';
        ctx.textAlign = 'right';
        for (let i = 0; i <= 4; i++) {
            const value = Math.round(minValue + (valueRange / 4) * i);
            const y = canvas.height - padding - (chartHeight / 4) * i;
            ctx.fillText(value.toString(), padding - 5, y + 4);
        }

        // Store chart reference
        const chart = { type: 'line', canvas, ctx, data, options, points };
        this.charts.set(canvasId, chart);
        
        return chart;
    }

    /**
     * Update chart with new data
     */
    updateChart(canvasId, newData) {
        const chart = this.charts.get(canvasId);
        if (!chart) return null;

        chart.data = newData;
        
        if (chart.type === 'bar') {
            return this.createBarChart(canvasId, newData, chart.options);
        } else if (chart.type === 'pie') {
            return this.createPieChart(canvasId, newData, chart.options);
        } else if (chart.type === 'line') {
            return this.createLineChart(canvasId, newData, chart.options);
        }
        
        return chart;
    }

    /**
     * Destroy chart
     */
    destroyChart(canvasId) {
        this.charts.delete(canvasId);
    }

    /**
     * Destroy all charts
     */
    destroyAll() {
        this.charts.clear();
    }
}

// Export for use in other modules
window.ChartsManager = ChartsManager;
