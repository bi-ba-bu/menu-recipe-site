/**
 * appearance.js — 外观设置：明暗 + 风格（两个独立维度）
 *
 * 【两个维度，互不干扰】
 *   1. 明暗  data-theme = 'light' | 'dark'   → 由 main.css 的令牌负责
 *      没设置时跟随系统 prefers-color-scheme（保持原站行为）
 *   2. 风格  data-skin  = 'cute' | 不设置     → 由 css/skins/cute.css 负责
 *      不设置 = 默认风格，与本次改动之前完全一致
 *
 * 于是有四种合法组合：
 *   默认浅色 / 默认深色 / 可爱浅色 / 可爱深色
 *
 * 【为什么风格用「不设置」表示默认，而不是写 data-skin="default"】
 *   皮肤文件常驻加载，规则全部挂在 :root[data-skin="cute"] 下。
 *   「不设置」时它一条都不命中 —— 默认风格的渲染路径上没有任何多余规则，
 *   也就不存在"关掉皮肤后还残留一点样式"的风险。
 *
 * 存储键：
 *   menu-recipe-theme  沿用原站，用户此前在顶栏切换过的选择原样继承
 *   menu-recipe-skin   新增，只记录可爱风开/关
 */

import { UI_ICONS } from './icons.js';

const THEME_KEY = 'menu-recipe-theme';
const SKIN_KEY = 'menu-recipe-skin';

/* ── 元信息 ──────────────────────────────────────────────────── */

/** 明暗两种取值（顺序即展示顺序） */
export const THEMES = [
  { key: 'light', label: '浅色', desc: '明亮清爽', icon: 'sun' },
  { key: 'dark', label: '深色', desc: '暗色柔光', icon: 'moon' }
];

/** 风格两种取值 */
export const SKINS = [
  { key: 'default', label: '默认', desc: '暖橙餐厅风', icon: 'brand' },
  { key: 'cute', label: '可爱', desc: '糖果圆润风', icon: 'palette' }
];

/**
 * 预览四色块：底 / 卡 / 主色 / 辅色。
 * 按「风格 × 明暗」给出真实配色，让人一眼看出组合后的样子。
 */
const SWATCH = {
  'default-light': ['#f6f4f0', '#ffffff', '#e0654a', '#2f9e6f'],
  'default-dark': ['#16181d', '#1e2127', '#f07e63', '#4cc38a'],
  'cute-light': ['#fff7f2', '#ffffff', '#ff7fa5', '#5ccfb0'],
  'cute-dark': ['#221c2b', '#2c2436', '#ff8fb0', '#6fdcc0']
};

function swatch(skin, theme) {
  return SWATCH[`${skin}-${theme}`] || SWATCH['default-light'];
}

/* ── 读写当前状态 ────────────────────────────────────────────── */

const root = document.documentElement;

/** 当前明暗：手动选过就以 data-theme 为准，否则跟随系统 */
export function currentTheme() {
  const saved = root.dataset.theme;
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/** 当前风格：只有 'cute' 与 'default' 两种 */
export function currentSkin() {
  return root.dataset.skin === 'cute' ? 'cute' : 'default';
}

/* ── 应用状态 ────────────────────────────────────────────────── */

export function applyTheme(key) {
  const next = key === 'dark' ? 'dark' : 'light';
  root.dataset.theme = next;
  try {
    localStorage.setItem(THEME_KEY, next);
  } catch {
    /* 隐私模式下写入失败可忽略，本次会话内仍然生效 */
  }
  return next;
}

export function applySkin(key) {
  const next = key === 'cute' ? 'cute' : 'default';
  if (next === 'cute') root.dataset.skin = 'cute';
  else delete root.dataset.skin; // 删属性而不是写空值，保持「默认 = 无属性」
  try {
    localStorage.setItem(SKIN_KEY, next);
  } catch {
    /* 同上 */
  }
  return next;
}

/**
 * 启动时恢复上次的外观。
 *
 * 明暗：只恢复手动选择过的值；没选过就不写 data-theme，继续跟随系统。
 * 风格：default 时连属性都不加，保证默认风格零皮肤规则命中。
 */
export function initAppearance() {
  try {
    const t = localStorage.getItem(THEME_KEY);
    if (t === 'light' || t === 'dark') root.dataset.theme = t;

    const s = localStorage.getItem(SKIN_KEY);
    if (s === 'cute') root.dataset.skin = 'cute';
    else delete root.dataset.skin;
  } catch {
    /* 隐私模式：按默认走 */
  }
}

/* ── 面板 HTML ───────────────────────────────────────────────── */

function cardsHtml({ group, entries, activeKey, skin, theme }) {
  return entries
    .map((item) => {
      const on = item.key === activeKey;
      const dot = swatch(group === 'skin' ? item.key : skin, group === 'theme' ? item.key : theme);
      return `
        <label class="choice-card ${on ? 'is-active' : ''}" data-choice-card="${item.key}">
          <input class="choice-card__radio" type="radio" name="${group === 'skin' ? 'appSkin' : 'appTheme'}"
                 value="${item.key}" ${on ? 'checked' : ''} />
          <span class="choice-card__preview" aria-hidden="true">
            ${dot.map((c) => `<span class="choice-card__dot" style="background:${c}"></span>`).join('')}
          </span>
          <span class="choice-card__body">
            <span class="choice-card__name">
              <span class="choice-card__ico">${UI_ICONS[item.icon] || ''}</span>${item.label}
            </span>
            <span class="choice-card__desc">${item.desc}</span>
          </span>
          <span class="choice-card__check" aria-hidden="true">${UI_ICONS.check}</span>
        </label>`;
    })
    .join('');
}

/**
 * 家庭设置里的「外观」面板。
 *
 * 用 fieldset + 原生 radio 而不是按钮：
 * 这是「二选一」的语义，屏幕阅读器能正确播报选中状态，
 * 键盘可以用方向键在组内切换，比一串按钮更合规范。
 */
export function appearancePanelHtml() {
  const theme = currentTheme();
  const skin = currentSkin();
  const themeLabel = THEMES.find((t) => t.key === theme)?.label || '浅色';
  const skinLabel = SKINS.find((s) => s.key === skin)?.label || '默认';

  return `
    <section class="panel appearance-panel" id="appearancePanel" aria-labelledby="appearanceTitle">
      <div class="panel__head">
        <h3 id="appearanceTitle">
          <span class="appearance-panel__ico" aria-hidden="true">${UI_ICONS.palette}</span>外观
        </h3>
      </div>

      <div class="appearance-group">
        <div class="appearance-group__head">
          <span class="appearance-group__title" id="appearanceThemeTitle">明暗</span>
          <span class="appearance-group__value" id="appearanceThemeValue">当前：${themeLabel}</span>
        </div>
        <fieldset class="choice-grid" role="radiogroup" aria-labelledby="appearanceThemeTitle">
          <legend class="sr-only">选择明暗主题</legend>
          ${cardsHtml({ group: 'theme', entries: THEMES, activeKey: theme, skin, theme })}
        </fieldset>
      </div>

      <div class="appearance-group">
        <div class="appearance-group__head">
          <span class="appearance-group__title" id="appearanceSkinTitle">风格</span>
          <span class="appearance-group__value" id="appearanceSkinValue">当前：${skinLabel}</span>
        </div>
        <fieldset class="choice-grid" role="radiogroup" aria-labelledby="appearanceSkinTitle">
          <legend class="sr-only">选择界面风格</legend>
          ${cardsHtml({ group: 'skin', entries: SKINS, activeKey: skin, skin, theme })}
        </fieldset>
      </div>

      <p class="appearance-panel__foot">
        明暗与风格互不影响，可自由组合。选择会记在这台设备上，下次打开自动恢复。
      </p>
    </section>`;
}

/* ── 面板状态同步 ────────────────────────────────────────────── */

/**
 * 把面板刷成当前真实状态。
 *
 * 单独抽出是因为：家庭页每次重新渲染都会整块替换 innerHTML，
 * 新面板是按"生成那一刻"的状态写出来的 HTML，切换之后可能已过期。
 * 所以「插入新面板」和「切换之后」两个时机都要调它。
 */
function syncPanel(panel) {
  if (!panel) return;
  const theme = currentTheme();
  const skin = currentSkin();

  panel.querySelectorAll('[data-choice-card]').forEach((card) => {
    const group = card.querySelector('input')?.name === 'appSkin' ? 'skin' : 'theme';
    const want = group === 'skin' ? skin : theme;
    const on = card.dataset.choiceCard === want;
    card.classList.toggle('is-active', on);
    const radio = card.querySelector('input');
    if (radio) radio.checked = on;

    // 预览色块跟着组合变：切风格时明暗卡片的色块也要更新
    const dots = card.querySelectorAll('.choice-card__dot');
    const colors = swatch(
      group === 'skin' ? card.dataset.choiceCard : skin,
      group === 'theme' ? card.dataset.choiceCard : theme
    );
    dots.forEach((d, i) => {
      if (colors[i]) d.style.background = colors[i];
    });
  });

  const tVal = panel.querySelector('#appearanceThemeValue');
  if (tVal) tVal.textContent = `当前：${THEMES.find((t) => t.key === theme)?.label || '浅色'}`;
  const sVal = panel.querySelector('#appearanceSkinValue');
  if (sVal) sVal.textContent = `当前：${SKINS.find((s) => s.key === skin)?.label || '默认'}`;
}

/* ── 绑定 ────────────────────────────────────────────────────── */

let toastTimer = null;

function toast(msg) {
  const host = document.getElementById('toast');
  if (!host) return;
  host.textContent = msg;
  host.classList.add('is-show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => host.classList.remove('is-show'), 1800);
}

/** 系统主题变化：仅在用户没手动选过时同步面板 */
let systemWatcherBound = false;

/** 切换后的回调（app.js 用它重绘家庭页头像） */
let changeListener = null;

/**
 * 绑定交互 + 同步状态。
 *
 * 事件监听只加一次（靠 dataset.bound 判断），但状态每次都同步——
 * 否则 MutationObserver 重新插入的新面板会停留在过期的选中态。
 */
export function bindAppearancePanel(panel, onChange) {
  if (!panel) return;
  if (typeof onChange === 'function') changeListener = onChange;

  if (panel.dataset.bound !== '1') {
    panel.dataset.bound = '1';

    panel.addEventListener('change', (e) => {
      const radio = e.target.closest('.choice-card__radio');
      if (!radio) return;

      if (radio.name === 'appSkin') {
        applySkin(radio.value);
        toast(radio.value === 'cute' ? '已切换到可爱风格' : '已切换到默认风格');
      } else {
        applyTheme(radio.value);
        toast(radio.value === 'dark' ? '已切换到深色' : '已切换到浅色');
      }

      syncPanel(panel);
      if (changeListener) changeListener();
    });
  }

  if (!systemWatcherBound && typeof window.matchMedia === 'function') {
    systemWatcherBound = true;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      if (!document.documentElement.dataset.theme) {
        syncPanel(document.getElementById('appearancePanel'));
      }
    };
    if (typeof mq.addEventListener === 'function') mq.addEventListener('change', onChange);
  }

  syncPanel(panel);
}

export { THEME_KEY, SKIN_KEY };
