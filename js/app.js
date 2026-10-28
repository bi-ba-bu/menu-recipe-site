/**
 * app.js — 菜单与食谱页面交互逻辑
 *
 * 模块：
 *   1. 状态与工具
 *   2. 路由（hash 驱动，侧栏与 TabBar 共用）
 *   3. 渲染：一周菜单 / 食谱详情 / 营养概览 / 收藏
 *   4. 交互：星期切换、收藏、搜索、主题、抽屉
 *
 * 无构建、无框架，直接用 ES Module 加载。
 */

import {
  WEEK_DAYS,
  WEEK_META,
  GENERATE_POOL,
  RECIPES,
  NUTRITION_TARGET,
  TODAY_OVERVIEW,
  TAG_META
} from './data.js';
import { getDishIcon, UI_ICONS, starHtml } from './icons.js';
import * as Order from './order.js';
import * as Api from './api.js';
import * as Appearance from './appearance.js';
import * as CuteSkin from './skins/cute-skin.js';

/* ── §1 状态 ─────────────────────────────────────────────────── */

/** 今天在示例数据里对应周四（10/23），与运行环境无关，保证演示稳定 */
const TODAY_INDEX = 3;

const ROUTES = ['menu', 'order', 'recipe', 'recipes', 'nutrition', 'favorite', 'family'];

const state = {
  route: 'menu',
  dayIndex: TODAY_INDEX,
  currentRecipeId: null,
  favorites: new Set(loadFavorites()),
  // 点餐
  orders: Order.loadOrders(),
  orderDay: Order.DAYS[TODAY_INDEX].key,
  orderMeal: 'lunch',
  orderFilter: 'all',
  orderQuery: '',
  // 点餐橱窗数据缓存（来自后端 /api/dishes）
  catalog: null,
  catalogLoaded: false,
  basketOpen: false,
  // 后端连接状态：true 表示降级到 localStorage
  offline: false,
  // 后端返回的营养统计（点餐变更后刷新）
  nutrition: null,
  // 当前登录用户
  user: null,
  // 家庭
  families: null,
  familyDetail: null,
  // —— 我的菜谱（维护中心）——
  // null 表示还没拉过；[] 表示拉过但没有数据
  recipeItems: null,
  recipesLoading: false,
  recipesError: '',
  // 审核员身份：null=未探测，true/false=已探测
  isReviewer: null,
  pendingRecipes: null,
  // 当前标签页：mine | pending | public
  recipesTab: 'mine',
  // 菜谱列表最近一次加载的时间戳，用于避免重复拉取
  recipesLoadedAt: 0
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function loadFavorites() {
  try {
    const raw = localStorage.getItem('menu-recipe-favorites');
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr.filter((id) => RECIPES[id]) : [];
  } catch {
    return [];
  }
}

function saveFavorites() {
  try {
    localStorage.setItem('menu-recipe-favorites', JSON.stringify([...state.favorites]));
  } catch {
    /* 隐私模式下写入失败可忽略 */
  }
}

/** HTML 转义，防止数据里的尖括号破坏结构 */
function esc(str) {
  return String(str).replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[ch]);
}

function tagsHtml(tags = []) {
  return tags
    .filter((t) => TAG_META[t])
    .map((t) => `<span class="tag tag--${TAG_META[t].color}">${TAG_META[t].label}</span>`)
    .join('');
}

/** 简单 Toast */
let toastTimer = null;
function toast(msg) {
  const el = $('#toast');
  el.textContent = msg;
  el.classList.add('is-show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('is-show'), 1800);
}

/* ── §2 路由 ─────────────────────────────────────────────────── */

const PAGE_META = {
  menu: { title: '一周菜单', sub: `${WEEK_META.range} · ${WEEK_META.week}` },
  order: { title: '点餐', sub: '选菜品、挑日期，加入本周菜单' },
  recipe: { title: '食谱详情', sub: '食材、步骤与营养拆解' },
  recipes: { title: '我的菜谱', sub: '维护自己的菜谱，提交审核后即可公开' },
  nutrition: { title: '营养概览', sub: '本周摄入趋势与今日完成度' },
  favorite: { title: '我的收藏', sub: `已收藏 ${state.favorites.size} 道菜` },
  family: { title: '家庭管理', sub: '创建家庭、邀请成员、切换家庭' }
};

function currentRecipe() {
  return state.currentRecipeId ? RECIPES[state.currentRecipeId] : null;
}

function syncRouteUI() {
  const { route } = state;

  // 标记当前路由，供 CSS 做按页显隐（如点餐篮只在点餐页出现）
  document.body.dataset.route = route;

  // 视图切换
  $$('.view').forEach((view) => {
    view.classList.toggle('is-active', view.id === `view-${route}`);
  });

  // 导航高亮（侧栏 + TabBar 同步）
  $$('[data-route]').forEach((link) => {
    const active = link.dataset.route === route;
    link.classList.toggle('is-active', active);
    if (active) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });

  // 标题
  const recipe = currentRecipe();
  const meta = PAGE_META[route] || PAGE_META.menu;
  $('#pageTitle').textContent = route === 'recipe' && recipe ? recipe.name : meta.title;
  $('#pageSub').textContent = route === 'recipe' && recipe ? recipe.subtitle : meta.sub;

  document.title = `${route === 'recipe' && recipe ? recipe.name : meta.title} · 今日食堂`;

  // 浏览器返回时回到顶部更符合阅读习惯
  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
}

function go(route, recipeId) {
  if (route === 'recipe') {
    // 没指定食谱时，默认展示今日午餐的第一道菜
    state.currentRecipeId = recipeId || state.currentRecipeId || defaultRecipeId();
  }
  if (location.hash.slice(1) === route) {
    state.route = route;
    syncRouteUI();
  } else {
    location.hash = route;
  }
}

/** 默认食谱：今日午餐第一道菜；当天没安排则取全部菜品的第一道 */
function defaultRecipeId() {
  const todayKey = Order.DAYS[TODAY_INDEX].key;
  for (const m of ['lunch', 'breakfast', 'dinner']) {
    const hit = state.orders[todayKey]?.[m]?.[0];
    if (hit && RECIPES[hit.id]) return hit.id;
  }
  for (const d of Order.DAYS) {
    for (const m of Order.MEALS) {
      const hit = state.orders[d.key]?.[m.key]?.[0];
      if (hit && RECIPES[hit.id]) return hit.id;
    }
  }
  return Object.keys(RECIPES)[0];
}

window.addEventListener('hashchange', () => {
  const route = location.hash.slice(1).split('/')[0] || 'menu';
  const valid = ROUTES.includes(route) ? route : 'menu';
  state.route = valid;
  if (valid === 'recipe' && !state.currentRecipeId) state.currentRecipeId = defaultRecipeId();
  renderRoute(valid);
  syncRouteUI();
});

/* ── §3 渲染 ─────────────────────────────────────────────────── */

function renderRoute(route) {
  if (route === 'menu') renderMenu();
  if (route === 'order') renderOrder();
  if (route === 'recipe') renderRecipe();
  if (route === 'recipes') renderRecipes();
  if (route === 'nutrition') loadNutrition();
  if (route === 'favorite') renderFavorites();
  if (route === 'family') loadFamilyPage();
}

/**
 * 加载营养页数据。
 *
 * 在线时以后端为准（后端按订单实时计算），
 * 离线时由本地订单推导，保证两边都能实时反映点餐结果。
 */
async function loadNutrition() {
  if (!state.offline) {
    try {
      state.nutrition = await Api.getNutrition();
    } catch (err) {
      if (err instanceof Api.ApiUnavailable) enterOfflineMode();
      state.nutrition = null;
    }
  } else {
    state.nutrition = null;
  }
  renderNutrition();
}

/* —— 3.1 一周菜单 —— */

/**
 * 把点餐订单转换成菜单视图需要的菜品结构。
 * 菜单本身不再硬编码，完全由 state.orders 推导，因此：
 *   · 首次打开 → 全空
 *   · 点餐 / 一键生成 / 删除 → 菜单随之变化
 */
function menuDishes(dayKey, mealKey) {
  const items = state.orders[dayKey]?.[mealKey] || [];
  return items
    .map((it) => {
      const r = RECIPES[it.id];
      if (!r) return null;
      return {
        id: it.id,
        name: it.qty > 1 ? `${r.name} ×${it.qty}` : r.name,
        tags: r.tags || [],
        kcal: r.nutrition.calorie * it.qty,
        time: r.time,
        spicy: (r.tags || []).includes('spicy'),
        qty: it.qty,
        mealKey
      };
    })
    .filter(Boolean);
}

/** 整周是否还没有任何安排 */
function isWeekEmpty() {
  return Order.countItems(state.orders) === 0;
}

/** 某天是否还没有任何安排 */
function isDayEmpty(dayKey) {
  return Order.MEALS.every((m) => (state.orders[dayKey]?.[m.key] || []).length === 0);
}

function renderMenu() {
  // 星期 tab
  $('#todayLabel').textContent = Order.DAYS[TODAY_INDEX].label;

  $('#dayTabs').innerHTML = Order.DAYS.map((d, i) => {
    const count = Order.MEALS.reduce(
      (n, m) => n + (state.orders[d.key]?.[m.key] || []).length,
      0
    );
    return `
      <button class="day-tab ${i === state.dayIndex ? 'is-active' : ''} ${i === TODAY_INDEX ? 'is-today' : ''}"
              role="tab"
              aria-selected="${i === state.dayIndex}"
              data-day="${i}">
        <span class="day-tab__label">${esc(d.label)}</span>
        <span class="day-tab__date">${esc(WEEK_DAYS[i].date)}</span>
        ${count ? `<span class="day-tab__dot" aria-label="${count} 道菜"></span>` : ''}
      </button>`;
  }).join('');

  // 整周为空时，显示引导性空态 + 一键生成入口
  if (isWeekEmpty()) {
    $('#mealList').innerHTML = emptyWeekHtml();
    renderTodayMetrics();
    return;
  }

  const dayKey = Order.DAYS[state.dayIndex].key;
  const mealMeta = {
    breakfast: { icon: UI_ICONS.sunrise, name: '早餐' },
    lunch: { icon: UI_ICONS.sun, name: '午餐' },
    dinner: { icon: UI_ICONS.moon, name: '晚餐' }
  };

  $('#mealList').innerHTML = Order.MEALS.map(({ key }) => {
    const meta = mealMeta[key];
    const dishes = menuDishes(dayKey, key);
    const total = dishes.reduce((sum, d) => sum + d.kcal, 0);

    return `
      <article class="meal-block ${dishes.length ? '' : 'is-empty'}">
        <div class="meal-block__head">
          <span class="meal-block__icon" aria-hidden="true">${meta.icon}</span>
          <h3 class="meal-block__name">${meta.name}</h3>
          <span class="meal-block__sum">${
            dishes.length ? `${dishes.length} 道 · ${total} 千卡` : '未安排'
          }</span>
        </div>
        <div class="dish-grid">
          ${dishes.length ? dishes.map(dishHtml).join('') : emptyMealHtml()}
        </div>
      </article>`;
  }).join('');

  renderTodayMetrics();
}

/** 整周空态 */
function emptyWeekHtml() {
  return `
    <div class="empty-week">
      <span class="empty-week__ico">${UI_ICONS.calendar}</span>
      <p class="empty-week__title">本周还没有安排菜单</p>
      <p class="empty-week__hint">可以一键生成为期一周的搭配，或去「点餐」页自己挑</p>
      <div class="empty-week__actions">
        <button class="btn btn--primary" type="button" data-generate>
          <span class="btn__ico" aria-hidden="true">${UI_ICONS.spark}</span>
          一键生成本周菜单
        </button>
        <a class="btn btn--ghost" href="#order" data-route="order">去点餐</a>
      </div>
    </div>`;
}

function emptyMealHtml() {
  return `<p class="empty__hint meal-empty">这一餐还没安排</p>`;
}

/** 今日概览数字：取当天已排菜品的热量与蛋白/纤维估算 */
function renderTodayMetrics() {
  const dayKey = Order.DAYS[TODAY_INDEX].key;
  let kcal = 0;
  let protein = 0;
  let fiber = 0;
  for (const m of Order.MEALS) {
    for (const it of state.orders[dayKey]?.[m.key] || []) {
      const n = RECIPES[it.id]?.nutrition;
      if (!n) continue;
      kcal += n.calorie * it.qty;
      protein += n.protein * it.qty;
      fiber += n.fiber * it.qty;
    }
  }
  animateNumber($('#mCalorie'), Math.round(kcal));
  animateNumber($('#mProtein'), Math.round(protein));
  animateNumber($('#mFiber'), Math.round(fiber));
}

/**
 * 一周菜单的菜品展示。
 *
 * 菜单页不再做关键词过滤：搜索已收敛到「点餐」页的菜品橱窗，
 * 菜单只展示本周实际排了什么，避免"搜了词却看到残缺菜单"的困惑。
 */
function dishHtml(dish) {
  const recipe = RECIPES[dish.id];
  const isFav = state.favorites.has(dish.id);
  const hasDetail = Boolean(recipe);
  const openAttr = hasDetail ? `data-dish="${esc(dish.id)}" role="button" tabindex="0"` : '';
  const ic = getDishIcon(dish.id);
  const dayKey = Order.DAYS[state.dayIndex].key;

  // 卡片主体可点击（打开食谱），右侧是收藏与"从菜单移除"
  return `
    <div class="dish">
      <div class="dish__main" ${openAttr}>
        <span class="dish__thumb" style="--ic-fill:${ic.fg};--ic-stroke:#fff;background:${ic.bg}">
          <span class="dish__thumb-inner">${ic.svg}</span>
        </span>
        <span class="dish__body">
          <span class="dish__name">${esc(dish.name)}</span>
          <span class="dish__meta">
            <span class="meta-ico">${UI_ICONS.clock}<i>${dish.time} 分钟</i></span>
            <span class="meta-ico meta-ico--flame">${UI_ICONS.flame}<i>${dish.kcal} 千卡</i></span>
            ${dish.spicy ? `<span class="meta-ico meta-ico--spicy">${UI_ICONS.chili}<i>微辣</i></span>` : ''}
          </span>
          <span class="dish__tags">${tagsHtml(dish.tags)}</span>
        </span>
      </div>
      <button class="dish__fav ${isFav ? 'is-fav' : ''}"
              data-fav="${esc(dish.id)}"
              aria-label="${isFav ? '取消收藏' : '收藏'} ${esc(dish.name)}"
              aria-pressed="${isFav}">${starHtml(isFav, '19px')}</button>
      <button class="dish__del" type="button"
              data-menu-del="${esc(dish.id)}" data-menu-day="${dayKey}" data-menu-meal="${esc(dish.mealKey || '')}"
              aria-label="从菜单移除 ${esc(dish.name)}" title="从菜单移除">
        ${UI_ICONS.trash}
      </button>
    </div>`;
}

/* —— 3.2 点餐 —— */

const ORDER_FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'meat', label: '荤菜' },
  { key: 'veg', label: '素菜' },
  { key: 'soup', label: '汤羹' },
  { key: 'staple', label: '主食' },
  { key: 'light', label: '清淡' }
];

/**
 * 橱窗里展示的菜品。
 *
 * 数据来源优先级：
 *   1. state.catalog —— 后端 /api/dishes 返回的「当前用户可见」菜品
 *      （含公共菜谱 + 自己的个人菜谱，已过滤下架的）
 *   2. RECIPES       —— 后端不可用时的静态兜底
 *
 * 之所以必须走后端：用户自己新建的菜谱存在服务端，
 * 静态 data.js 里没有，只用本地数据会导致"建了菜却搜不到"。
 */
function allDishes() {
  if (Array.isArray(state.catalog) && state.catalog.length) {
    return state.catalog;
  }
  return Object.keys(RECIPES).map((id) => ({ id, recipe: RECIPES[id] }));
}

/** 从后端拉取可见菜品，供点餐橱窗使用 */
async function loadCatalog() {
  try {
    // 拉全量（不带 tag/q），分类与搜索都在前端做，避免每次输入都请求
    const data = await Api.listDishes();
    state.catalog = (data.items || []).map((item) => ({
      id: item.id,
      recipe: {
        ...item,
        // 列表接口只给摘要字段，补齐渲染需要的最小结构
        ingredients: item.ingredients || [],
        tags: item.tags || [],
        nutrition: { calorie: item.calorie || 0 }
      }
    }));
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      state.catalog = null;
    }
  }
}

function filterCatalog(dishes) {
  const q = state.orderQuery.trim().toLowerCase();
  return dishes.filter(({ recipe }) => {
    if (state.orderFilter !== 'all' && !(recipe.tags || []).includes(state.orderFilter)) {
      return false;
    }
    if (!q) return true;
    const haystack = [
      recipe.name,
      recipe.subtitle || '',
      (recipe.ingredients || []).map((i) => i.name).join(' ')
    ]
      .join(' ')
      .toLowerCase();
    return haystack.includes(q);
  });
}

/**
 * 渲染点餐页。
 *
 * 首次进入（或菜谱有变更）时先拉一次可见菜品，再渲染，
 * 保证新建的个人菜谱能立刻出现在橱窗里。
 */
async function renderOrder() {
  if (!state.catalogLoaded && !state.offline) {
    await loadCatalog();
    state.catalogLoaded = true;
  }
  paintOrder();
}

/** 纯绘制：不发起请求，供筛选/搜索等高频操作复用 */
function paintOrder() {
  const dishes = allDishes();

  // 操作条左侧：当前生效的筛选条件（分类 + 关键词）
  renderOrderFilterLabel(dishes.length);

  // 分类胶囊（带数量）
  $('#dishChips').innerHTML = ORDER_FILTERS.map((f) => {
    const count =
      f.key === 'all'
        ? dishes.length
        : dishes.filter(({ recipe }) => (recipe.tags || []).includes(f.key)).length;
    return `
      <button class="chip ${state.orderFilter === f.key ? 'is-active' : ''}"
              role="tab" aria-selected="${state.orderFilter === f.key}"
              data-filter="${f.key}">
        ${f.label}<span class="chip__count">${count}</span>
      </button>`;
  }).join('');

  // 菜品橱窗
  const list = filterCatalog(dishes);
  $('#orderCatalog').innerHTML = list.length
    ? list
        .map(({ id, recipe }) =>
          Order.catalogCardHtml(id, state.orderDay, state.orderMeal, state.orders, recipe)
        )
        .join('')
    : `<div class="empty">
         <span class="empty__text">没有匹配的菜品</span>
         <span class="empty__hint">试试换个分类或关键词</span>
         ${state.orderQuery ? '<button class="btn btn--ghost" type="button" data-clear-catalog-search>清空搜索</button>' : ''}
       </div>`;

  // 搜索框内容同步（从其他页面回来时保持用户输入）
  const input = $('#catalogSearch');
  if (input && input.value !== state.orderQuery) input.value = state.orderQuery;
  syncCatalogSearchClear();

  renderBasket();
}

/**
 * 点餐页操作条左侧的筛选描述。
 * 让用户一眼知道"现在看到的这些菜是被什么条件筛出来的"，
 * 避免搜了词、切了分类却忘了，以为菜变少了。
 */
function renderOrderFilterLabel(total) {
  const el = $('#orderFilterLabel');
  if (!el) return;

  const filterLabel = ORDER_FILTERS.find((f) => f.key === state.orderFilter)?.label || '全部';
  const q = state.orderQuery.trim();
  const parts = [`${filterLabel}菜品`, `共 ${total} 道`];
  if (q) parts.push(`关键词「${q}」`);
  el.textContent = parts.join(' · ');
}

/** 只刷新点餐篮与统计（点菜后无需整页重绘） */
function renderBasket() {
  const items = Order.countItems(state.orders);
  const kcal = Order.totalKcal(state.orders);

  $('#basketBody').innerHTML = Order.basketHtml(state.orders);
  $('#basketSummary').textContent = `${items} 道 · ${kcal} 千卡`;
  $('#clearOrders').disabled = items === 0;
  $('#confirmOrders').disabled = items === 0;

  // 侧栏与 TabBar 徽标
  const navBadge = $('#orderCount');
  navBadge.hidden = items === 0;
  navBadge.textContent = items;

  const tabBadge = $('#tabOrderBadge');
  tabBadge.hidden = items === 0;
  tabBadge.textContent = items;

  // App 端悬浮操作条
  const bar = $('#orderBar');
  if (bar) {
    bar.classList.toggle('is-show', items > 0 && state.route === 'order');
    const countEl = $('#orderBarCount');
    const sumEl = $('#orderBarSum');
    if (countEl) countEl.textContent = `已点 ${items} 道`;
    if (sumEl) sumEl.textContent = `合计 ${kcal} 千卡`;
  }
  document.querySelector('#view-order')?.classList.toggle('is-bar', items > 0);
}

/**
 * 统一的订单变更入口。
 *
 * 优先调用后端；后端不可用（未启动 / 网络异常）时，
 * 自动降级为本地 localStorage 计算，保证页面仍可离线使用。
 *
 * @param {Function} remote  调用后端的方法，返回 Promise
 * @param {Function} local   本地降级：接收/返回 orders
 */
async function mutateOrders(remote, local) {
  if (state.offline) {
    state.orders = local(state.orders);
    Order.saveOrders(state.orders);
    return;
  }
  try {
    await remote();
    await syncOrdersFromServer();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      // 后端掉线：切到离线模式，本次用本地逻辑兜底
      enterOfflineMode();
      state.orders = local(state.orders);
      Order.saveOrders(state.orders);
    } else {
      showError(err.message);
    }
  }
}

/** 从后端拉取最新订单并刷新界面 */
async function syncOrdersFromServer() {
  try {
    const week = await Api.getWeekMenu();
    state.orders = weekToLocalOrders(week);
    Order.saveOrders(state.orders);
    refreshOrderViews();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) enterOfflineMode();
    else showError(err.message);
  }
}

/**
 * 后端返回的周视图 → 前端订单结构。
 * 后端按天返回展开后的菜品，这里收回成 {day:{meal:[{id,qty}]}}。
 */
function weekToLocalOrders(week) {
  const orders = {};
  for (const day of Order.DAYS) {
    orders[day.key] = { breakfast: [], lunch: [], dinner: [] };
  }
  for (const day of week.days || []) {
    for (const mealKey of ['breakfast', 'lunch', 'dinner']) {
      const items = day.meals?.[mealKey]?.items || [];
      orders[day.key][mealKey] = items.map((it) => ({ id: it.id, qty: it.qty }));
    }
  }
  return orders;
}

/** 刷新所有依赖订单的视图 */
function refreshOrderViews() {
  renderBasket();
  if (state.route === 'menu') renderMenu();
  if (state.route === 'order') renderOrder();
  if (state.route === 'nutrition') {
    // 营养页依赖后端统计，需要拉取最新值
    if (!state.offline) {
      Api.getNutrition()
        .then((data) => {
          state.nutrition = data;
          renderNutrition();
        })
        .catch(() => {
          state.nutrition = null;
          renderNutrition();
        });
    } else {
      renderNutrition();
    }
  }
}

/** 进入离线模式（只提示一次） */
function enterOfflineMode() {
  if (state.offline) return;
  state.offline = true;
  setConnectionBadge(false);
  toast('后端未连接，已切换到本地模式');
}

function showError(message) {
  toast(message || '操作失败');
}

/** 加入一道菜到当前选定的日期 / 餐次 */
function addToOrder(dishId, dayKey, mealKey) {
  if (!RECIPES[dishId]) return;
  mutateOrders(
    () => Api.addItem(dishId, dayKey, mealKey, 1),
    (orders) => Order.addDish(orders, dayKey, mealKey, dishId, 1)
  );
  setTimeout(() => {
    toast(`已加入 ${Order.dayLabel(dayKey)} ${Order.mealLabel(mealKey)}：${RECIPES[dishId].name}`);
  }, 0);
}

/** 修改数量 / 移除 */
function changeQty(dayKey, mealKey, dishId, delta) {
  const list = state.orders[dayKey]?.[mealKey] || [];
  const current = list.find((it) => it.id === dishId)?.qty ?? 0;
  const next = current + delta;
  mutateOrders(
    () => (next <= 0 ? Api.removeItem(dishId, dayKey, mealKey) : Api.setQuantity(dishId, dayKey, mealKey, next)),
    (orders) => Order.setQty(orders, dayKey, mealKey, dishId, next)
  );
}

function removeFromOrder(dayKey, mealKey, dishId) {
  mutateOrders(
    () => Api.removeItem(dishId, dayKey, mealKey),
    (orders) => Order.removeDish(orders, dayKey, mealKey, dishId)
  );
}

/** 一键生成整周菜单（覆盖已有安排） */
async function generateWeekMenu() {
  const hasContent = Order.countItems(state.orders) > 0;
  if (hasContent) {
    const ok = await dialog.confirm({
      title: '覆盖本周安排？',
      message: '一键生成会重新安排整周菜单，当前已有的安排将被替换。',
      okText: '生成'
    });
    if (!ok) return;
  }

  mutateOrders(
    () => Api.generateWeek(),
    (orders) => Order.generateWeek(GENERATE_POOL)
  );
  setTimeout(() => toast('已生成本周菜单'), 0);
}

/* —— 3.3 食谱详情 —— */

/**
 * 渲染食谱详情。
 *
 * 数据优先从后端取：用户自建菜谱只存在于服务端，
 * 静态 RECIPES 里没有，直接查静态表会显示"还在整理中"。
 */
async function renderRecipe() {
  const id = state.currentRecipeId || defaultRecipeId();
  state.currentRecipeId = id;
  const host = $('#recipeDetail');

  let r = null;
  if (!state.offline) {
    try {
      r = await Api.getDish(id);
    } catch (err) {
      // 后端不可用或该菜谱对当前用户不可见，回落到静态数据
      if (!(err instanceof Api.ApiUnavailable) && err.status !== 404) {
        showError(err.message);
      }
      r = RECIPES[id] || null;
    }
  } else {
    r = RECIPES[id] || null;
  }

  // 统一结构：后端详情的热量可能来自 calorie 或 nutrition.calorie
  if (r && !r.nutrition) {
    r = { ...r, nutrition: { calorie: r.calorie || 0 } };
  }

  if (!r) {
    host.innerHTML = `
      <div class="empty">
        <span class="empty__icon" aria-hidden="true">🍽</span>
        <p class="empty__text">这个食谱还在整理中</p>
        <p class="empty__hint">可以先看看一周菜单里的其他菜品</p>
      </div>`;
    return;
  }

  const isFav = state.favorites.has(id);
  const n = r.nutrition;
  const heroIc = getDishIcon(id);

  const nutriItems = [
    ['calorie', '千卡', '热量'],
    ['protein', 'g', '蛋白质'],
    ['fat', 'g', '脂肪'],
    ['carb', 'g', '碳水'],
    ['fiber', 'g', '纤维']
  ]
    .map(
      ([key, unit, name]) => `
      <div class="nutri-item">
        <span class="nutri-item__val">${n[key]}</span>
        <span class="nutri-item__unit">${unit}</span>
        <span class="nutri-item__name">${name}</span>
      </div>`
    )
    .join('');

  const ingHtml = r.ingredients
    .map(
      (ing) => `
      <div class="ing ${ing.main ? 'is-main' : ''}">
        <span class="ing__dot" aria-hidden="true"></span>
        <span class="ing__name">${esc(ing.name)}</span>
        <span class="ing__amount">${esc(ing.amount)}</span>
      </div>`
    )
    .join('');

  const stepsHtml = r.steps
    .map(
      (s, i) => `
      <div class="step">
        <span class="step__idx" aria-hidden="true">${i + 1}</span>
        <div class="step__body">
          <p class="step__title">
            ${esc(s.title)}
            <span class="step__time">${s.minutes} 分钟</span>
          </p>
          <p class="step__desc">${esc(s.desc)}</p>
        </div>
      </div>`
    )
    .join('');

  host.innerHTML = `
    <div class="recipe-layout">
      <div class="recipe-layout__main">
        <div class="recipe-hero" style="background:${r.cover};--ic-fill:#fff;--ic-stroke:${heroIc.fg}">
          <span class="recipe-hero__art">${heroIc.svg}</span>
          <button class="recipe-hero__fav ${isFav ? 'is-fav' : ''}"
                  data-fav="${esc(id)}"
                  aria-label="${isFav ? '取消收藏' : '收藏'}这道菜"
                  aria-pressed="${isFav}">${starHtml(isFav, '21px')}</button>
        </div>

        <div class="recipe-head">
          <h2>${esc(r.name)}</h2>
          <p class="recipe-head__sub">${esc(r.subtitle)}</p>
          <p class="recipe-head__desc">${esc(r.desc)}</p>
          <div class="dish__tags" style="margin-top:10px">${tagsHtml(r.tags)}</div>
        </div>

        <div class="facts">
          <div class="fact">
            <div class="fact__value">${r.time}</div>
            <div class="fact__label">分钟</div>
          </div>
          <div class="fact">
            <div class="fact__value">${esc(r.difficulty)}</div>
            <div class="fact__label">难度</div>
          </div>
          <div class="fact">
            <div class="fact__value">${esc(r.serving)}</div>
            <div class="fact__label">份量</div>
          </div>
          <div class="fact">
            <div class="fact__value">${r.steps.length}</div>
            <div class="fact__label">步骤</div>
          </div>
        </div>

        <section class="panel">
          <div class="panel__head">
            <h3>烹饪步骤</h3>
            <span class="muted">共 ${r.steps.reduce((a, s) => a + s.minutes, 0)} 分钟</span>
          </div>
          <div class="steps">${stepsHtml}</div>
        </section>

        <div class="tip-box">
          <span class="tip-box__icon" aria-hidden="true">${UI_ICONS.bulb}</span>
          <p>${esc(r.tips)}</p>
        </div>
      </div>

      <aside class="recipe-layout__aside">
        <section class="panel">
          <div class="panel__head">
            <h3>营养成分</h3>
            <span class="muted">每份估算</span>
          </div>
          <div class="nutri-grid">${nutriItems}</div>
        </section>

        <section class="panel">
          <div class="panel__head">
            <h3>所需食材</h3>
            <span class="muted">${r.ingredients.length} 项</span>
          </div>
          <div class="ing-list">${ingHtml}</div>
        </section>
      </aside>
    </div>`;
}

/* —— 3.3 营养概览 —— */

/**
 * 营养概览。
 *
 * 数据来源优先级：
 *   1. state.nutrition —— 后端实时计算（点餐后自动刷新）
 *   2. 无后端时由 state.orders 现场计算（离线模式）
 * 不再使用写死的 TODAY_OVERVIEW，否则点餐后页面不会变。
 */
function renderNutrition() {
  const data = state.nutrition || deriveNutritionFromOrders();
  const days = data.days;
  const progress = data.progress;
  const water = data.water;
  const target = data.target;

  // 柱状图：热量 + 蛋白质双色
  const maxCal = Math.max(1, ...days.map((d) => d.calorie));
  const maxPro = Math.max(1, ...days.map((d) => d.protein)) * 10; // 蛋白量级放大便于对比

  $('#calorieChart').innerHTML = days
    .map((d, i) => {
      const calH = d.calorie > 0 ? Math.max(6, Math.round((d.calorie / maxCal) * 100)) : 2;
      const proH = d.protein > 0 ? Math.max(4, Math.round(((d.protein * 10) / maxPro) * 100)) : 2;
      return `
      <div class="chart__col ${i === TODAY_INDEX ? 'is-today' : ''}" title="${esc(d.label)}：${d.calorie} 千卡 / 蛋白质 ${d.protein} 克">
        <div class="chart__bars">
          <div class="chart__bar chart__bar--cal"
               style="height:${calH}%;animation-delay:${i * 45}ms"></div>
          <div class="chart__bar chart__bar--pro"
               style="height:${proH}%;animation-delay:${i * 45 + 60}ms"></div>
        </div>
        <span class="chart__label">${esc(d.label)}</span>
      </div>`;
    })
    .join('');

  // 完成度进度条（按日均值对比每日目标）
  $('#nutriBars').innerHTML = progress
    .map((p, i) => {
      const pct = p.percent;
      const tone = pct >= 90 && pct <= 115 ? 'nbar__fill--ok' : pct < 60 ? 'nbar__fill--low' : '';
      return `
        <div>
          <div class="nbar__top">
            <span class="nbar__name">${esc(p.label)}</span>
            <span class="nbar__val">日均 ${p.dailyAvg} / ${p.target} ${esc(p.unit)} · ${pct}%</span>
          </div>
          <div class="nbar__track">
            <div class="nbar__fill ${tone}"
                 style="width:${Math.min(pct, 100)}%;animation-delay:${i * 70}ms"></div>
          </div>
        </div>`;
    })
    .join('');

  // 饮水环
  const waterTarget = water?.target || target?.water || 2000;
  const waterCurrent = water?.current || 0;
  const waterPct = Math.round((waterCurrent / waterTarget) * 100);
  $('#waterRing').style.setProperty('--pct', Math.min(waterPct, 100));
  $('#waterPct').textContent = waterPct;
  $('#waterNow').textContent = waterCurrent;

  // 页头副标题带上统计口径，避免"为什么是日均"的困惑
  const plannedDays = data.plannedDays ?? days.filter((d) => !d.isEmpty).length;
  PAGE_META.nutrition.sub = plannedDays
    ? `按已排 ${plannedDays} 天统计 · 完成度取日均值`
    : '本周还没有安排，先去点餐或一键生成';
  if (state.route === 'nutrition') $('#pageSub').textContent = PAGE_META.nutrition.sub;
}

/** 离线兜底：直接从本地订单推导营养数据（结构与后端一致） */
function deriveNutritionFromOrders() {
  const days = Order.DAYS.map((d, i) => {
    const acc = { calorie: 0, protein: 0, fat: 0, carb: 0, fiber: 0 };
    let count = 0;
    for (const m of Order.MEALS) {
      for (const it of state.orders[d.key]?.[m.key] || []) {
        const n = RECIPES[it.id]?.nutrition;
        if (!n) continue;
        count += 1;
        for (const k of Object.keys(acc)) acc[k] += (n[k] || 0) * it.qty;
      }
    }
    return {
      key: d.key,
      label: d.label,
      calorie: Math.round(acc.calorie * 10) / 10,
      protein: Math.round(acc.protein * 10) / 10,
      fat: Math.round(acc.fat * 10) / 10,
      carb: Math.round(acc.carb * 10) / 10,
      fiber: Math.round(acc.fiber * 10) / 10,
      isEmpty: count === 0
    };
  });

  const planned = days.filter((d) => !d.isEmpty);
  const denominator = planned.length || 1;
  const totals = days.reduce(
    (acc, d) => {
      for (const k of Object.keys(acc)) acc[k] += d[k];
      return acc;
    },
    { calorie: 0, protein: 0, fat: 0, carb: 0, fiber: 0 }
  );

  const progress = [
    ['calorie', '热量', '千卡'],
    ['protein', '蛋白质', '克'],
    ['fat', '脂肪', '克'],
    ['carb', '碳水化合物', '克'],
    ['fiber', '膳食纤维', '克']
  ].map(([key, label, unit]) => {
    const target = NUTRITION_TARGET[key] || 1;
    const dailyAvg = Math.round((totals[key] / denominator) * 10) / 10;
    return { key, label, unit, total: Math.round(totals[key] * 10) / 10, dailyAvg, target, percent: Math.round((dailyAvg / target) * 100) };
  });

  return {
    days,
    progress,
    water: { current: TODAY_OVERVIEW.water, target: TODAY_OVERVIEW.waterTarget },
    target: NUTRITION_TARGET,
    plannedDays: planned.length
  };
}

/* —— 3.5 家庭管理 —— */

/** 加载并渲染家庭管理页 */
async function loadFamilyPage() {
  try {
    // 先取列表，从列表里拿到当前家庭 id：
    // 这样不依赖 state.user（启动时序上它可能还没就绪）
    const list = await Api.listFamilies();
    state.families = list;

    const activeId =
      list.activeFamilyId ||
      list.items?.find((f) => f.isActive)?.id ||
      state.user?.familyId ||
      '';

    state.familyDetail = activeId ? await Api.getFamily(activeId) : null;
    renderFamilyPage();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      enterOfflineMode();
      return;
    }
    showError(err.message);
  }
}

function renderFamilyPage() {
  const list = state.families?.items || [];
  const detail = state.familyDetail;

  // 外观面板（明暗 + 风格）先渲染：它是设备级偏好，与当前家庭无关，
  // 而且必须在 detail 为空（还没加入任何家庭）时也能看到。
  renderAppearancePanel();

  // 家庭切换列表
  $('#familyCountText').textContent = `共 ${list.length} 个`;
  $('#familyList').innerHTML = list.length
    ? list
        .map(
          (f) => `
      <div class="family-card ${f.isActive ? 'is-active' : ''}">
        <span class="family-card__body">
          <span class="family-card__name">
            ${esc(f.name)}
            ${f.role === 'owner' ? `<span class="member-row__tag">家长</span>` : ''}
          </span>
          <span class="family-card__meta">家长：${esc(f.ownerName)} · ${f.memberCount} 人</span>
        </span>
        ${
          f.isActive
            ? `<span class="family-card__state">${UI_ICONS.check}当前</span>`
            : `<button class="family-card__go" type="button" data-switch-family="${esc(f.id)}">切换</button>`
        }
      </div>`
        )
        .join('')
    : '<p class="empty__hint">还没有家庭</p>';

  // 当前家庭详情
  const host = $('#familyDetail');
  if (!detail) {
    host.innerHTML = '';
    refreshCuteAvatars();
    return;
  }

  const isOwner = detail.isOwner;
  const members = detail.members || [];

  const memberRows = members
    .map(
      (m) => `
      <div class="member-row ${m.role === 'owner' ? 'is-owner' : ''}">
        <span class="member-row__avatar" aria-hidden="true">${esc((m.displayName || m.username || '?').slice(0, 1).toUpperCase())}</span>
        <span class="member-row__body">
          <span class="member-row__name">
            ${esc(m.displayName || m.username)}
            ${m.role === 'owner' ? '<span class="member-row__tag">家长</span>' : ''}
            ${m.isMe ? '<span class="member-row__me">我</span>' : ''}
          </span>
          <span class="member-row__sub">@${esc(m.username)}</span>
        </span>
        ${
          isOwner && m.role !== 'owner'
            ? `<button class="member-row__kick" type="button"
                       data-kick="${esc(m.id)}" data-kick-name="${esc(m.displayName || m.username)}">移出</button>`
            : ''
        }
      </div>`
    )
    .join('');

  host.innerHTML = `
    <div class="family-hero">
      <span class="family-hero__avatar" aria-hidden="true">${esc((detail.name || '家').slice(0, 1))}</span>
      <span class="family-hero__body">
        <span class="family-hero__name">${esc(detail.name)}</span>
        <span class="family-hero__meta">家长：${esc(detail.ownerName)} · ${members.length} 位成员</span>
      </span>
      <span class="family-hero__badge">
        ${isOwner ? `${UI_ICONS.crown}家长` : '成员'}
      </span>
    </div>

    ${
      isOwner && detail.inviteCode
        ? `<div class="invite-box">
             <span class="invite-box__label">邀请码</span>
             <span class="invite-box__code" id="inviteCode">${esc(detail.inviteCode)}</span>
             <button class="btn btn--ghost" type="button" data-copy-invite>复制</button>
             <button class="btn btn--ghost" type="button" data-reset-invite>重置</button>
           </div>`
        : ''
    }

    <div class="panel">
      <div class="panel__head">
        <h3>家庭成员</h3>
        <span class="muted">${members.length} 人</span>
      </div>
      <div class="member-list">${memberRows}</div>

      <div class="family-danger">
        ${
          isOwner
            ? `<button class="btn btn--ghost" type="button" data-rename-family>重命名家庭</button>
               <button class="btn btn--danger-ghost" type="button" data-dissolve-family>解散家庭</button>`
            : `<button class="btn btn--danger-ghost" type="button" data-leave-family>退出该家庭</button>`
        }
      </div>
    </div>`;

  // 可爱风格下把单字圆点头像换成分角色 Q 版 SVG。
  // 默认风格下这次调用只做还原（无残留节点），等于空操作。
  refreshCuteAvatars();
}

/** 切换家庭：成功后整页数据都要重新加载 */
async function doSwitchFamily(familyId) {
  try {
    const data = await Api.switchFamily(familyId);
    state.user = data.user;
    renderUserCard(data.user);
    await loadFamilyPage();
    await loadInitialData();
    refreshOrderViews();
    toast(`已切换到「${data.user.familyName}」`);
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) return enterOfflineMode();
    showError(err.message);
  }
}

/* —— 家庭操作（均使用页面内弹窗，不用原生 confirm/prompt） —— */

/** 重置邀请码 */
async function handleResetInvite() {
  const ok = await dialog.confirm({
    title: '重置邀请码？',
    message: '重置后旧邀请码立即失效，已加入的成员不受影响。',
    okText: '重置',
    danger: true
  });
  if (!ok) return;

  try {
    state.familyDetail = await Api.resetInviteCode(state.user.familyId);
    renderFamilyPage();
    toast('邀请码已更新');
  } catch (err) {
    showError(err.message);
  }
}

/** 移出成员 */
async function handleKickMember(memberId, memberName) {
  const ok = await dialog.confirm({
    title: '移出成员？',
    message: `确定把「${memberName}」移出家庭吗？对方将无法再看到该家庭的菜单。`,
    okText: '移出',
    danger: true
  });
  if (!ok) return;

  try {
    state.familyDetail = await Api.removeMember(state.user.familyId, memberId);
    renderFamilyPage();
    toast(`已移出「${memberName}」`);
  } catch (err) {
    showError(err.message);
  }
}

/** 重命名家庭 */
async function handleRenameFamily() {
  const current = state.familyDetail?.name || '';
  const next = await dialog.prompt({
    title: '重命名家庭',
    label: '家庭名称',
    value: current,
    placeholder: '例如：我家的食堂',
    maxlength: 20,
    okText: '保存'
  });

  if (next === null) return; // 用户取消
  if (!next || next === current) return;

  try {
    const detail = await Api.renameFamily(state.user.familyId, next);
    state.familyDetail = detail;
    state.user.familyName = detail.name;
    renderUserCard(state.user);
    renderFamilyPage();
    toast('家庭名称已更新');
  } catch (err) {
    showError(err.message);
  }
}

/** 退出家庭 */
async function handleLeaveFamily() {
  const ok = await dialog.confirm({
    title: '退出该家庭？',
    message: '退出后将看不到该家庭的菜单，你的收藏仍会保留。',
    okText: '退出',
    danger: true
  });
  if (!ok) return;

  try {
    await Api.leaveFamily(state.user.familyId);
    const me = await Api.me();
    state.user = me;
    renderUserCard(me);
    await loadFamilyPage();
    await loadInitialData();
    refreshOrderViews();
    toast('已退出该家庭');
  } catch (err) {
    showError(err.message);
  }
}

/** 解散家庭 */
async function handleDissolveFamily() {
  const name = state.familyDetail?.name || '该家庭';
  const ok = await dialog.confirm({
    title: '解散家庭？',
    message: `「${name}」的菜单数据将被删除且不可恢复，所有成员将回到各自的家庭。`,
    okText: '解散',
    danger: true
  });
  if (!ok) return;

  try {
    await Api.dissolveFamily(state.user.familyId);
    const me = await Api.me();
    state.user = me;
    renderUserCard(me);
    await loadFamilyPage();
    await loadInitialData();
    refreshOrderViews();
    toast('家庭已解散');
  } catch (err) {
    showError(err.message);
  }
}

/* —— 3.5.5 我的菜谱（维护中心） —— */

/**
 * 菜谱状态 → 展示信息。
 *
 * status 由后端给出（public / private / pending / rejected / archived），
 * statusLabel 也由后端提供中文名，这里只兜底颜色。
 */
const RECIPE_STATUS_META = {
  public: { label: '公共', tone: 'info', hint: '已公开，所有人可见' },
  private: { label: '个人', tone: 'neutral', hint: '仅自己可见，可提交审核' },
  pending: { label: '待审核', tone: 'warn', hint: '审核中，暂不可编辑' },
  rejected: { label: '已驳回', tone: 'danger', hint: '按意见修改后可再次提交' },
  archived: { label: '已下架', tone: 'muted', hint: '已从橱窗下架，历史菜单不受影响' }
};

function statusMeta(item) {
  return RECIPE_STATUS_META[item?.status] || { label: item?.statusLabel || '未知', tone: 'neutral', hint: '' };
}

/** 状态徽标 */
function statusBadgeHtml(item) {
  const meta = statusMeta(item);
  const label = item.statusLabel || meta.label;
  return `<span class="status-badge status-badge--${meta.tone}">${esc(label)}</span>`;
}

/** 菜谱管理页的标签页定义 */
function recipesTabs() {
  const items = state.recipeItems || [];
  const mine = items.filter((it) => it.isMine);
  const pub = items.filter((it) => !it.isMine);
  const tabs = [
    { key: 'mine', label: '我的菜谱', count: mine.length },
    { key: 'public', label: '公共菜谱', count: pub.length }
  ];
  // 审核员才有「待审核」标签（后端 /recipes/pending 返回 200 而非 403）
  if (state.isReviewer) {
    tabs.splice(1, 0, { key: 'pending', label: '待审核', count: (state.pendingRecipes || []).length });
  }
  return tabs;
}

/**
 * 「我的菜谱」页的渲染入口：先确保数据，再绘制。
 *
 * 与 paintRecipes 分开的原因：
 *   绘制是纯函数（只读 state），加载才有副作用。
 *   拆开后加载流程可以安全地"只重绘不重载"，避免请求风暴。
 */
function renderRecipes() {
  ensureRecipesLoaded();
  paintRecipes();
}

/** 纯绘制：只根据 state 出 DOM，不发请求 */
function paintRecipes() {
  renderRecipesTabs();

  const host = $('#recipesList');
  if (!host) return;

  if (state.recipesLoading && state.recipeItems === null) {
    host.innerHTML = `
      <div class="recipes-skeleton" aria-busy="true">
        ${[1, 2, 3].map(() => '<div class="recipes-skeleton__row"></div>').join('')}
      </div>`;
    return;
  }

  // 后端不可用/接口报错：给可重试的空态，而不是白屏
  if (state.recipesError) {
    host.innerHTML = `
      <div class="empty">
        <span class="empty__icon" aria-hidden="true">${UI_ICONS.book || ''}</span>
        <p class="empty__text">菜谱列表加载失败</p>
        <p class="empty__hint">${esc(state.recipesError)}</p>
        <button class="btn btn--ghost" type="button" data-reload-recipes>重新加载</button>
      </div>`;
    return;
  }

  if (state.recipesTab === 'pending') {
    renderPendingList(host);
    return;
  }

  const items = (state.recipeItems || []).filter((it) =>
    state.recipesTab === 'mine' ? it.isMine : !it.isMine
  );

  if (!items.length) {
    host.innerHTML =
      state.recipesTab === 'mine'
        ? `<div class="empty">
             <span class="empty__icon" aria-hidden="true">${UI_ICONS.book || ''}</span>
             <p class="empty__text">还没有自己的菜谱</p>
             <p class="empty__hint">新增一道家里的拿手菜，提交审核后家人也能看到</p>
             <button class="btn btn--primary" type="button" data-new-recipe>新增菜谱</button>
           </div>`
        : `<div class="empty">
             <p class="empty__text">还没有公共菜谱</p>
             <p class="empty__hint">提交审核并通过后，菜谱会出现在这里</p>
           </div>`;
    return;
  }

  host.innerHTML = `<div class="recipe-cards">${items.map(recipeCardHtml).join('')}</div>`;
}

function renderRecipesTabs() {
  const host = $('#recipesTabs');
  if (!host) return;
  const tabs = recipesTabs();
  // 标签页被收回（如失去审核员身份）时回到「我的菜谱」
  if (!tabs.some((t) => t.key === state.recipesTab)) state.recipesTab = 'mine';

  host.innerHTML = tabs
    .map(
      (t) => `
      <button class="recipes-tab ${state.recipesTab === t.key ? 'is-active' : ''}"
              role="tab" aria-selected="${state.recipesTab === t.key}"
              data-recipes-tab="${t.key}">
        ${t.label}<span class="recipes-tab__count">${t.count}</span>
      </button>`
    )
    .join('');
}

/** 单条菜谱卡片：信息 + 状态徽标 + 操作按钮 */
function recipeCardHtml(item) {
  const meta = statusMeta(item);
  const n = item.nutrition || {};
  const calorie = item.calorie ?? n.calorie;
  const timeText = item.time ? `${item.time} 分钟` : '';
  const servingText = item.serving ? esc(item.serving) : '';

  return `
    <article class="recipe-card" data-recipe-row="${esc(item.id)}">
      <div class="recipe-card__main">
        <div class="recipe-card__head">
          <h3 class="recipe-card__name">${esc(item.name)}</h3>
          ${statusBadgeHtml(item)}
          ${item.isMine ? '<span class="recipe-card__mine">我创建的</span>' : ''}
        </div>
        ${item.subtitle ? `<p class="recipe-card__sub">${esc(item.subtitle)}</p>` : ''}
        <div class="recipe-card__meta">
          ${timeText ? `<span class="meta-ico">${UI_ICONS.clock}<i>${timeText}</i></span>` : ''}
          ${calorie != null ? `<span class="meta-ico meta-ico--flame">${UI_ICONS.flame}<i>${calorie} 千卡</i></span>` : ''}
          ${item.difficulty ? `<span class="meta-ico">${esc(item.difficulty)}</span>` : ''}
          ${servingText ? `<span class="meta-ico">${servingText}</span>` : ''}
        </div>
        <div class="dish__tags">${tagsHtml(item.tags || [])}</div>
        ${
          item.status === 'rejected' && item.reviewNote
            ? `<p class="recipe-card__note">驳回原因：${esc(item.reviewNote)}</p>`
            : ''
        }
        ${meta.hint ? `<p class="recipe-card__hint">${esc(meta.hint)}</p>` : ''}
      </div>
      <div class="recipe-card__actions">${recipeActionsHtml(item)}</div>
    </article>`;
}

/**
 * 操作按钮。
 *
 * 显隐优先级：后端给的能力位（canEdit / canSubmit / canReview）优先，
 * 缺失时（例如后端尚未补齐字段）回落到前端按 status + isMine 推断，
 * 保证即使接口字段不全，界面也不会没有可用按钮。
 */
function recipeActionsHtml(item) {
  const btns = [];
  const viewBtn = `<button class="btn btn--ghost btn--sm" type="button"
                     data-recipe-view="${esc(item.id)}">查看</button>`;

  if (!item.isMine) {
    // 公共菜谱只读
    return viewBtn;
  }

  const canEdit = item.canEdit ?? ['private', 'rejected'].includes(item.status);
  const canSubmit = item.canSubmit ?? ['private', 'rejected'].includes(item.status);

  if (canEdit) {
    btns.push(
      `<button class="btn btn--ghost btn--sm" type="button" data-recipe-edit="${esc(item.id)}">编辑</button>`
    );
  }
  if (canSubmit) {
    btns.push(
      `<button class="btn btn--primary btn--sm" type="button" data-recipe-submit="${esc(item.id)}">提交审核</button>`
    );
  }
  if (item.status === 'pending') {
    btns.push(
      `<button class="btn btn--ghost btn--sm" type="button" data-recipe-withdraw="${esc(item.id)}">撤回</button>`
    );
  }
  if (item.status === 'archived') {
    btns.push(
      `<button class="btn btn--ghost btn--sm" type="button" data-recipe-restore="${esc(item.id)}">恢复</button>`
    );
  } else if (item.status !== 'pending') {
    btns.push(
      `<button class="btn btn--ghost btn--sm" type="button" data-recipe-archive="${esc(item.id)}">下架</button>`
    );
  }
  btns.push(
    `<button class="btn btn--danger-ghost btn--sm" type="button" data-recipe-delete="${esc(item.id)}">删除</button>`
  );
  btns.push(viewBtn);
  return btns.join('');
}

/** 审核员的待审核列表 */
function renderPendingList(host) {
  const items = state.pendingRecipes || [];
  if (!items.length) {
    host.innerHTML = `
      <div class="empty">
        <span class="empty__icon" aria-hidden="true">${UI_ICONS.check || ''}</span>
        <p class="empty__text">没有待审核的菜谱</p>
        <p class="empty__hint">有人提交菜谱审核时会出现在这里</p>
      </div>`;
    return;
  }

  host.innerHTML = `<div class="recipe-cards">${items
    .map((item) => {
      const calorie = item.calorie ?? item.nutrition?.calorie;
      return `
      <article class="recipe-card" data-recipe-row="${esc(item.id)}">
        <div class="recipe-card__main">
          <div class="recipe-card__head">
            <h3 class="recipe-card__name">${esc(item.name)}</h3>
            ${statusBadgeHtml(item)}
            ${item.ownerName ? `<span class="recipe-card__mine">提交人：${esc(item.ownerName)}</span>` : ''}
          </div>
          ${item.subtitle ? `<p class="recipe-card__sub">${esc(item.subtitle)}</p>` : ''}
          <div class="recipe-card__meta">
            ${item.time ? `<span class="meta-ico">${UI_ICONS.clock}<i>${item.time} 分钟</i></span>` : ''}
            ${calorie != null ? `<span class="meta-ico meta-ico--flame">${UI_ICONS.flame}<i>${calorie} 千卡</i></span>` : ''}
            ${item.difficulty ? `<span class="meta-ico">${esc(item.difficulty)}</span>` : ''}
          </div>
          <div class="dish__tags">${tagsHtml(item.tags || [])}</div>
        </div>
        <div class="recipe-card__actions">
          <button class="btn btn--primary btn--sm" type="button"
                  data-recipe-approve="${esc(item.id)}">通过</button>
          <button class="btn btn--danger-ghost btn--sm" type="button"
                  data-recipe-reject="${esc(item.id)}">驳回</button>
          <button class="btn btn--ghost btn--sm" type="button"
                  data-recipe-view="${esc(item.id)}">查看</button>
        </div>
      </article>`;
    })
    .join('')}</div>`;
}

/**
 * 拉取菜谱列表。
 *
 * 三种降级路径都要有明确结果，不能吞错后留白页：
 *   · 后端不可用 → 离线提示，可重试
 *   · 接口不存在（后端还没上线该系列接口）→ 提示"功能暂未就绪"
 *   · 其它业务错误 → 原样展示后端文案
 */
async function loadRecipes() {
  if (state.offline) {
    state.recipeItems = null;
    state.recipesError = '后端未连接，菜谱维护功能需要联网使用';
    state.recipesLoading = false;
    paintRecipes();
    return;
  }

  // 同一时刻只允许一个在途请求，避免渲染与加载互相触发导致请求风暴
  if (state.recipesLoading) return;

  state.recipesLoading = true;
  state.recipesError = '';

  try {
    const data = await Api.listRecipes();
    state.recipeItems = normalizeRecipeList(data);
    state.recipesLoadedAt = Date.now();
    // 顺手探测审核员身份（非审核员会拿到 403，静默忽略）
    if (state.isReviewer === null) await probeReviewer();
    else if (state.isReviewer) await loadPending();
  } catch (err) {
    handleRecipeError(err, '菜谱列表');
    // 失败时保持 recipeItems 为 null：
    // 若置成 []，渲染层会误判成"加载成功但没有菜谱"，
    // 把错误态覆盖成空态，用户就看不到失败原因和重试入口了。
    state.recipeItems = null;
  } finally {
    state.recipesLoading = false;
    // 这里只重绘 DOM，不再走 renderRecipes()：
    // 后者会调用 ensureRecipesLoaded()，在失败态下可能与本次加载互相触发。
    paintRecipes();
    updatePendingBadge();
  }
}

/** 后端返回结构统一成 { items: [] } */
function normalizeRecipeList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.items)) return data.items;
  return [];
}

/** 探测当前用户是否审核员：pending 接口 200 即审核员，403 即普通用户 */
async function probeReviewer() {
  try {
    const data = await Api.listPendingRecipes();
    state.isReviewer = true;
    state.pendingRecipes = normalizeRecipeList(data);
  } catch (err) {
    if (err instanceof Api.ApiError && err.status === 403) {
      state.isReviewer = false;
      state.pendingRecipes = [];
    } else if (err instanceof Api.ApiUnavailable) {
      state.isReviewer = false;
      enterOfflineMode();
    } else {
      // 404：后端还没有该接口，按普通用户处理，不报错打扰
      state.isReviewer = false;
      state.pendingRecipes = [];
    }
  }
}

/** 拉取待审核列表（仅审核员） */
async function loadPending() {
  if (!state.isReviewer) return;
  try {
    state.pendingRecipes = normalizeRecipeList(await Api.listPendingRecipes());
  } catch (err) {
    if (err instanceof Api.ApiError && err.status === 403) {
      state.isReviewer = false;
      state.pendingRecipes = [];
    } else {
      state.pendingRecipes = [];
    }
  }
}

/**
 * 菜谱相关的统一错误处理。
 * 后端未就绪时给出可读的提示，而不是抛到控制台让页面空白。
 */
function handleRecipeError(err, action = '操作') {
  if (err instanceof Api.ApiUnavailable) {
    enterOfflineMode();
    state.recipesError = '后端未连接，菜谱功能需要联网使用';
    return;
  }
  if (err instanceof Api.ApiError) {
    if (err.status === 404) {
      state.recipesError = '后端还没有开放菜谱接口，请稍后再试';
      return;
    }
    state.recipesError = err.message || `${action}失败`;
    return;
  }
  state.recipesError = `${action}失败，请稍后重试`;
}

/** 侧栏 / TabBar 的待审核徽标 */
function updatePendingBadge() {
  const count = state.isReviewer ? (state.pendingRecipes || []).length : 0;
  ['pendingCount', 'tabPendingBadge'].forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.hidden = count === 0;
    el.textContent = count;
  });
}

/**
 * 首次进入「我的菜谱」时拉数据。
 *
 * 三种情况都不重复请求：
 *   · 已经成功加载过（recipeItems 非 null）
 *   · 正在加载中
 *   · 上次失败了 —— 交给用户点「重新加载」，避免每次重绘都打一次失败请求
 */
function ensureRecipesLoaded() {
  if (state.recipeItems !== null) return; // 已加载成功
  if (state.recipesLoading) return; // 请求进行中
  if (state.recipesError) return; // 失败态：等用户主动重试
  loadRecipes();
}

/** 从本地列表里取一条菜谱 */
function findRecipeItem(id) {
  const pool = [...(state.recipeItems || []), ...(state.pendingRecipes || [])];
  return pool.find((it) => it.id === id) || null;
}

/* —— 菜谱操作 —— */

/**
 * 提交 / 撤回 / 下架 / 恢复 / 删除 的共同流程：
 *   confirm → 请求 → 成功后重载列表 → toast
 */
async function recipeAction({ id, confirm, request, success }) {
  const item = findRecipeItem(id);
  const name = item?.name || '该菜谱';

  if (confirm) {
    const ok = await dialog.confirm({
      title: confirm.title,
      message: confirm.message.replace('{name}', name),
      okText: confirm.okText,
      danger: Boolean(confirm.danger)
    });
    if (!ok) return false;
  }

  try {
    await request();
    toast(success.replace('{name}', name));
    await reloadRecipes();
    return true;
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) enterOfflineMode();
    showError(err.message || '操作失败');
    return false;
  }
}

/**
 * 强制重新拉取菜谱列表。
 *
 * 写操作（新增/修改/审核/下架…）之后统一走这里：
 * 先清掉失败态与旧数据，再按正常流程加载，最后只重绘依赖它的视图。
 * 状态与能力位都由后端计算，绝不能靠前端本地推断，因此必须重拉。
 */
async function reloadRecipes() {
  state.recipeItems = null;
  state.recipesError = '';
  state.recipesLoading = false;
  // 菜谱变了，点餐橱窗的缓存也必须失效，否则新建的菜不会出现在橱窗
  state.catalogLoaded = false;
  state.catalog = null;
  await loadRecipes();
  refreshRecipeViews();
}

/** 菜谱数据变了之后，刷新依赖它的视图。
 * 只做重绘：数据刚在调用方拉取过，这里再触发加载会产生重复请求。
 */
function refreshRecipeViews() {
  if (state.route === 'recipes') paintRecipes();
  if (state.route === 'order') renderOrder();
}

async function handleSubmitRecipe(id) {
  await recipeAction({
    id,
    confirm: {
      title: '提交审核？',
      message: '「{name}」将进入审核队列，审核通过后所有人都能看到。审核期间不可编辑，可随时撤回。',
      okText: '提交审核'
    },
    request: () => Api.submitRecipe(id),
    success: '已提交审核：「{name}」'
  });
}

async function handleWithdrawRecipe(id) {
  await recipeAction({
    id,
    confirm: {
      title: '撤回审核？',
      message: '「{name}」将从审核队列撤回，恢复为仅自己可见。',
      okText: '撤回'
    },
    request: () => Api.withdrawRecipe(id),
    success: '已撤回：「{name}」'
  });
}

async function handleArchiveRecipe(id) {
  await recipeAction({
    id,
    confirm: {
      title: '下架这道菜？',
      message: '「{name}」将不再出现在点餐橱窗，但已排进菜单的历史记录不受影响，之后可恢复。',
      okText: '下架',
      danger: true
    },
    request: () => Api.archiveRecipe(id),
    success: '已下架：「{name}」'
  });
}

async function handleRestoreRecipe(id) {
  await recipeAction({
    id,
    confirm: {
      title: '恢复这道菜？',
      message: '「{name}」将恢复为个人菜谱，重新出现在你的菜谱列表里。',
      okText: '恢复'
    },
    request: () => Api.restoreRecipe(id),
    success: '已恢复：「{name}」'
  });
}

async function handleDeleteRecipe(id) {
  await recipeAction({
    id,
    confirm: {
      title: '删除这道菜？',
      message: '「{name}」将被永久删除，无法恢复。若已被菜单引用，需要先从菜单移除。',
      okText: '删除',
      danger: true
    },
    request: () => Api.deleteRecipe(id),
    success: '已删除：「{name}」'
  });
}

/** 审核：通过直接提交，驳回需填原因 */
async function handleApproveRecipe(id) {
  const item = findRecipeItem(id);
  const ok = await dialog.confirm({
    title: '审核通过？',
    message: `「${item?.name || '该菜谱'}」通过后将变为公共菜谱，所有人可见。`,
    okText: '通过'
  });
  if (!ok) return;

  try {
    await Api.reviewRecipe(id, true, '');
    toast('已通过审核');
    await loadPending();
    await reloadRecipes();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) enterOfflineMode();
    showError(err.message || '审核失败');
  }
}

async function handleRejectRecipe(id) {
  const item = findRecipeItem(id);
  const note = await dialog.prompt({
    title: '驳回菜谱',
    message: `请说明驳回「${item?.name || '该菜谱'}」的原因，作者会看到这条意见。`,
    label: '驳回原因',
    placeholder: '例如：步骤描述太笼统，缺少年份与火候说明',
    maxlength: 200,
    okText: '驳回'
  });

  if (note === null) return; // 用户取消
  if (!note) {
    toast('请填写驳回原因');
    return;
  }

  try {
    await Api.reviewRecipe(id, false, note);
    toast('已驳回，并通知作者');
    await loadPending();
    await reloadRecipes();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) enterOfflineMode();
    showError(err.message || '驳回失败');
  }
}

/* —— 菜谱编辑弹窗 —— */

/**
 * 菜谱编辑弹窗（新增 / 修改共用）。
 *
 * 为什么不复用 dialog：
 *   dialog 是"一问一答"式的确认/单输入弹窗，而这里是一个多字段长表单，
 *   有动态行、需要校验与滚动，独立控制器更好维护。视觉仍复用 .modal 组件。
 *
 * 约束：
 *   · 标签取值限定在 TAG_META 内（与后端校验口径一致）
 *   · 食材至少 1 项、步骤至少 1 步，名称 1-30 字，时长正整数
 */

/** 难度选项：与后端既有数据口径一致 */
const DIFFICULTY_OPTIONS = ['简单', '中等', '进阶'];

/** 当前编辑的菜谱（null 表示新增）；表单数据从 DOM 读取，不单独存 state */
let editingRecipe = null;

const recipeModal = () => $('#recipeModal');
const recipeModalBody = () => $('#recipeModalBody');

/** 空表单结构 */
function emptyRecipeDraft() {
  return {
    id: '',
    name: '',
    subtitle: '',
    desc: '',
    time: 30,
    difficulty: '中等',
    serving: '2 人份',
    tags: [],
    nutrition: { calorie: 300, protein: 15, fat: 10, carb: 30, fiber: 3 },
    ingredients: [{ name: '', amount: '', main: true }],
    steps: [{ title: '', desc: '', minutes: 5 }],
    tips: ''
  };
}

/** 打开新增弹窗 */
function openCreateRecipe() {
  editingRecipe = null;
  renderRecipeForm(emptyRecipeDraft());
  showRecipeModal('新增菜谱', '保存后为个人菜谱，仅自己可见，可在「我的菜谱」里提交审核');
}

/** 打开编辑弹窗：先从列表项填充，再尝试拉详情补全食材/步骤 */
async function openEditRecipe(id) {
  const listed = findRecipeItem(id);
  editingRecipe = listed || { id };

  // 列表接口通常只返回摘要字段，这里先渲染摘要再异步补全
  renderRecipeForm(draftFromItem(editingRecipe));
  showRecipeModal('编辑菜谱', '修改后保持原有状态，已公开的菜谱会直接更新');

  if (!state.offline) {
    try {
      const detail = await Api.getRecipe(id);
      // 弹窗可能已被取消，避免覆盖用户正在填的表单
      if (editingRecipe?.id !== id) return;
      editingRecipe = { ...editingRecipe, ...detail };
      renderRecipeForm(draftFromItem(editingRecipe));
      showRecipeModal('编辑菜谱', '修改后保持原有状态，已公开的菜谱会直接更新', true);
    } catch (err) {
      // 详情拉不到时，用列表里的摘要数据也能编辑基础字段
      if (err instanceof Api.ApiUnavailable) enterOfflineMode();
    }
  }
}

/** 列表项 / 详情 → 表单草稿（字段缺失时给合理默认值，避免控件为空） */
function draftFromItem(item) {
  const base = emptyRecipeDraft();
  if (!item) return base;

  const n = item.nutrition || {};
  return {
    ...base,
    id: item.id || '',
    name: item.name || '',
    subtitle: item.subtitle || '',
    desc: item.desc || '',
    time: Number(item.time) || base.time,
    difficulty: DIFFICULTY_OPTIONS.includes(item.difficulty) ? item.difficulty : base.difficulty,
    serving: item.serving || base.serving,
    tags: Array.isArray(item.tags) ? item.tags.filter((t) => TAG_META[t]) : [],
    nutrition: {
      calorie: numOr(n.calorie ?? item.calorie, base.nutrition.calorie),
      protein: numOr(n.protein, base.nutrition.protein),
      fat: numOr(n.fat, base.nutrition.fat),
      carb: numOr(n.carb, base.nutrition.carb),
      fiber: numOr(n.fiber, base.nutrition.fiber)
    },
    ingredients:
      Array.isArray(item.ingredients) && item.ingredients.length
        ? item.ingredients.map((i) => ({
            name: i.name || '',
            amount: i.amount || '',
            main: Boolean(i.main)
          }))
        : base.ingredients,
    steps:
      Array.isArray(item.steps) && item.steps.length
        ? item.steps.map((s) => ({
            title: s.title || '',
            desc: s.desc || '',
            minutes: numOr(s.minutes, 5)
          }))
        : base.steps,
    tips: item.tips || ''
  };
}

function numOr(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

/** 渲染表单主体 */
function renderRecipeForm(draft) {
  const tagChips = Object.entries(TAG_META)
    .map(
      ([key, meta]) => `
      <label class="tag-pick ${draft.tags.includes(key) ? 'is-on' : ''}">
        <input type="checkbox" name="recipeTags" value="${esc(key)}"
               ${draft.tags.includes(key) ? 'checked' : ''} />
        <span>${esc(meta.label)}</span>
      </label>`
    )
    .join('');

  const nutri = draft.nutrition;

  recipeModalBody().innerHTML = `
    <div class="recipe-form">
      <div class="recipe-form__row">
        <div class="field">
          <label class="field__label" for="rfName">菜名 <i class="req">*</i></label>
          <input class="control" id="rfName" type="text" maxlength="30"
                 placeholder="例如：番茄炖牛腩" value="${esc(draft.name)}" autocomplete="off" />
        </div>
      </div>

      <div class="field">
        <label class="field__label" for="rfSubtitle">副标题</label>
        <input class="control" id="rfSubtitle" type="text" maxlength="40"
               placeholder="一句话卖点，例如：酸甜浓郁 · 炖到入口即化"
               value="${esc(draft.subtitle)}" autocomplete="off" />
      </div>

      <div class="field">
        <label class="field__label" for="rfDesc">简介</label>
        <textarea class="control control--area" id="rfDesc" rows="2" maxlength="200"
                  placeholder="做法要点、火候与关键技巧">${esc(draft.desc)}</textarea>
      </div>

      <div class="recipe-form__row recipe-form__row--3">
        <div class="field">
          <label class="field__label" for="rfTime">时长（分钟）<i class="req">*</i></label>
          <input class="control" id="rfTime" type="number" min="1" max="600" step="1"
                 value="${esc(draft.time)}" inputmode="numeric" />
        </div>
        <div class="field">
          <label class="field__label" for="rfDifficulty">难度</label>
          <select class="control control--select" id="rfDifficulty">
            ${DIFFICULTY_OPTIONS.map(
              (d) => `<option value="${d}" ${d === draft.difficulty ? 'selected' : ''}>${d}</option>`
            ).join('')}
          </select>
        </div>
        <div class="field">
          <label class="field__label" for="rfServing">份量</label>
          <input class="control" id="rfServing" type="text" maxlength="20"
                 placeholder="例如：2-3 人份" value="${esc(draft.serving)}" autocomplete="off" />
        </div>
      </div>

      <div class="field">
        <span class="field__label">标签（可多选）</span>
        <div class="tag-picks" id="rfTags">${tagChips}</div>
      </div>

      <div class="field">
        <span class="field__label">营养成分（每份估算）</span>
        <div class="nutri-inputs">
          ${[
            ['calorie', '热量', '千卡'],
            ['protein', '蛋白质', 'g'],
            ['fat', '脂肪', 'g'],
            ['carb', '碳水', 'g'],
            ['fiber', '纤维', 'g']
          ]
            .map(
              ([key, label, unit]) => `
            <label class="nutri-input">
              <span class="nutri-input__label">${label}<i>${unit}</i></span>
              <input class="control" id="rfN-${key}" type="number" min="0" step="0.1"
                     value="${esc(nutri[key])}" inputmode="decimal" />
            </label>`
            )
            .join('')}
        </div>
      </div>

      <!-- 食材：可增删，首项默认为主料 -->
      <div class="field">
        <div class="field__label-row">
          <span class="field__label">食材 <i class="req">*</i></span>
          <button class="link-btn" type="button" data-add-ingredient>+ 添加食材</button>
        </div>
        <div class="ing-rows" id="rfIngredients">
          ${draft.ingredients.map(ingredientRowHtml).join('')}
        </div>
      </div>

      <!-- 步骤：可增删 -->
      <div class="field">
        <div class="field__label-row">
          <span class="field__label">步骤 <i class="req">*</i></span>
          <button class="link-btn" type="button" data-add-step>+ 添加步骤</button>
        </div>
        <div class="step-rows" id="rfSteps">
          ${draft.steps.map((s, i) => stepRowHtml(s, i)).join('')}
        </div>
      </div>

      <div class="field">
        <label class="field__label" for="rfTips">小贴士</label>
        <textarea class="control control--area" id="rfTips" rows="2" maxlength="300"
                  placeholder="容易翻车的点、替换方案等">${esc(draft.tips)}</textarea>
      </div>

      <p class="recipe-form__error" id="rfError" role="alert" hidden></p>
    </div>`;
}

function ingredientRowHtml(ing = { name: '', amount: '', main: false }) {
  return `
    <div class="ing-row">
      <input class="control ing-row__name" type="text" maxlength="20"
             placeholder="食材名称" value="${esc(ing.name || '')}"
             data-ing-name autocomplete="off" />
      <input class="control ing-row__amount" type="text" maxlength="16"
             placeholder="用量，如 500 g" value="${esc(ing.amount || '')}"
             data-ing-amount autocomplete="off" />
      <label class="ing-row__main" title="标记为主料">
        <input type="checkbox" data-ing-main ${ing.main ? 'checked' : ''} />
        <span>主料</span>
      </label>
      <button class="row-del" type="button" data-del-ingredient aria-label="删除这行食材">
        <span data-icon="close" aria-hidden="true"></span>
      </button>
    </div>`;
}

function stepRowHtml(step = { title: '', desc: '', minutes: 5 }, index = 0) {
  return `
    <div class="step-row">
      <span class="step-row__idx" data-step-idx>${index + 1}</span>
      <div class="step-row__fields">
        <div class="step-row__top">
          <input class="control step-row__title" type="text" maxlength="30"
                 placeholder="步骤标题，如：牛腩焯水" value="${esc(step.title || '')}"
                 data-step-title autocomplete="off" />
          <label class="step-row__min">
            <input class="control" type="number" min="0" max="600" step="1"
                   value="${esc(numOr(step.minutes, 5))}" data-step-minutes inputmode="numeric" />
            <span>分钟</span>
          </label>
        </div>
        <textarea class="control control--area step-row__desc" rows="2" maxlength="200"
                  placeholder="这一步具体怎么做" data-step-desc>${esc(step.desc || '')}</textarea>
      </div>
      <button class="row-del" type="button" data-del-step aria-label="删除这一步">
        <span data-icon="close" aria-hidden="true"></span>
      </button>
    </div>`;
}

/** 打开弹窗（resetScroll 用于详情回填后回到顶部） */
function showRecipeModal(title, hint, resetScroll = false) {
  $('#recipeModalTitle').textContent = title;
  const body = recipeModalBody();
  // 提示语放在表单最上方，不占 footer
  let tipEl = $('#recipeModalHint');
  if (!tipEl) {
    tipEl = document.createElement('p');
    tipEl.id = 'recipeModalHint';
    tipEl.className = 'modal__hint';
    body.prepend(tipEl);
  }
  tipEl.textContent = hint || '';
  tipEl.hidden = !hint;

  recipeModal().classList.add('is-open');
  document.body.style.overflow = 'hidden';
  if (resetScroll) body.scrollTop = 0;

  // 图标槽位（新增的行由 data-icon 注入）
  injectIcons(recipeModal());
  requestAnimationFrame(() => $('#rfName')?.focus());
}

function closeRecipeModal() {
  recipeModal().classList.remove('is-open');
  document.body.style.overflow = '';
  editingRecipe = null;
}

function isRecipeModalOpen() {
  return recipeModal().classList.contains('is-open');
}

/** 静态 data-icon 槽位注入 SVG（弹窗内动态新增的按钮也要补） */
function injectIcons(root = document) {
  $$('[data-icon]', root).forEach((slot) => {
    if (slot.firstElementChild) return; // 已注入过
    const svg = UI_ICONS[slot.dataset.icon];
    if (svg) slot.innerHTML = svg;
  });
}

function showRecipeFormError(message) {
  const el = $('#rfError');
  if (!el) return;
  el.textContent = message;
  el.hidden = false;
  el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

function hideRecipeFormError() {
  const el = $('#rfError');
  if (el) {
    el.hidden = true;
    el.textContent = '';
  }
}

/** 读取表单 → 菜谱字段（不做校验，校验在 validateRecipeDraft） */
function readRecipeForm() {
  const tags = [];
  $$('input[name="recipeTags"]:checked', recipeModal()).forEach((el) => tags.push(el.value));

  const ingredients = $$('.ing-row', recipeModalBody())
    .map((row) => ({
      name: $(`[data-ing-name]`, row).value.trim(),
      amount: $(`[data-ing-amount]`, row).value.trim(),
      main: Boolean($('[data-ing-main]', row).checked)
    }))
    .filter((ing) => ing.name); // 空行直接丢弃，避免噪音

  const steps = $$('.step-row', recipeModalBody())
    .map((row) => ({
      title: $(`[data-step-title]`, row).value.trim(),
      desc: $(`[data-step-desc]`, row).value.trim(),
      minutes: Math.max(0, Math.round(numOr($('[data-step-minutes]', row).value, 0)))
    }))
    .filter((s) => s.title || s.desc);

  return {
    name: $('#rfName').value.trim(),
    subtitle: $('#rfSubtitle').value.trim(),
    desc: $('#rfDesc').value.trim(),
    time: Math.round(numOr($('#rfTime').value, 0)),
    difficulty: $('#rfDifficulty').value,
    serving: $('#rfServing').value.trim(),
    tags,
    nutrition: {
      calorie: numOr($('#rfN-calorie').value, 0),
      protein: numOr($('#rfN-protein').value, 0),
      fat: numOr($('#rfN-fat').value, 0),
      carb: numOr($('#rfN-carb').value, 0),
      fiber: numOr($('#rfN-fiber').value, 0)
    },
    ingredients,
    steps,
    tips: $('#rfTips').value.trim()
  };
}

/** 前端校验：与后端口径对齐，先拦住明显错误以少一次失败请求 */
function validateRecipeDraft(draft) {
  if (!draft.name) return '请填写菜名';
  if (draft.name.length > 30) return '菜名最多 30 个字';
  if (!Number.isInteger(draft.time) || draft.time <= 0) return '时长需要填写大于 0 的整数分钟';
  if (!draft.ingredients.length) return '至少添加 1 项食材';
  if (!draft.steps.length) return '至少添加 1 个步骤';
  if (draft.tags.some((t) => !TAG_META[t])) return '标签取值不合法';
  return '';
}

/** 保存（新增或修改） */
async function saveRecipeForm() {
  hideRecipeFormError();
  const draft = readRecipeForm();

  const error = validateRecipeDraft(draft);
  if (error) {
    showRecipeFormError(error);
    return;
  }

  const btn = $('#recipeModalSave');
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '保存中…';

  try {
    if (editingRecipe?.id) {
      await Api.updateRecipe(editingRecipe.id, draft);
      toast(`已保存「${draft.name}」`);
    } else {
      await Api.createRecipe(draft);
      toast(`已新增「${draft.name}」`);
    }
    closeRecipeModal();
    // 保存成功后重新拉一次列表：服务端可能补全了 id / 状态 / 能力位
    await reloadRecipes();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      enterOfflineMode();
      showRecipeFormError('后端未连接，暂时无法保存菜谱');
    } else if (err instanceof Api.ApiError) {
      showRecipeFormError(err.message || '保存失败');
    } else {
      showRecipeFormError('保存失败，请稍后重试');
    }
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

/** 重新编号步骤序号（增删后调用） */
function renumberSteps() {
  $$('.step-row__idx', recipeModalBody()).forEach((el, i) => {
    el.textContent = i + 1;
  });
}

/* —— 3.6 收藏 —— */

function renderFavorites() {
  const ids = [...state.favorites].filter((id) => RECIPES[id]);
  const host = $('#favoriteList');

  PAGE_META.favorite.sub = `已收藏 ${ids.length} 道菜`;
  if (state.route === 'favorite') $('#pageSub').textContent = PAGE_META.favorite.sub;

  if (!ids.length) {
    host.innerHTML = `
      <div class="empty">
        <span class="empty__icon" aria-hidden="true">${UI_ICONS.star}</span>
        <p class="empty__text">还没有收藏任何菜品</p>
        <p class="empty__hint">在菜单里点右侧的星标，或在食谱详情页点收藏</p>
      </div>`;
    return;
  }

  host.innerHTML = `<div class="fav-grid">${ids
    .map((id) => {
      const r = RECIPES[id];
      const ic = getDishIcon(id);
      return `
      <button class="fav-card" data-dish="${esc(id)}">
        <span class="fav-card__thumb" style="--ic-fill:${ic.fg};--ic-stroke:#fff;background:${ic.bg}">
          <span class="fav-card__thumb-inner">${ic.svg}</span>
        </span>
        <span class="fav-card__body">
          <span class="fav-card__name">${esc(r.name)}</span>
          <span class="fav-card__meta">${r.time} 分钟 · ${r.nutrition.calorie} 千卡 · ${esc(r.difficulty)}</span>
        </span>
        <span class="fav-card__star" aria-hidden="true">${starHtml(true, '16px')}</span>
      </button>`;
    })
    .join('')}</div>`;
}

/* ── §4 交互 ─────────────────────────────────────────────────── */

/** 数字滚动动画（尊重减少动效偏好） */
function animateNumber(el, target) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduce || !el) {
    if (el) el.textContent = target;
    return;
  }
  const start = performance.now();
  const dur = 700;
  const from = 0;
  function tick(now) {
    const p = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(from + (target - from) * eased);
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function toggleFavorite(id) {
  if (!RECIPES[id]) return;
  const nowFav = !state.favorites.has(id);

  // 先乐观更新 UI，再同步到后端；失败时回滚
  applyFavoriteState(id, nowFav);

  if (!state.offline) {
    Api.toggleFavorite(id)
      .then((data) => {
        // 以后端结果为准
        state.favorites = new Set((data.items || []).map((it) => it.id));
        saveFavorites();
        applyFavoriteState(id, nowFav);
      })
      .catch((err) => {
        if (err instanceof Api.ApiUnavailable) {
          enterOfflineMode();
          saveFavorites();
        } else {
          // 回滚/同步失败：重新拉一次真实状态
          showError(err.message);
          applyFavoriteState(id, !nowFav);
        }
      });
  } else {
    saveFavorites();
  }

  toast(nowFav ? `已收藏「${RECIPES[id].name}」` : `已取消收藏「${RECIPES[id].name}」`);
}

/** 把某个菜品的收藏状态同步到页面上所有相关按钮 */
function applyFavoriteState(id, nowFav) {
  if (nowFav) state.favorites.add(id);
  else state.favorites.delete(id);

  $$(`[data-fav="${CSS.escape(id)}"]`).forEach((el) => {
    el.classList.toggle('is-fav', nowFav);
    el.setAttribute('aria-pressed', String(nowFav));
    el.innerHTML = starHtml(nowFav, el.classList.contains('dish__fav') ? '19px' : '21px');
    const label = el.getAttribute('aria-label') || '';
    el.setAttribute('aria-label', label.replace(nowFav ? '收藏' : '取消收藏', nowFav ? '取消收藏' : '收藏'));
  });

  updateFavBadge();
  if (state.route === 'favorite') renderFavorites();
}

function updateFavBadge() {
  const badge = $('#favCount');
  const count = [...state.favorites].filter((id) => RECIPES[id]).length;
  badge.hidden = count === 0;
  badge.textContent = count;
}

/* —— 全局事件委托 —— */

document.addEventListener('click', (e) => {
  // —— 菜谱：新增 / 编辑 / 查看 / 状态流转 ——
  if (e.target.closest('[data-new-recipe]')) {
    openCreateRecipe();
    return;
  }

  const editBtn = e.target.closest('[data-recipe-edit]');
  if (editBtn) {
    openEditRecipe(editBtn.dataset.recipeEdit);
    return;
  }

  const viewBtn = e.target.closest('[data-recipe-view]');
  if (viewBtn) {
    go('recipe', viewBtn.dataset.recipeView);
    return;
  }

  const submitBtn = e.target.closest('[data-recipe-submit]');
  if (submitBtn) {
    handleSubmitRecipe(submitBtn.dataset.recipeSubmit);
    return;
  }

  const withdrawBtn = e.target.closest('[data-recipe-withdraw]');
  if (withdrawBtn) {
    handleWithdrawRecipe(withdrawBtn.dataset.recipeWithdraw);
    return;
  }

  const archiveBtn = e.target.closest('[data-recipe-archive]');
  if (archiveBtn) {
    handleArchiveRecipe(archiveBtn.dataset.recipeArchive);
    return;
  }

  const restoreBtn = e.target.closest('[data-recipe-restore]');
  if (restoreBtn) {
    handleRestoreRecipe(restoreBtn.dataset.recipeRestore);
    return;
  }

  const deleteBtn = e.target.closest('[data-recipe-delete]');
  if (deleteBtn) {
    handleDeleteRecipe(deleteBtn.dataset.recipeDelete);
    return;
  }

  const approveBtn = e.target.closest('[data-recipe-approve]');
  if (approveBtn) {
    handleApproveRecipe(approveBtn.dataset.recipeApprove);
    return;
  }

  const rejectBtn = e.target.closest('[data-recipe-reject]');
  if (rejectBtn) {
    handleRejectRecipe(rejectBtn.dataset.recipeReject);
    return;
  }

  // —— 菜谱：切换标签页（数据已在，只重绘） ——
  const recipesTabBtn = e.target.closest('[data-recipes-tab]');
  if (recipesTabBtn) {
    state.recipesTab = recipesTabBtn.dataset.recipesTab;
    if (state.recipesTab === 'pending' && !state.pendingRecipes) {
      loadPending().then(() => paintRecipes());
    } else {
      paintRecipes();
    }
    return;
  }

  // —— 菜谱：重新加载（用户主动重试，清掉失败态后重新请求） ——
  if (e.target.closest('[data-reload-recipes]')) {
    state.recipeItems = null;
    state.recipesError = '';
    state.recipesLoading = false;
    loadRecipes();
    return;
  }

  // —— 菜谱弹窗：食材增删 ——
  if (e.target.closest('[data-add-ingredient]')) {
    $('#rfIngredients').insertAdjacentHTML('beforeend', ingredientRowHtml());
    injectIcons(recipeModalBody());
    // 聚焦新行的名称输入，便于连续录入
    $$('.ing-row [data-ing-name]', recipeModalBody()).pop()?.focus();
    return;
  }

  const delIng = e.target.closest('[data-del-ingredient]');
  if (delIng) {
    const rows = $$('.ing-row', recipeModalBody());
    if (rows.length <= 1) {
      // 至少保留一行，否则表单会失去编辑入口
      toast('至少保留一项食材');
      return;
    }
    delIng.closest('.ing-row').remove();
    return;
  }

  // —— 菜谱弹窗：步骤增删 ——
  if (e.target.closest('[data-add-step]')) {
    $('#rfSteps').insertAdjacentHTML('beforeend', stepRowHtml({}, $$('.step-row', recipeModalBody()).length));
    renumberSteps();
    injectIcons(recipeModalBody());
    $$('.step-row [data-step-title]', recipeModalBody()).pop()?.focus();
    return;
  }

  const delStep = e.target.closest('[data-del-step]');
  if (delStep) {
    const rows = $$('.step-row', recipeModalBody());
    if (rows.length <= 1) {
      toast('至少保留一个步骤');
      return;
    }
    delStep.closest('.step-row').remove();
    renumberSteps();
    return;
  }

  // —— 点餐：清空搜索 ——
  if (e.target.closest('[data-clear-catalog-search]')) {
    clearCatalogSearch();
    return;
  }

  // —— 家庭：切换 ——
  const sw = e.target.closest('[data-switch-family]');
  if (sw) {
    doSwitchFamily(sw.dataset.switchFamily);
    return;
  }

  // —— 家庭：复制邀请码 ——
  if (e.target.closest('[data-copy-invite]')) {
    const code = $('#inviteCode')?.textContent?.trim();
    if (code) {
      navigator.clipboard?.writeText(code).then(
        () => toast('邀请码已复制'),
        () => toast(`邀请码：${code}`)
      );
    }
    return;
  }

  // —— 家庭：重置邀请码 ——
  if (e.target.closest('[data-reset-invite]')) {
    handleResetInvite();
    return;
  }

  // —— 家庭：移出成员 ——
  const kick = e.target.closest('[data-kick]');
  if (kick) {
    handleKickMember(kick.dataset.kick, kick.dataset.kickName || '该成员');
    return;
  }

  // —— 家庭：重命名 ——
  if (e.target.closest('[data-rename-family]')) {
    handleRenameFamily();
    return;
  }

  // —— 家庭：退出 ——
  if (e.target.closest('[data-leave-family]')) {
    handleLeaveFamily();
    return;
  }

  // —— 家庭：解散 ——
  if (e.target.closest('[data-dissolve-family]')) {
    handleDissolveFamily();
    return;
  }

  // —— 一键生成本周菜单 ——
  const genBtn = e.target.closest('[data-generate]');
  if (genBtn) {
    generateWeekMenu();
    return;
  }

  // —— 菜单页：从菜单移除某道菜 ——
  const menuDel = e.target.closest('[data-menu-del]');
  if (menuDel) {
    e.stopPropagation();
    const { menuDel: dishId, menuDay, menuMeal } = menuDel.dataset;
    removeFromOrder(menuDay, menuMeal, dishId);
    toast(`已从菜单移除：${RECIPES[dishId]?.name || dishId}`);
    return;
  }

  // —— 点餐：分类筛选 ——
  const chip = e.target.closest('[data-filter]');
  if (chip) {
    state.orderFilter = chip.dataset.filter;
    paintOrder();
    return;
  }

  // —— 点餐：加入 ——
  const addBtn = e.target.closest('[data-add]');
  if (addBtn) {
    const dishId = addBtn.dataset.add;
    // 读取该卡片自己的下拉选择，允许逐张卡片选择不同日期
    const sel = document.querySelector(`[data-order-target="${CSS.escape(dishId)}"]`);
    const [dayKey, mealKey] = (sel?.value || `${state.orderDay}|${state.orderMeal}`).split('|');
    state.orderDay = dayKey;
    state.orderMeal = mealKey;
    addToOrder(dishId, dayKey, mealKey);
    return;
  }

  // —— 点餐：数量增减 ——
  const stepBtn = e.target.closest('[data-qty]');
  if (stepBtn) {
    changeQty(stepBtn.dataset.day, stepBtn.dataset.meal, stepBtn.dataset.id, Number(stepBtn.dataset.qty));
    return;
  }

  // —— 点餐：移除单条 ——
  const delBtn = e.target.closest('[data-del]');
  if (delBtn) {
    removeFromOrder(delBtn.dataset.day, delBtn.dataset.meal, delBtn.dataset.id);
    toast('已从点餐中移除');
    return;
  }

  // —— 点餐：打开 / 关闭点餐篮抽屉（App） ——
  const openBasket = e.target.closest('#orderBarBtn');
  if (openBasket) {
    openBasketSheet();
    return;
  }
  if (e.target.closest('[data-close-sheet]')) {
    closeBasketSheet();
    return;
  }

  // —— 点餐：清空 ——
  if (e.target.closest('#clearOrders')) {
    openClearDialog();
    return;
  }

  // —— 点餐：确认 ——
  if (e.target.closest('#confirmOrders')) {
    openSubmitDialog();
    return;
  }

  const favBtn = e.target.closest('[data-fav]');
  if (favBtn) {
    e.stopPropagation();
    toggleFavorite(favBtn.dataset.fav, favBtn);
    return;
  }

  const dayTab = e.target.closest('[data-day]');
  // 注意：只在没有其它 data-day 元素时才按日切换，避免误判
  if (dayTab) {
    state.dayIndex = Number(dayTab.dataset.day);
    renderMenu();
    return;
  }

  const dish = e.target.closest('[data-dish]');
  if (dish) {
    go('recipe', dish.dataset.dish);
    return;
  }

  // —— 路由跳转按钮（无 href 的 <button data-route>，如点餐页的「我的菜谱」） ——
  const routeBtn = e.target.closest('button[data-route]');
  if (routeBtn) {
    go(routeBtn.dataset.route);
    closeSidebar();
    closeBasketSheet();
    return;
  }

  const routeLink = e.target.closest('[data-route]');
  if (routeLink) {
    closeSidebar();
    closeBasketSheet();
  }
});

// 键盘可达：卡片支持 Enter / Space 打开
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    // 弹窗优先级最高：菜谱编辑弹窗 > 通用弹窗 > 抽屉
    if (isRecipeModalOpen()) {
      closeRecipeModal();
      return;
    }
    if (dialog.isOpen()) {
      dialog.cancel();
      return;
    }
    closeSidebar();
    return;
  }
  if (e.key !== 'Enter' && e.key !== ' ') return;
  // textarea / input 内的空格与回车属于正常输入，不触发跳转
  if (e.target.closest('input, textarea, select')) return;
  const target = e.target.closest('[data-dish][tabindex="0"]');
  if (target) {
    e.preventDefault();
    go('recipe', target.dataset.dish);
  }
});

/* —— 搜索（仅点餐页） —— */

/**
 * 点餐页搜索框。
 *
 * 顶栏原来的全局搜索已移除：它同时作用于一周菜单，又不清空，
 * 容易让人误以为菜单数据少了。现在搜索只属于点餐橱窗，
 * 输入时只重绘橱窗，不触发路由跳转。
 */
const catalogSearchInput = $('#catalogSearch');
const catalogSearchClear = $('#catalogSearchClear');

catalogSearchInput.addEventListener('input', (e) => {
  state.orderQuery = e.target.value;
  syncCatalogSearchClear();
  if (state.route === 'order') paintOrder();
});

catalogSearchInput.addEventListener('keydown', (e) => {
  // Esc 清空搜索，符合搜索框的通用预期
  if (e.key === 'Escape' && e.target.value) {
    e.stopPropagation();
    e.target.value = '';
    state.orderQuery = '';
    syncCatalogSearchClear();
    paintOrder();
  }
});

catalogSearchClear.addEventListener('click', () => clearCatalogSearch());

/** 清空点餐页搜索（按钮与空态里的「清空搜索」共用） */
function clearCatalogSearch() {
  const input = $('#catalogSearch');
  if (input) input.value = '';
  state.orderQuery = '';
  syncCatalogSearchClear();
  if (state.route === 'order') paintOrder();
  input?.focus();
}

/** 有内容时才显示清空按钮 */
function syncCatalogSearchClear() {
  const btn = $('#catalogSearchClear');
  if (btn) btn.hidden = !state.orderQuery.trim();
}

/* —— 侧栏抽屉 —— */

const sidebar = $('#sidebar');
const scrim = document.createElement('div');
scrim.className = 'scrim';
document.body.appendChild(scrim);

function openSidebar() {
  sidebar.classList.add('is-open');
  scrim.classList.add('is-open');
  $('#menuToggle').setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  if (!sidebar.classList.contains('is-open')) return;
  sidebar.classList.remove('is-open');
  scrim.classList.remove('is-open');
  $('#menuToggle').setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

$('#menuToggle').addEventListener('click', () => {
  sidebar.classList.contains('is-open') ? closeSidebar() : openSidebar();
});
scrim.addEventListener('click', closeSidebar);

/* —— 外观：明暗 + 风格（家庭设置里切换） ——
 *
 * 两个维度互不干扰：
 *   data-theme = light | dark   明暗，沿用原来的存储键与行为
 *   data-skin  = cute           风格，不设置即默认暖橙风
 * 具体实现见 js/appearance.js（面板与读写）与 js/skins/cute-skin.js（头像增强）。
 */

/** 渲染家庭设置里的外观面板，并绑定交互 */
function renderAppearancePanel() {
  const host = $('#appearanceHost');
  if (!host) return;
  host.innerHTML = Appearance.appearancePanelHtml();
  Appearance.bindAppearancePanel(host.querySelector('#appearancePanel'), () => {
    // 风格变了：家庭页的头像要跟着换（默认风格会还原成单字圆点）
    refreshCuteAvatars();
  });
}

/** 刷新可爱风对家庭页的增强（默认风格下是空操作式还原） */
function refreshCuteAvatars() {
  if (state.route !== 'family') return;
  try {
    CuteSkin.refreshCuteAvatars();
  } catch {
    /* 皮肤增强失败不该影响主流程 */
  }
}

/* —— 窗口尺寸变化：跨断点时关闭抽屉 —— */

window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024) {
    closeSidebar();
    closeBasketSheet();
  }
});

/* —— 点餐篮抽屉（App 端） —— */

const sheetScrim = document.createElement('div');
sheetScrim.className = 'scrim';
sheetScrim.setAttribute('data-close-sheet', '');
document.body.appendChild(sheetScrim);

const basketEl = () => document.querySelector('.order-basket');

function openBasketSheet() {
  if (window.innerWidth >= 1024) return; // 桌面端常驻，无需抽屉
  basketEl()?.classList.add('is-open');
  sheetScrim.classList.add('is-open');
  state.basketOpen = true;
  document.body.style.overflow = 'hidden';
}

function closeBasketSheet() {
  if (!state.basketOpen) return;
  basketEl()?.classList.remove('is-open');
  sheetScrim.classList.remove('is-open');
  state.basketOpen = false;
  document.body.style.overflow = '';
}

/* —— 通用弹窗（替代 window.confirm / window.prompt） —— */

/**
 * 页面内的弹窗控制器。
 *
 * 为什么不用原生 confirm/prompt：
 *   App 端（WebView）里原生弹窗可能被拦截、样式不可控、且无法统一深色模式，
 *   因此统一用页面内的 .modal 组件，行为与视觉都可控。
 *
 * 用法：
 *   if (await dialog.confirm({ title, message, okText, danger })) { ... }
 *   const name = await dialog.prompt({ title, label, value });   // 取消返回 null
 */
const dialog = (() => {
  let resolver = null;
  let mode = 'confirm'; // confirm | prompt
  let inputEl = null;

  const el = () => $('#modal');

  function settle(value) {
    const done = resolver;
    resolver = null;
    el().classList.remove('is-open');
    document.body.style.overflow = '';
    if (done) done(value);
  }

  /** 打开弹窗并返回 Promise */
  function open({ kind, title, bodyHtml, okText, cancelText, danger, focusSelector }) {
    // 若上一个弹窗还没关闭，先按"取消"收尾，避免 Promise 悬挂
    if (resolver) settle(kind === 'prompt' ? null : false);

    mode = kind;
    $('#modalTitle').textContent = title || '确认';
    $('#modalBody').innerHTML = bodyHtml || '';
    $('#modalOk').textContent = okText || '确定';
    $('#modalCancel').textContent = cancelText || '取消';

    // 主按钮样式：危险操作显示为红色
    $('#modalOk').classList.toggle('btn--primary', !danger);
    $('#modalOk').classList.toggle('btn--danger', Boolean(danger));

    el().classList.add('is-open');
    document.body.style.overflow = 'hidden';

    // 可聚焦元素：输入框优先，其次是主按钮
    requestAnimationFrame(() => {
      const target = focusSelector ? $(focusSelector) : null;
      if (target) {
        target.focus();
        if (target.select) target.select();
      } else {
        $('#modalOk').focus();
      }
    });

    return new Promise((resolve) => {
      resolver = resolve;
    });
  }

  function esc(str) {
    return String(str).replace(/[&<>"']/g, (ch) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
  }

  return {
    /** 确认框：确定返回 true，取消返回 false */
    confirm({ title, message, okText = '确定', cancelText = '取消', danger = false }) {
      const body = message
        ? `<p class="dialog__text">${esc(message)}</p>`
        : '';
      return open({ kind: 'confirm', title, bodyHtml: body, okText, cancelText, danger });
    },

    /** 输入框：确定返回输入值（已 trim），取消返回 null */
    prompt({
      title,
      message = '',
      label = '',
      value = '',
      placeholder = '',
      maxlength = 40,
      okText = '确定',
      cancelText = '取消'
    }) {
      const body = `
        ${message ? `<p class="dialog__text">${esc(message)}</p>` : ''}
        ${label ? `<label class="field__label" for="dialogInput">${esc(label)}</label>` : ''}
        <input class="control" id="dialogInput" type="text"
               value="${esc(value)}" placeholder="${esc(placeholder)}"
               maxlength="${maxlength}" autocomplete="off" />`;
      return open({
        kind: 'prompt',
        title,
        bodyHtml: body,
        okText,
        cancelText,
        focusSelector: '#dialogInput'
      });
    },

    /** 读取当前输入值 */
    read() {
      return inputEl ? inputEl.value : '';
    },

    /** 供外部（按钮/遮罩/Esc）触发收尾 */
    cancel() {
      settle(mode === 'prompt' ? null : false);
    },

    /** 确认 */
    accept() {
      if (mode === 'prompt') {
        inputEl = $('#dialogInput');
        settle((inputEl?.value || '').trim() || null);
      } else {
        settle(true);
      }
    },

    isOpen() {
      return Boolean(resolver);
    },

    mode() {
      return mode;
    }
  };
})();

// 事件绑定：关闭 / 取消 / 遮罩 / 确定
$('#modalClose').addEventListener('click', () => dialog.cancel());
$('#modalCancel').addEventListener('click', () => dialog.cancel());
$('#modal').addEventListener('click', (e) => {
  if (e.target.id === 'modal') dialog.cancel();
});
$('#modalOk').addEventListener('click', () => dialog.accept());

// 输入框里按 Enter 直接确认
$('#modalBody').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && dialog.mode() === 'prompt') {
    e.preventDefault();
    dialog.accept();
  }
});

/* —— 菜谱编辑弹窗的按钮绑定 —— */

$('#recipeModalClose').addEventListener('click', () => closeRecipeModal());
$('#recipeModalCancel').addEventListener('click', () => closeRecipeModal());
$('#recipeModalSave').addEventListener('click', () => saveRecipeForm());
// 点击遮罩关闭（点在面板内部不关）
$('#recipeModal').addEventListener('click', (e) => {
  if (e.target.id === 'recipeModal') closeRecipeModal();
});

// 标签选中态跟随 checkbox（label 包着 input，用 change 事件统一处理）
$('#recipeModalBody').addEventListener('change', (e) => {
  const tagInput = e.target.closest('input[name="recipeTags"]');
  if (tagInput) {
    tagInput.closest('.tag-pick')?.classList.toggle('is-on', tagInput.checked);
  }
});

/* —— 点餐：确认提交 / 清空 —— */

/** 确认提交本周菜单 */
async function openSubmitDialog() {
  const items = Order.countItems(state.orders);
  if (items === 0) {
    toast('还没有点任何菜');
    return;
  }

  const ok = await dialog.confirm({
    title: '确认本周菜单',
    bodyHtml: `<div class="confirm-summary">${Order.confirmSummaryHtml(state.orders)}</div>
       <p class="muted" style="font-size:12px">
         共 ${items} 项，合计 ${Order.totalKcal(state.orders)} 千卡。
       </p>`,
    okText: '确认提交'
  });

  if (!ok) return;
  closeBasketSheet();
  toast(`已确认，本周共 ${items} 项菜品`);
  go('menu');
}

/** 清空本周点餐 */
async function openClearDialog() {
  const items = Order.countItems(state.orders);
  if (items === 0) {
    toast('还没有点任何菜');
    return;
  }

  const ok = await dialog.confirm({
    title: '确认清空本周点餐？',
    message: `将移除全部 ${items} 项已点菜品，此操作不可撤销。`,
    okText: '清空',
    danger: true
  });

  if (!ok) return;

  // 清空必须走后端，否则前后端数据不一致（刷新后旧数据会回来）
  mutateOrders(
    () => Api.clearWeek(),
    () => Order.clearOrders()
  );
  toast('已清空本周菜单');
}

/* ── §5 认证流程 ─────────────────────────────────────────────── */

let authMode = 'login'; // login | register

/** 切换登录 / 注册表单 */
function setAuthMode(mode) {
  authMode = mode;
  const isRegister = mode === 'register';

  $$('[data-auth-tab]').forEach((tab) => {
    const active = tab.dataset.authTab === mode;
    tab.classList.toggle('is-active', active);
    tab.setAttribute('aria-selected', String(active));
  });

  $('#displayNameField').hidden = !isRegister;
  $('#confirmField').hidden = !isRegister;
  $('#authSubmit').textContent = isRegister ? '注册并登录' : '登录';
  $('#authPassword').setAttribute('autocomplete', isRegister ? 'new-password' : 'current-password');
  hideAuthError();
}

function showAuthError(message) {
  const el = $('#authError');
  el.textContent = message;
  el.hidden = false;
}

function hideAuthError() {
  const el = $('#authError');
  el.hidden = true;
  el.textContent = '';
}

/** 显示登录页（隐藏主应用） */
function showAuthPage() {
  $('#authPage').hidden = false;
  $('#app').hidden = true;
  document.body.dataset.authed = 'false';
  setTimeout(() => $('#authUsername')?.focus(), 60);
}

/** 进入主应用 */
function showApp(user) {
  $('#authPage').hidden = true;
  $('#app').hidden = false;
  document.body.dataset.authed = 'true';
  renderUserCard(user);
}

/** 侧栏用户信息 */
function renderUserCard(user) {
  if (!user) return;
  const name = user.displayName || user.username || '我';
  $('#userName').textContent = name;
  $('#userFamily').textContent = user.familyName || '我的家庭';
  $('#userAvatar').textContent = name.slice(0, 1).toUpperCase();
}

/** 提交登录 / 注册 */
async function submitAuth(e) {
  e.preventDefault();

  const username = $('#authUsername').value.trim();
  const password = $('#authPassword').value;
  const displayName = $('#authDisplayName').value.trim();
  const confirm = $('#authConfirm').value;
  const submitBtn = $('#authSubmit');

  hideAuthError();

  // 前端先做基础校验，减少无谓请求
  if (username.length < 2) return showAuthError('用户名至少 2 个字符');
  if (password.length < 6) return showAuthError('密码至少 6 位');
  if (authMode === 'register' && password !== confirm) {
    return showAuthError('两次输入的密码不一致');
  }

  submitBtn.disabled = true;
  const originalText = submitBtn.textContent;
  submitBtn.textContent = authMode === 'register' ? '注册中…' : '登录中…';

  try {
    const data =
      authMode === 'register'
        ? await Api.register(username, password, displayName || undefined)
        : await Api.login(username, password);

    // 必须同步到 state，否则家庭页等依赖 state.user 的逻辑会拿到空值
    state.user = data.user;
    showApp(data.user);
    await startApp();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      showAuthError('无法连接后端服务，请确认已启动 python server/run.py');
    } else {
      showAuthError(err.message || '操作失败，请重试');
    }
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

/** 退出登录 */
async function doLogout() {
  try {
    await Api.logout();
  } catch {
    /* 即便请求失败也清掉本地状态 */
    Api.setToken('');
  }
  state.user = null;
  state.orders = Order.loadOrders();
  state.nutrition = null;
  showAuthPage();
  toast('已退出登录');
}

/* ── §6 启动 ─────────────────────────────────────────────────── */

/** 顶栏右侧的连接状态标识 */
function setConnectionBadge(online) {
  const el = $('#connBadge');
  if (!el) return;
  el.hidden = online;
  el.textContent = online ? '' : '本地模式';
  el.title = online ? '已连接后端' : '后端未连接，数据保存在浏览器本地';
}

/**
 * 登录后加载业务数据。
 *
 * 菜单与营养按家庭隔离、收藏按用户隔离，均由后端按 token 判定，
 * 前端只需带上 token，不需要也不应该自己传 userId。
 */
async function loadInitialData() {
  const [week, favs] = await Promise.all([Api.getWeekMenu(), Api.listFavorites()]);
  state.orders = weekToLocalOrders(week);
  Order.saveOrders(state.orders);
  state.favorites = new Set((favs.items || []).map((it) => it.id));
  saveFavorites();
  state.offline = false;
  setConnectionBadge(true);
}

/** 登录成功（或已有有效会话）后进入主界面 */
async function startApp() {
  const route = location.hash.slice(1).split('/')[0];
  state.route = ROUTES.includes(route) ? route : 'menu';
  if (state.route === 'recipe') state.currentRecipeId = defaultRecipeId();

  // 先渲染一屏骨架，避免等待接口时白屏
  renderRoute(state.route);
  syncRouteUI();
  updateFavBadge();
  renderBasket();

  try {
    await loadInitialData();
  } catch (err) {
    if (err instanceof Api.ApiUnavailable) {
      enterOfflineMode();
    } else if (err?.status !== 401) {
      showError(err.message);
    }
    return;
  }

  if (state.route === 'recipe' && state.currentRecipeId) {
    renderRecipe();
  } else {
    renderRoute(state.route);
  }
  syncRouteUI();
  updateFavBadge();
  renderBasket();
}

async function boot() {
  // 静态图标槽位（导航、品牌、TabBar、登录页）统一注入 SVG
  $$('[data-icon]').forEach((slot) => {
    const svg = UI_ICONS[slot.dataset.icon];
    if (svg) slot.innerHTML = svg;
  });

  // 恢复上次的外观选择（明暗 + 风格）。必须在首屏渲染前执行，
  // 否则会先闪一下默认暖橙再跳到可爱风。
  Appearance.initAppearance();

  // 认证相关事件
  $$('[data-auth-tab]').forEach((tab) => {
    tab.addEventListener('click', () => setAuthMode(tab.dataset.authTab));
  });
  $('#authForm').addEventListener('submit', submitAuth);
  $('#logoutBtn').addEventListener('click', doLogout);
  $('#userSwitchBtn')?.addEventListener('click', () => go('family'));

  // 家庭表单
  $('#familyJoinForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const code = $('#familyCode').value.trim().toUpperCase();
    if (!code) return toast('请输入邀请码');

    try {
      const detail = await Api.joinFamily(code);
      $('#familyCode').value = '';
      // 加入后直接切到该家庭，符合"加入后就想看它"的预期
      await doSwitchFamily(detail.id);
      toast(`已加入「${detail.name}」`);
    } catch (err) {
      showError(err.message);
    }
  });

  $('#familyCreateForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = $('#familyName').value.trim();
    if (!name) return toast('请输入家庭名称');

    try {
      const detail = await Api.createFamily(name);
      $('#familyName').value = '';
      await doSwitchFamily(detail.id);
      toast(`已创建「${detail.name}」`);
    } catch (err) {
      showError(err.message);
    }
  });

  // 会话失效统一跳回登录页
  Api.setUnauthorizedHandler(() => {
    state.user = null;
    showAuthPage();
    showAuthError('登录已失效，请重新登录');
  });

  // 有 token 时先尝试恢复会话，否则直接显示登录页
  if (Api.getToken()) {
    try {
      const user = await Api.me();
      state.user = user;
      showApp(user);
      await startApp();
      return;
    } catch (err) {
      if (err instanceof Api.ApiUnavailable) {
        // 后端没起：明确提示，不静默失败
        showAuthPage();
        showAuthError('无法连接后端服务，请先运行 python server/run.py');
        return;
      }
      // token 失效（401 已由 handler 处理），落到登录页
    }
  }

  setAuthMode('login');
  showAuthPage();
}

boot();
