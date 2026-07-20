/* ============================================
   Kalemna — Particle System (particles.js)
   كلمنا — نظام الجسيمات المتحركة
   ============================================ */

export class ParticleSystem {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;

    this.ctx = this.canvas.getContext('2d');
    this.particles = [];
    this.maxParticles = 50;
    this.mouse = { x: null, y: null };
    this.animationId = null;
    this.isVisible = true;

    this._resize();
    this._createParticles();
    this._bindEvents();
    this._animate();
  }

  _resize() {
    this.canvas.width = window.innerWidth;
    this.canvas.height = window.innerHeight;
  }

  _getThemeColors() {
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    switch (theme) {
      case 'light':
        return {
          particle: 'rgba(99, 72, 221, 0.08)',
          line: 'rgba(99, 72, 221, 0.04)',
        };
      case 'midnight':
        return {
          particle: 'rgba(0, 200, 255, 0.12)',
          line: 'rgba(180, 100, 255, 0.06)',
        };
      default: // dark
        return {
          particle: 'rgba(255, 255, 255, 0.06)',
          line: 'rgba(255, 255, 255, 0.025)',
        };
    }
  }

  _createParticles() {
    this.particles = [];
    for (let i = 0; i < this.maxParticles; i++) {
      this.particles.push({
        x: Math.random() * this.canvas.width,
        y: Math.random() * this.canvas.height,
        size: Math.random() * 2.5 + 1,
        speedX: (Math.random() - 0.5) * 0.4,
        speedY: (Math.random() - 0.5) * 0.4,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }
  }

  _bindEvents() {
    window.addEventListener('resize', () => {
      this._resize();
      this._createParticles();
    });

    window.addEventListener('mousemove', (e) => {
      this.mouse.x = e.clientX;
      this.mouse.y = e.clientY;
    });

    window.addEventListener('mouseout', () => {
      this.mouse.x = null;
      this.mouse.y = null;
    });

    // Pause when tab is hidden for performance
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.isVisible = false;
        cancelAnimationFrame(this.animationId);
      } else {
        this.isVisible = true;
        this._animate();
      }
    });

    // Re-color on theme change
    window.addEventListener('themechange', () => {
      // Colors update automatically on next frame
    });
  }

  _animate() {
    if (!this.isVisible) return;

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    const colors = this._getThemeColors();

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];

      // Update position
      p.x += p.speedX;
      p.y += p.speedY;

      // Wrap around edges
      if (p.x < 0) p.x = this.canvas.width;
      if (p.x > this.canvas.width) p.x = 0;
      if (p.y < 0) p.y = this.canvas.height;
      if (p.y > this.canvas.height) p.y = 0;

      // Mouse proximity — gentle push
      if (this.mouse.x !== null && this.mouse.y !== null) {
        const dx = p.x - this.mouse.x;
        const dy = p.y - this.mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          const force = (120 - dist) / 120;
          p.x += (dx / dist) * force * 1.5;
          p.y += (dy / dist) * force * 1.5;
        }
      }

      // Draw particle
      this.ctx.beginPath();
      this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      this.ctx.fillStyle = colors.particle;
      this.ctx.fill();

      // Draw connections
      for (let j = i + 1; j < this.particles.length; j++) {
        const p2 = this.particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 150) {
          this.ctx.beginPath();
          this.ctx.moveTo(p.x, p.y);
          this.ctx.lineTo(p2.x, p2.y);
          this.ctx.strokeStyle = colors.line;
          this.ctx.lineWidth = 0.5;
          this.ctx.stroke();
        }
      }
    }

    this.animationId = requestAnimationFrame(() => this._animate());
  }

  destroy() {
    cancelAnimationFrame(this.animationId);
    this.particles = [];
  }
}
