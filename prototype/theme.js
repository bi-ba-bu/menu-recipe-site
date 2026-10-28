/**
 * theme.js — 主题切换（原型版）
 *
 * 现有机制（原站 js/app.js）：
 *   顶栏右侧有一个「日/月」图标按钮，点一下在 light / dark 之间切换，
 *   选择存在 localStorage 的 menu-recipe-theme 里。
 *
 * 本次改动（按需求）：
 *   · 把主题切换从顶栏移进「家庭设置」页，做成两个可视化选项卡片
 *   · 仍然只保留这两种主题（浅色 / 深色），不引入第三种
 *   · 顶栏那个图标按钮在原型里隐藏，避免两处入口互相打架
 *
 * 这里复用同一套约定：同样读写 menu-recipe-theme，同样用
 * document.documentElement.dataset.theme，所以与已有逻辑完全兼容——
 * 用户此前在顶栏切换过的选择会被原样继承。
 */

import { UI_ICONS } from './icons.js';

/** localStorage 键：与 app.js 中的保持一致 */
const THEME_KEY = 'menu-recipe-theme';

/** toast 计时器：与 app.js 里的同名变量互不影响（各自作用域） */
let toastTimer = null;

/** 两种主题的元信息（顺序即展示顺序） */
export const THEMES = [
  {
    key: 'light',
    label: '浅色',
    desc: '奶油草莓 · 明亮清爽',
    icon: 'sun',
    /* 预览色块：底 / 卡 / 主色 / 辅色 */
    swatch: ['#fff7f2', '#ffffff', '#ff7fa5', '#5ccfb0']
  },
  {
    key: 'dark',
    label: '深色',
    desc: '夜间软糖 · 暗紫柔光',
    icon: 'moon',
    swatch: ['#221c2b', '#2c2436', '#ff8fb0', '#6fdcc0']
  }
];

/**
 * 当前生效的主题。
 * 没有手动选过时跟随系统（prefers-color-scheme），与 app.js 的判断一致。
 */
export function currentTheme() {
  const saved = document.documentElement.dataset.theme;
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/** 应用并持久化主题 */
export function applyTheme(key) {
  const next = key === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = next;
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* 隐私模式下写入失败可忽略，本次会话内仍然生效 */
  }
  return next;
}

/**
 * 家庭设置里的主题选择器。
 *
 * 用 radio 而不是 button：这是「二选一」的语义，屏幕阅读器能正确播报
 * 选中状态，键盘也能用方向键切换，比一串按钮更合规范。
 */
export function themePickerHtml() {
  const active = currentTheme();

  const cards = THEMES.map(
    (t) => `
      <label class="theme-card ${t.key === active ? 'is-active' : ''}" data-theme-card="${t.key}">
        <input class="theme-card__radio" type="radio" name="appTheme"
               value="${t.key}" ${t.key === active ? 'checked' : ''} />
        <span class="theme-card__preview" aria-hidden="true">
          <span class="theme-card__dot" style="background:${t.swatch[0]}"></span>
          <span class="theme-card__dot" style="background:${t.swatch[1]}"></span>
          <span class="theme-card__dot" style="background:${t.swatch[2]}"></span>
          <span class="theme-card__dot" style="background:${t.swatch[3]}"></span>
        </span>
        <span class="theme-card__body">
          <span class="theme-card__name">
            <span class="theme-card__ico">${UI_ICONS[t.icon] || ''}</span>
            ${t.label}
          </span>
          <span class="theme-card__desc">${t.desc}</span>
        </span>
        <span class="theme-card__check" aria-hidden="true">${UI_ICONS.check}</span>
      </label>`
  ).join('');

  return `
    <section class="panel appearance-panel" id="appearancePanel" aria-labelledby="appearanceTitle">
      <div class="panel__head">
        <h3 id="appearanceTitle">
          <span class="appearance-panel__ico" aria-hidden="true">${UI_ICONS.palette}</span>
          界面主题
        </h3>
        <span class="muted" id="appearanceHint">当前：${active === 'dark' ? '深色' : '浅色'}</span>
      </div>
      <fieldset class="theme-picker" role="radiogroup" aria-label="界面主题">
        <legend class="sr-only">选择界面主题</legend>
        ${cards}
      </fieldset>
      <p class="appearance-panel__foot">选择会记在这台设备上，下次打开自动恢复。</p>
    </section>`;
}

/**
 * 把面板的选中态刷成当前真实主题。
 *
 * 单独抽出来是因为：家庭页每次重新渲染都会整块替换 innerHTML，
 * 新插入的面板是按"渲染那一刻"的主题生成的 HTML —— 但主题切换
 * 之后又重渲染时，HTML 里的 initial 状态可能已经过期。
 * 所以「插入新面板」和「切换主题」两个时机都要调它。
 */
function syncPanel(panel) {
  if (!panel) return;
  const now = currentTheme();
  panel.querySelectorAll('[data-theme-card]').forEach((card) => {
    const on = card.dataset.themeCard === now;
    card.classList.toggle('is-active', on);
    const radio = card.querySelector('input');
    if (radio) radio.checked = on;
  });
  const hint = panel.querySelector('#appearanceHint');
  if (hint) hint.textContent = `当前：${now === 'dark' ? '深色' : '浅色'}`;
}

/**
 * 绑定交互 + 同步状态。
 *
 * 注意不能因为「已绑定过」就提前 return，否则 MutationObserver 重新
 * 插入的新面板永远不会被同步，表现为卡片高亮与实际主题不一致。
 * 事件监听仍然只加一次（靠 dataset.bound 判断）。
 */
/* 系统主题变化时，如果用户没手动选过，面板要跟着实时变 */
let systemWatcherBound = false;

export function bindThemePicker(root = document) {
  const panel = root.querySelector('#appearancePanel');
  if (!panel) return;

  if (panel.dataset.bound !== '1') {
    panel.dataset.bound = '1';

    panel.addEventListener('change', (e) => {
      const radio = e.target.closest('input[name="appTheme"]');
      if (!radio) return;
      applyTheme(radio.value);
      syncPanel(panel);
      // 复用原站的 toast，不另起一套提示系统
      const host = document.getElementById('toast');
      if (host) {
        host.textContent = radio.value === 'dark' ? '已切换到深色主题' : '已切换到浅色主题';
        host.classList.add('is-show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => host.classList.remove('is-show'), 1800);
      }
    });
  }

  // 监听系统主题变化：仅在用户没有手动选择过时生效
  // （手动选过就会写 data-theme，此时 currentTheme 不受系统影响）
  if (!systemWatcherBound && typeof window.matchMedia === 'function') {
    systemWatcherBound = true;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      if (!document.documentElement.dataset.theme) {
        syncPanel(document.querySelector('#appearancePanel'));
      }
    };
    if (typeof mq.addEventListener === 'function') mq.addEventListener('change', onChange);
  }

  // 无论是否首次绑定，都把选中态刷成真实主题
  syncPanel(panel);
}

export { THEME_KEY };
