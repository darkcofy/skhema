function initTheme() {
  const saved = localStorage.getItem('skhema-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  else if (window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.setAttribute('data-theme', 'dark');
  updateToggleLabel();
}
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('skhema-theme', next);
  updateToggleLabel();
}
function updateToggleLabel() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = dark ? '\u2600 Light' : '\u263e Dark';
}
function filterCards() {
  const q = document.getElementById('search').value.toLowerCase();
  let total = 0, shown = 0;
  document.querySelectorAll('.card').forEach(c => {
    total++;
    const match = c.dataset.name.toLowerCase().includes(q);
    c.classList.toggle('hidden', !match);
    if (match) shown++;
  });
  document.querySelectorAll('.section').forEach(s => {
    const visible = s.querySelectorAll('.card:not(.hidden)').length;
    s.style.display = visible ? '' : 'none';
  });
  const mc = document.getElementById('matchCount');
  if (mc) mc.textContent = q ? shown + ' of ' + total + ' diagrams' : total + ' diagrams';
}
function openModal(card) {
  const modal = document.getElementById('modal');
  const svg = card.querySelector('.thumb').innerHTML;
  const name = card.querySelector('.name').textContent;
  const href = card.dataset.href;
  document.getElementById('modalTitle').textContent = name;
  document.getElementById('modalSvg').innerHTML = svg;
  document.getElementById('modalLink').href = href;
  modal.classList.add('active');
}
function closeModal() { document.getElementById('modal').classList.remove('active'); }
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
function initScrollTracking() {
  const sections = document.querySelectorAll('.section');
  const navLinks = document.querySelectorAll('.nav-section a');
  if (!sections.length || !navLinks.length) return;
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        navLinks.forEach(l => l.classList.remove('active'));
        const id = e.target.id;
        const link = document.querySelector('.nav-section a[href="#' + id + '"]');
        if (link) link.classList.add('active');
      }
    });
  }, { threshold: 0.1 });
  sections.forEach(s => observer.observe(s));
}
function toggleSidebar() { document.querySelector('.sidebar').classList.toggle('open'); }
initTheme();
document.addEventListener('DOMContentLoaded', () => { initScrollTracking(); filterCards(); });
