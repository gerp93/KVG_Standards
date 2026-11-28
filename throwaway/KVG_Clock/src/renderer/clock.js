const NS = 'http://www.w3.org/2000/svg';

function build() {
  const ticks = document.getElementById('ticks');
  for (let i = 0; i < 60; i++) {
    const major = i % 5 === 0;
    const line = document.createElementNS(NS, 'line');
    line.setAttribute('class', major ? 'tick major' : 'tick');
    line.setAttribute('y1', major ? -88 : -92);
    line.setAttribute('y2', -96);
    line.setAttribute('transform', `rotate(${i * 6})`);
    ticks.appendChild(line);
  }
  const numerals = document.getElementById('numerals');
  for (let h = 1; h <= 12; h++) {
    const a = (h * 30 * Math.PI) / 180;
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('class', 'numeral');
    t.setAttribute('x', (Math.sin(a) * 74).toFixed(2));
    t.setAttribute('y', (-Math.cos(a) * 74).toFixed(2));
    t.textContent = h;
    numerals.appendChild(t);
  }
}

function tick() {
  const now = new Date();
  const s = now.getSeconds() + now.getMilliseconds() / 1000;
  const m = now.getMinutes() + s / 60;
  const h = (now.getHours() % 12) + m / 60;
  document.getElementById('second').setAttribute('transform', `rotate(${s * 6})`);
  document.getElementById('minute').setAttribute('transform', `rotate(${m * 6})`);
  document.getElementById('hour').setAttribute('transform', `rotate(${h * 30})`);
  requestAnimationFrame(tick);
}

build();
tick();
