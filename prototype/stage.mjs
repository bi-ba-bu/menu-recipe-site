/**
 * stage.mjs — 原型舞台控制
 *
 * 职责：
 *   1. 把 demo.html（真实骨架 + 可爱皮肤）装进 iframe
 *   2. 顶部导航切换场景时只换 iframe 的 hash，不重载整个页面
 *   3. 同步登录态：原型与真实页面同源，登录一次即可看真实数据
 */

const frame = document.getElementById('stageFrame');
const links = Array.from(document.querySelectorAll('[data-stage-link]'));

/** 登录态：从同源的真实页面本地存储读取（原型共用同一份会话） */
const TOKEN_KEY = 'menu-recipe-token';

/** 演示用会话 token：没有登录过时兜底，保证设计稿能展示真实布局 */
const DEMO_TOKEN_KEY = 'cute-prototype-token';

function ensureToken() {
  try {
    if (localStorage.getItem(TOKEN_KEY)) return;
    const demo = localStorage.getItem(DEMO_TOKEN_KEY);
    if (demo) localStorage.setItem(TOKEN_KEY, demo);
  } catch {
    /* 隐私模式忽略 */
  }
}

function syncActive(route) {
  links.forEach((a) => {
    a.classList.toggle('is-active', a.dataset.stageLink === route);
  });
}

function currentRoute() {
  const h = location.hash.replace('#', '');
  return h || new URLSearchParams(location.search).get('v') || 'family';
}

function load() {
  ensureToken();
  const route = currentRoute();
  syncActive(route);
  frame.src = `./demo.html#${route}`;
}

/* 顶部导航：点击只改 hash */
links.forEach((a) => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    const route = a.dataset.stageLink;
    history.replaceState(null, '', `?v=${route}#${route}`);
    syncActive(route);
    frame.contentWindow?.location.replace(`./demo.html#${route}`);
  });
});

/* 关闭说明栏，得到纯净的整屏效果 */
document.getElementById('stageClose')?.addEventListener('click', () => {
  document.body.classList.add('is-bar-hidden');
});

window.addEventListener('hashchange', load);

load();
