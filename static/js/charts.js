/**
 * Railway Control System — Charts.js
 * Reusable Chart.js configuration utilities.
 */
'use strict';

const RCSCharts = {
  COLORS: {
    blue:'#3b82f6', green:'#10b981', red:'#ef4444', yellow:'#f59e0b',
    purple:'#8b5cf6', cyan:'#06b6d4', orange:'#f97316', pink:'#ec4899',
    grid:'rgba(255,255,255,0.04)', text:'#8892a4', bg:'#1a2234',
  },

  baseOptions(extra={}) {
    return {
      responsive:true, maintainAspectRatio:false,
      animation:{duration:700, easing:'easeInOutQuart'},
      plugins:{
        legend:{display:false},
        tooltip:{backgroundColor:this.COLORS.bg, borderColor:'rgba(255,255,255,0.1)', borderWidth:1, titleColor:'#e8eaf0', bodyColor:'#8892a4', padding:10, cornerRadius:8},
      },
      scales:{
        x:{grid:{color:this.COLORS.grid}, ticks:{color:this.COLORS.text, font:{size:11}}},
        y:{grid:{color:this.COLORS.grid}, ticks:{color:this.COLORS.text, font:{size:11}}},
      },
      ...extra,
    };
  },

  gradient(ctx, colorHex, alphaTop=0.3, alphaBot=0.01) {
    const grad = ctx.createLinearGradient(0,0,0,300);
    grad.addColorStop(0, colorHex + Math.round(alphaTop*255).toString(16).padStart(2,'0'));
    grad.addColorStop(1, colorHex + Math.round(alphaBot*255).toString(16).padStart(2,'0'));
    return grad;
  },

  line(canvasId, labels, datasets, extra={}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    const styledDatasets = datasets.map((ds,i) => {
      const color = ds.color || Object.values(this.COLORS)[i] || this.COLORS.blue;
      return {
        ...ds, borderColor:color,
        backgroundColor: ds.fill!==false ? this.gradient(ctx,color) : 'transparent',
        borderWidth:2.5, tension:ds.tension!==undefined?ds.tension:0.4,
        fill:ds.fill!==false, pointRadius:4, pointHoverRadius:6,
        pointBackgroundColor:color, pointBorderColor:'#1a2234', pointBorderWidth:2,
      };
    });
    return new Chart(ctx, {type:'line', data:{labels,datasets:styledDatasets}, options:this.baseOptions(extra)});
  },

  bar(canvasId, labels, data, colorFn, extra={}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const colors = Array.isArray(colorFn) ? colorFn : data.map((v,i)=>typeof colorFn==='function'?colorFn(v,i):(colorFn||this.COLORS.blue));
    return new Chart(canvas, {
      type:'bar',
      data:{labels, datasets:[{data, backgroundColor:colors.map(c=>c+'bb'), borderColor:colors, borderWidth:1, borderRadius:5, borderSkipped:false}]},
      options:this.baseOptions(extra),
    });
  },

  doughnut(canvasId, labels, data, colors, extra={}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    return new Chart(canvas, {
      type:'doughnut',
      data:{labels, datasets:[{data, backgroundColor:colors, borderColor:'#1a2234', borderWidth:2, hoverOffset:8}]},
      options:{
        responsive:true, maintainAspectRatio:false, cutout:'65%', animation:{duration:700},
        plugins:{
          legend:{position:'bottom', labels:{color:this.COLORS.text, font:{size:11}, padding:10, usePointStyle:true}},
          tooltip:{backgroundColor:this.COLORS.bg, borderColor:'rgba(255,255,255,0.1)', borderWidth:1},
        },
        ...extra,
      },
    });
  },

  gauge(containerId, value, max=100, color='#3b82f6', label='') {
    const el = document.getElementById(containerId);
    if (!el) return;
    const pct = Math.min(100,(value/max)*100);
    const circ = 2*Math.PI*45;
    const offset = circ-(pct/100)*circ;
    el.innerHTML=`<svg viewBox="0 0 100 100" style="width:100%;height:100%;"><circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="8"/><circle cx="50" cy="50" r="45" fill="none" stroke="${color}" stroke-width="8" stroke-dasharray="${circ}" stroke-dashoffset="${offset}" stroke-linecap="round" transform="rotate(-90 50 50)" style="transition:stroke-dashoffset 0.8s ease;"/><text x="50" y="46" text-anchor="middle" fill="#e8eaf0" style="font-family:Inter,sans-serif;font-size:18px;font-weight:800;">${Math.round(pct)}%</text><text x="50" y="60" text-anchor="middle" fill="#8892a4" style="font-family:Inter,sans-serif;font-size:8px;">${label}</text></svg>`;
  },

  updateChart(chartInstance, newLabels, newData) {
    if (!chartInstance) return;
    if (newLabels) chartInstance.data.labels = newLabels;
    chartInstance.data.datasets.forEach((ds,i)=>{ if(Array.isArray(newData)) ds.data=newData; else if(newData&&newData[i]) ds.data=newData[i]; });
    chartInstance.update('active');
  },
};

window.RCSCharts = RCSCharts;
