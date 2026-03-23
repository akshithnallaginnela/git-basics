// ===== PROGRESS BAR ANIMATION =====
document.addEventListener('DOMContentLoaded', () => {
  // Animate progress bars on load
  requestAnimationFrame(() => {
    document.querySelectorAll('.progress-fill').forEach(el => {
      const w = el.dataset.width;
      setTimeout(() => { el.style.width = w + '%'; }, 100);
    });
  });

  // ===== HEATMAP GENERATION =====
  const heatmapData = [
    // 4 weeks × 7 days = 28 cells, values 0-100
    0,  25, 100, 75,  50, 25,  0,
    50, 75, 100, 100, 75, 50, 25,
    25, 50,  75, 100, 50, 75, 100,
    75, 100, 50,  25, 75, 50,  25
  ];

  const colorMap = (val) => {
    if (val === 0)   return '#F2FDFB';
    if (val <= 25)   return '#C8F0EC';
    if (val <= 50)   return '#7ECCC7';
    if (val <= 75)   return '#26C6BF';
    return '#1A3A38';
  };

  const grid = document.getElementById('heatmap');
  const today = new Date();

  heatmapData.forEach((val, i) => {
    const cell = document.createElement('div');
    cell.className = 'hm-cell';
    cell.style.background = colorMap(val);

    // Tooltip on hover
    const d = new Date(today);
    d.setDate(today.getDate() - (27 - i));
    const label = d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    cell.title = `${label}: ${val}% complete`;

    grid.appendChild(cell);
  });
});
