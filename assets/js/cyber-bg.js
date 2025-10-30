(() => {
  // Cyber background animation module
  const canvas = document.getElementById('cyber-canvas');
  if (!canvas) return; // nothing to do on pages without the canvas

  const ctx = canvas.getContext('2d');
  var W, H;
  const trails = [];
  const TRAIL_COUNT = 3;

  function resizeCanvas() {
    W = window.innerWidth;
    H = window.innerHeight;
    canvas.width = W;
    canvas.height = H;
    initTrails();
  }

  function initTrails() {
    trails.length = 0;
    for (let i = 0; i < TRAIL_COUNT; i++) {
      trails.push({
        color: i % 3 === 0 ? 'rgba(79, 70, 229, 0.8)' : i % 3 === 1 ? 'rgba(34, 197, 94, 0.8)' : 'rgba(167, 139, 250, 0.8)',
        speed: (0.5 + Math.random()) * 0.5,
        amplitude: (H / 4) + (Math.random() * (H / 6)),
        frequency: 0.0005 + Math.random() * 0.0005,
        yOffset: H / 2 + (i - TRAIL_COUNT / 2) * 50
      });
    }
  }

  function animate(time) {
    requestAnimationFrame(animate);
    ctx.fillStyle = 'rgba(18, 25, 33, 0.1)';
    ctx.fillRect(0, 0, W, H);

    trails.forEach(trail => {
      ctx.beginPath();
      ctx.strokeStyle = trail.color;
      ctx.lineWidth = 2;
      ctx.shadowBlur = 15;
      ctx.shadowColor = trail.color;
      ctx.moveTo(-10, trail.yOffset);
      for (let x = -10; x <= W + 10; x += 5) {
        const y = trail.yOffset + Math.sin(x * trail.frequency + time * trail.speed * 0.005) * trail.amplitude * Math.sin(time * 0.0001);
        ctx.lineTo(x, y);
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    });
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  animate(0);
})();
