/**
 * cute-skin.js — 可爱风格对家庭页的增强（只在 data-skin="cute" 时生效）
 *
 * 为什么要单独一层：
 *   家庭页的头像（.family-hero__avatar / .member-row__avatar）是 app.js
 *   渲染出来的 HTML 字符串。要换成 Q 版 SVG 有两条路：
 *     a) 改 app.js 的渲染函数 —— 默认风格也要背这个分支，不符合「默认不变」
 *     b) 渲染完成后在 DOM 上替换 —— 默认风格下根本不调用
 *   选 b：默认风格的代码路径与改动前的 app.js 完全一致。
 *
 * 还原策略：
 *   替换前把原始 HTML 存进「不会被替换掉的那个节点」的 dataset 上。
 *   · 主卡：原头像节点本身会被 replaceWith 移走，所以存在 .family-hero 上
 *   · 成员行：innerHTML 替换，节点本身还在，存在自己的 dataset.rawHtml 上
 *   切回默认风格时按这些存档还原，不重绘整页（避免丢滚动位置与焦点）。
 */

import { cutePairHtml, memberAvatarHtml, miniPairHtml } from './cute-avatars.js';

const HERO_RAW_KEY = 'rawAvatarHtml';

function isCute() {
  return document.documentElement.dataset.skin === 'cute';
}

/** 页面上真实渲染出的成员名（家庭页数据回填后才拿得到） */
function pageMemberNames() {
  return [...document.querySelectorAll('.member-row__name')]
    .map((el) => el.textContent.trim().split(/\s+/)[0])
    .filter(Boolean);
}

/**
 * 演示用名字。
 *
 * 演示数据里「厨师的家庭」只有 1 名成员，双人头像的完整形态展示不出来。
 * 只在「真实成员不足 2 人」时补齐，真实成员 ≥2 时永远用真实名字。
 */
const DEMO_MEMBERS = ['妈妈', '爸爸'];

function pickNames(realNames = []) {
  if (realNames.length >= 2) return realNames;
  if (realNames.length === 1) return [realNames[0], DEMO_MEMBERS[1]];
  return DEMO_MEMBERS;
}

/* ── 家庭主卡 ────────────────────────────────────────────────── */

function patchHero() {
  document.querySelectorAll('.family-hero').forEach((hero) => {
    if (hero.querySelector('.cute-pair')) return;

    const old = hero.querySelector('.family-hero__avatar');
    if (!old) return;

    // 存档挂在 hero 上：old 自己马上要被移走，存它身上就丢了
    hero.dataset[HERO_RAW_KEY] = old.outerHTML;

    const slot = document.createElement('span');
    slot.innerHTML = cutePairHtml(pickNames(pageMemberNames()));
    const node = slot.firstElementChild;
    if (node) old.replaceWith(node);
  });
}

/* ── 成员行 ──────────────────────────────────────────────────── */

function patchMembers() {
  document.querySelectorAll('.member-row__avatar').forEach((el, i) => {
    if (el.dataset.cute === '1') return;
    if (el.dataset.rawHtml == null) el.dataset.rawHtml = el.innerHTML;
    el.dataset.cute = '1';
    el.innerHTML = memberAvatarHtml(el.textContent.trim() || '小朋友', i + 1);
  });
}

/* ── 家庭切换列表 ────────────────────────────────────────────── */

function patchFamilyCards() {
  document.querySelectorAll('.family-card').forEach((card) => {
    if (card.querySelector('.family-mini-avatars')) return;
    const body = card.querySelector('.family-card__body');
    if (!body) return;

    const slot = document.createElement('span');
    slot.innerHTML = miniPairHtml(pickNames(pageMemberNames()));
    const node = slot.firstElementChild;
    if (node) body.before(node);
  });
}

/* ── 还原 ────────────────────────────────────────────────────── */

/** 把 DOM 还原成 app.js 原始渲染的样子 */
export function restoreCuteAvatars() {
  // 主卡：移除 Q 版双人头像，插回原单字头像
  document.querySelectorAll('.family-hero').forEach((hero) => {
    const pair = hero.querySelector('.cute-pair');
    if (!pair) return;
    pair.remove();
    const raw = hero.dataset[HERO_RAW_KEY];
    if (raw && !hero.querySelector('.family-hero__avatar')) {
      hero.insertAdjacentHTML('afterbegin', raw);
    }
  });

  // 成员行：按存档还原 innerHTML
  document.querySelectorAll('.member-row__avatar').forEach((el) => {
    if (el.dataset.cute !== '1') return;
    if (el.dataset.rawHtml != null) el.innerHTML = el.dataset.rawHtml;
    delete el.dataset.cute;
  });

  // 家庭列表：移除迷你头像
  document.querySelectorAll('.family-card .family-mini-avatars').forEach((el) => el.remove());
}

/* ── 入口 ────────────────────────────────────────────────────── */

/**
 * 刷新家庭页的可爱头像。
 * 由 app.js 在 renderFamilyPage() 之后、以及风格切换后调用。
 * 默认风格下只做还原，不产生任何新增节点。
 */
export function refreshCuteAvatars() {
  if (!isCute()) {
    restoreCuteAvatars();
    return;
  }
  patchHero();
  patchMembers();
  patchFamilyCards();
}
