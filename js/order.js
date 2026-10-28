/**
 * order.js — 点餐模块
 *
 * 职责：把菜品以"点餐"的方式加入一周中某一天的某一餐。
 *
 * 数据模型：
 *   orders = {
 *     "mon": { breakfast: [{ id, qty }], lunch: [...], dinner: [...] },
 *     ...
 *   }
 *
 * 设计要点：
 *   · 同一道菜在同一天同一餐只能有一条记录，重复加入走数量累加
 *   · 订单持久化到 localStorage，刷新不丢
 *   · 渲染与事件由 app.js 调度，本模块只提供数据操作 + HTML 片段
 */

import { RECIPES, TAG_META } from './data.js';
import { getDishIcon, UI_ICONS, starHtml } from './icons.js';

export const DAYS = [
  { key: 'mon', label: '周一', short: '周一' },
  { key: 'tue', label: '周二', short: '周二' },
  { key: 'wed', label: '周三', short: '周三' },
  { key: 'thu', label: '周四', short: '周四' },
  { key: 'fri', label: '周五', short: '周五' },
  { key: 'sat', label: '周六', short: '周六' },
  { key: 'sun', label: '周日', short: '周日' }
];

export const MEALS = [
  { key: 'breakfast', label: '早餐', icon: 'sunrise' },
  { key: 'lunch', label: '午餐', icon: 'sun' },
  { key: 'dinner', label: '晚餐', icon: 'moon' }
];

const STORAGE_KEY = 'menu-recipe-orders';

/* ── 工具 ────────────────────────────────────────────────────── */

function esc(str) {
  return String(str).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[ch]);
}

export function dayLabel(key) {
  return DAYS.find((d) => d.key === key)?.label || key;
}

export function mealLabel(key) {
  return MEALS.find((m) => m.key === key)?.label || key;
}

/** 菜品单价（用食谱热量近似"份量"，可按需替换为真实价格） */
export function dishKcal(id) {
  return RECIPES[id]?.nutrition?.calorie ?? 0;
}

/* ── 订单读写 ────────────────────────────────────────────────── */

/** 空订单结构 */
function emptyOrders() {
  const out = {};
  for (const d of DAYS) {
    out[d.key] = { breakfast: [], lunch: [], dinner: [] };
  }
  return out;
}

/**
 * 读取订单，并对历史数据做结构校验与修复：
 *   · 丢弃不存在的日期 / 餐次 / 菜品
 *   · 数量非法时回落为 1
 */
export function loadOrders() {
  const base = emptyOrders();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return base;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return base;

    for (const d of DAYS) {
      const src = parsed[d.key];
      if (!src || typeof src !== 'object') continue;
      for (const m of MEALS) {
        const list = src[m.key];
        if (!Array.isArray(list)) continue;
        base[d.key][m.key] = list
          .filter((it) => it && RECIPES[it.id])
          .map((it) => ({
            id: it.id,
            qty: Math.min(99, Math.max(1, Number(it.qty) || 1))
          }));
      }
    }
  } catch {
    /* 解析失败时用空订单，避免整个页面崩掉 */
    return emptyOrders();
  }
  return base;
}

export function saveOrders(orders) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(orders));
  } catch {
    /* 隐私模式下写入失败可忽略 */
  }
}

/* ── 订单操作（均为纯函数，返回新对象便于比较） ──────────────── */

/** 加入一道菜；同天同餐已存在则数量 +1 */
export function addDish(orders, dayKey, mealKey, dishId, qty = 1) {
  if (!RECIPES[dishId] || !orders[dayKey]?.[mealKey]) return orders;
  const next = structuredClone(orders);
  const list = next[dayKey][mealKey];
  const hit = list.find((it) => it.id === dishId);
  if (hit) {
    hit.qty = Math.min(99, hit.qty + qty);
  } else {
    list.push({ id: dishId, qty: Math.min(99, Math.max(1, qty)) });
  }
  return next;
}

/** 移除一道菜 */
export function removeDish(orders, dayKey, mealKey, dishId) {
  if (!orders[dayKey]?.[mealKey]) return orders;
  const next = structuredClone(orders);
  next[dayKey][mealKey] = next[dayKey][mealKey].filter((it) => it.id !== dishId);
  return next;
}

/** 调整数量，减到 0 即移除 */
export function setQty(orders, dayKey, mealKey, dishId, qty) {
  if (!orders[dayKey]?.[mealKey]) return orders;
  const next = structuredClone(orders);
  const list = next[dayKey][mealKey];
  const idx = list.findIndex((it) => it.id === dishId);
  if (idx < 0) return next;
  const q = Math.max(0, Math.min(99, qty));
  if (q === 0) list.splice(idx, 1);
  else list[idx].qty = q;
  return next;
}

/** 清空全部 */
export function clearOrders() {
  return emptyOrders();
}

/* ── 一键生成一整周菜单 ──────────────────────────────────────── */

/**
 * 从候选池挑一道菜，按优先级：
 *   1) 本周未用过，且不是上一餐刚出现的
 *   2) 本周未用过
 *   3) 池子里任意一道（避不开时才复用）
 */
function pickUnique(pool, used, exclude = new Set()) {
  if (!pool.length) return null;

  const fresh = pool.filter((id) => !used.has(id) && !exclude.has(id));
  const freshAny = pool.filter((id) => !used.has(id));
  const fallback = pool.filter((id) => !exclude.has(id));
  const source = fresh.length ? fresh : freshAny.length ? freshAny : fallback.length ? fallback : pool;

  const id = source[Math.floor(Math.random() * source.length)];
  used.add(id);
  return id;
}

function hasTag(id, tag) {
  return (RECIPES[id]?.tags || []).includes(tag);
}

/**
 * 生成一天的某一餐。
 * 规则（缺料时自动降级，保证一定凑出内容）：
 *   早餐：1 主食 + 1 蛋奶/清淡
 *   午餐：1 主食 + 1 荤菜 + 1 素菜
 *   晚餐：1 主食 +（1 荤菜或素菜）+ 1 汤羹
 */
function buildMeal(mealKey, pool, used, lastMealIds = new Set()) {
  const result = [];

  const take = (filter, exclude = new Set()) => {
    const candidates = pool.filter(
      (id) => filter(id) && !result.includes(id) && !exclude.has(id)
    );
    if (!candidates.length) return null;
    return pickUnique(candidates, used, exclude);
  };

  // 主食每天都会出现，容易雷同，最后再考虑"上一餐用过"的限制
  const staple = take((id) => hasTag(id, 'staple'), lastMealIds);
  if (staple) result.push(staple);

  if (mealKey === 'breakfast') {
    const other = take((id) => !hasTag(id, 'staple'));
    if (other) result.push(other);
  } else if (mealKey === 'lunch') {
    const meat = take((id) => hasTag(id, 'meat'));
    if (meat) result.push(meat);
    const veg = take((id) => hasTag(id, 'veg'));
    if (veg) result.push(veg);
  } else {
    const main = take((id) => hasTag(id, 'meat') || hasTag(id, 'veg'));
    if (main) result.push(main);
    const soup = take((id) => hasTag(id, 'soup'));
    if (soup) result.push(soup);
  }

  // 兜底：规则没凑出东西时随机补一道
  if (!result.length) {
    const any = take(() => true);
    if (any) result.push(any);
  }
  return result;
}

/**
 * 生成完整一周菜单（覆盖原有订单）。
 *
 * 去重策略：优先选本周没用过的菜；候选池取尽后允许复用，
 * 但尽量避开"上一餐刚用过"的，避免连续重复。
 */
export function generateWeek(pool) {
  const next = emptyOrders();
  const used = new Set();
  let lastMealIds = new Set();

  for (const d of DAYS) {
    for (const m of MEALS) {
      const ids = buildMeal(m.key, pool[m.key] || [], used, lastMealIds);
      next[d.key][m.key] = ids.map((id) => ({ id, qty: 1 }));
      lastMealIds = new Set(ids);
    }
  }
  return next;
}

/* ── 统计 ────────────────────────────────────────────────────── */

/** 全部已点条目数（按条目算，不按数量） */
export function countItems(orders) {
  let n = 0;
  for (const d of DAYS) {
    for (const m of MEALS) {
      n += orders[d.key]?.[m.key]?.length || 0;
    }
  }
  return n;
}

/** 总热量（数量 × 单份热量） */
export function totalKcal(orders) {
  let sum = 0;
  for (const d of DAYS) {
    for (const m of MEALS) {
      for (const it of orders[d.key]?.[m.key] || []) {
        sum += dishKcal(it.id) * it.qty;
      }
    }
  }
  return sum;
}

/** 某天的热量合计 */
export function dayKcal(orders, dayKey) {
  let sum = 0;
  for (const m of MEALS) {
    for (const it of orders[dayKey]?.[m.key] || []) {
      sum += dishKcal(it.id) * it.qty;
    }
  }
  return sum;
}

/** 某天已点的菜名列表（去重、含数量后缀） */
export function dayDishNames(orders, dayKey) {
  const names = [];
  for (const m of MEALS) {
    for (const it of orders[dayKey]?.[m.key] || []) {
      const name = RECIPES[it.id]?.name || it.id;
      names.push(it.qty > 1 ? `${name}×${it.qty}` : name);
    }
  }
  return names;
}

/** 某道菜本周是否已点（用于橱窗高亮） */
export function isDishOrdered(orders, dishId) {
  for (const d of DAYS) {
    for (const m of MEALS) {
      if ((orders[d.key]?.[m.key] || []).some((it) => it.id === dishId)) return true;
    }
  }
  return false;
}

/* ── 渲染片段 ────────────────────────────────────────────────── */

/** 分类/筛选用的日期下拉选项 */
export function dayOptionsHtml(selectedDay) {
  return DAYS.map(
    (d) =>
      `<option value="${d.key}" ${d.key === selectedDay ? 'selected' : ''}>${d.label}</option>`
  ).join('');
}

/** 餐次下拉选项 */
export function mealOptionsHtml(selectedMeal) {
  return MEALS.map(
    (m) =>
      `<option value="${m.key}" ${m.key === selectedMeal ? 'selected' : ''}>${m.label}</option>`
  ).join('');
}

/** 菜品橱窗卡片 */
/**
 * 生成橱窗菜品卡。
 *
 * @param {string} dishId
 * @param {string} selectedDay
 * @param {string} selectedMeal
 * @param {object} orders
 * @param {object} [recipeOverride] 后端返回的菜谱对象。
 *   传入时优先使用它，否则回落到静态 RECIPES。
 *   用户自建菜谱只存在于服务端，静态表里没有，必须靠这个参数传入。
 */
export function catalogCardHtml(dishId, selectedDay, selectedMeal, orders, recipeOverride) {
  const r = recipeOverride || RECIPES[dishId];
  if (!r) return '';
  const ic = getDishIcon(dishId);
  const ordered = isDishOrdered(orders, dishId);
  // 后端摘要结构用 calorie，静态结构用 nutrition.calorie，两者都要兼容
  const kcal = r.nutrition?.calorie ?? r.calorie ?? 0;
  const tags = (r.tags || [])
    .filter((t) => TAG_META[t])
    .map((t) => `<span class="tag tag--${TAG_META[t].color}">${TAG_META[t].label}</span>`)
    .join('');

  return `
    <article class="dish-card ${ordered ? 'is-ordered' : ''}">
      <div class="dish-card__head" data-dish="${esc(dishId)}" role="button" tabindex="0">
        <span class="dish-card__thumb" style="--ic-fill:${ic.fg};--ic-stroke:#fff;background:${ic.bg}">
          <span class="dish-card__thumb-inner">${ic.svg}</span>
        </span>
        <span class="dish-card__info">
          <span class="dish-card__name">${esc(r.name)}</span>
          <span class="dish-card__meta">
            <span class="meta-ico">${UI_ICONS.clock}<i>${r.time} 分钟</i></span>
            <span class="meta-ico meta-ico--flame">${UI_ICONS.flame}<i>${kcal} 千卡</i></span>
            <span class="meta-ico">${esc(r.difficulty || '')}</span>
          </span>
          <span class="dish-card__tags">${tags}</span>
        </span>
      </div>
      <div class="dish-card__actions">
        <select class="control control--select dish-card__select"
                id="order-target-${esc(dishId)}"
                name="order-target-${esc(dishId)}"
                data-order-target="${esc(dishId)}"
                aria-label="选择要加入的日期与餐次">${(() => {
    const opts = [];
    for (const d of DAYS) {
      opts.push(`<optgroup label="${d.label}">`);
      for (const m of MEALS) {
        const sel = d.key === selectedDay && m.key === selectedMeal ? 'selected' : '';
        opts.push(`<option value="${d.key}|${m.key}" ${sel}>${d.label} ${m.label}</option>`);
      }
      opts.push('</optgroup>');
    }
    return opts.join('');
  })()}</select>
        <button class="btn btn--add" data-add="${esc(dishId)}" type="button">
          <span class="btn__ico" data-icon="plus" aria-hidden="true"></span>
          加入
        </button>
      </div>
    </article>`;
}

/** 点餐篮：按星期分组 */
export function basketHtml(orders) {
  const groups = DAYS.map((d) => {
    const entries = [];
    for (const m of MEALS) {
      for (const it of orders[d.key]?.[m.key] || []) {
        entries.push({ ...it, meal: m.key, day: d.key });
      }
    }
    if (!entries.length) return '';
    return `
      <div class="basket-day">
        <div class="basket-day__head">
          <span class="basket-day__name">${d.label}</span>
          <span class="basket-day__date">${entries.length} 项</span>
          <span class="basket-day__sum">${dayKcal(orders, d.key)} 千卡</span>
        </div>
        ${entries.map((it) => basketItemHtml(it, orders)).join('')}
      </div>`;
  }).join('');

  if (!groups.trim()) {
    return `
      <div class="basket-empty">
        <span class="basket-empty__ico">${UI_ICONS.cart}</span>
        <p class="basket-empty__text">本周还没有点菜</p>
        <p class="basket-empty__hint">在左侧选好日期和餐次，点「加入」即可</p>
      </div>`;
  }
  return groups;
}

function basketItemHtml(item, orders) {
  const r = RECIPES[item.id];
  const ic = getDishIcon(item.id);
  return `
    <div class="basket-item">
      <span class="basket-item__thumb" style="--ic-fill:${ic.fg};--ic-stroke:#fff;background:${ic.bg}">
        <span class="basket-item__thumb-inner">${ic.svg}</span>
      </span>
      <span class="basket-item__body">
        <span class="basket-item__name">${esc(r.name)}</span>
        <span class="basket-item__meta">${mealLabel(item.meal)} · ${r.nutrition.calorie * item.qty} 千卡</span>
      </span>
      <span class="stepper">
        <button class="stepper__btn" type="button"
                data-qty="-1" data-day="${item.day}" data-meal="${item.meal}" data-id="${esc(item.id)}"
                aria-label="减少 ${esc(r.name)} 数量">${UI_ICONS.minus}</button>
        <span class="stepper__val">${item.qty}</span>
        <button class="stepper__btn" type="button"
                data-qty="1" data-day="${item.day}" data-meal="${item.meal}" data-id="${esc(item.id)}"
                aria-label="增加 ${esc(r.name)} 数量">${UI_ICONS.plus}</button>
      </span>
      <button class="basket-item__del" type="button"
              data-del data-day="${item.day}" data-meal="${item.meal}" data-id="${esc(item.id)}"
              aria-label="移除 ${esc(r.name)}">${UI_ICONS.close}</button>
    </div>`;
}

/** 确认弹窗里的按天摘要 */
export function confirmSummaryHtml(orders) {
  return DAYS.map((d) => {
    const names = dayDishNames(orders, d.key);
    const empty = names.length === 0;
    return `
      <div class="confirm-row ${empty ? 'is-empty' : ''}">
        <span class="confirm-row__day">${d.label}</span>
        <span class="confirm-row__dishes">${empty ? '未安排' : esc(names.join('、'))}</span>
        <span class="confirm-row__kcal">${empty ? '—' : dayKcal(orders, d.key) + ' 千卡'}</span>
      </div>`;
  }).join('');
}

export { starHtml };
