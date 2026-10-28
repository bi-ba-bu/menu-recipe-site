/**
 * api.js — 后端接口客户端
 *
 * 设计要点：
 *   · 统一封装 fetch，自动 JSON 编解码与错误抛出
 *   · 后端不可用时抛 ApiUnavailable，由调用方决定是否降级到 localStorage
 *   · 接口路径与 Python 后端 server/app/api/router.py 一一对应
 */

const BASE = '/api';

/** 登录 token 存储键 */
const TOKEN_KEY = 'menu-recipe-token';

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY) || '';
  } catch {
    return '';
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* 隐私模式下忽略 */
  }
}

/** 会话失效回调：任何接口返回 401 时触发，由 app.js 跳回登录页 */
let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

/** 后端不可达（未启动 / 网络错误），调用方据此降级 */
export class ApiUnavailable extends Error {
  constructor(message = '后端服务不可用') {
    super(message);
    this.name = 'ApiUnavailable';
  }
}

/** 业务错误（4xx/5xx，后端有明确返回） */
export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request(path, { method = 'GET', body, auth = true } = {}) {
  const init = { method, headers: {} };
  if (body !== undefined) {
    init.headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(body);
  }
  if (auth) {
    const token = getToken();
    if (token) init.headers['Authorization'] = `Bearer ${token}`;
  }

  let resp;
  try {
    resp = await fetch(`${BASE}${path}`, init);
  } catch {
    // 网络层失败：服务没起、被拦截等
    throw new ApiUnavailable();
  }

  let payload = null;
  try {
    payload = await resp.json();
  } catch {
    throw new ApiError(resp.status, '服务端返回了非 JSON 内容');
  }

  // 会话失效：清掉本地 token 并通知上层
  if (resp.status === 401 && auth) {
    setToken('');
    if (typeof onUnauthorized === 'function') onUnauthorized();
    throw new ApiError(401, payload?.error || '登录已失效，请重新登录');
  }

  if (!resp.ok || payload?.ok === false) {
    throw new ApiError(resp.status, payload?.error || `请求失败（${resp.status}）`);
  }
  return payload.data;
}

/* ── 认证 ──────────────────────────────────────────────────── */

export async function register(username, password, displayName) {
  const data = await request('/auth/register', {
    method: 'POST',
    body: { username, password, displayName },
    auth: false
  });
  if (data?.token) setToken(data.token);
  return data;
}

export async function login(username, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: { username, password },
    auth: false
  });
  if (data?.token) setToken(data.token);
  return data;
}

export async function logout() {
  try {
    await request('/auth/logout', { method: 'POST' });
  } finally {
    setToken('');
  }
}

export async function me() {
  return request('/auth/me');
}

/* ── 家庭管理 ──────────────────────────────────────────────── */

export async function listFamilies() {
  return request('/families');
}

export async function getFamily(familyId) {
  return request(`/families/${encodeURIComponent(familyId)}`);
}

export async function createFamily(name) {
  return request('/families', { method: 'POST', body: { name } });
}

export async function joinFamily(code) {
  return request('/families/join', { method: 'POST', body: { code } });
}

export async function switchFamily(familyId) {
  return request(`/families/${encodeURIComponent(familyId)}/switch`, { method: 'POST' });
}

export async function renameFamily(familyId, name) {
  return request(`/families/${encodeURIComponent(familyId)}`, { method: 'PATCH', body: { name } });
}

export async function resetInviteCode(familyId) {
  return request(`/families/${encodeURIComponent(familyId)}/invite-code`, { method: 'POST' });
}

export async function leaveFamily(familyId) {
  return request(`/families/${encodeURIComponent(familyId)}/leave`, { method: 'POST' });
}

export async function removeMember(familyId, memberId) {
  return request(
    `/families/${encodeURIComponent(familyId)}/members/${encodeURIComponent(memberId)}`,
    { method: 'DELETE' }
  );
}

export async function dissolveFamily(familyId) {
  return request(`/families/${encodeURIComponent(familyId)}`, { method: 'DELETE' });
}

/* ── 健康检查 ──────────────────────────────────────────────── */

export async function health() {
  return request('/health', { auth: false });
}

/* ── 元数据 ────────────────────────────────────────────────── */

export async function getMeta() {
  return request('/meta');
}

/* ── 菜品 ──────────────────────────────────────────────────── */

export async function listDishes(tag, q) {
  const params = new URLSearchParams();
  if (tag && tag !== 'all') params.set('tag', tag);
  if (q) params.set('q', q);
  const qs = params.toString();
  return request(`/dishes${qs ? `?${qs}` : ''}`);
}

export async function getDish(dishId) {
  return request(`/dishes/${encodeURIComponent(dishId)}`);
}

/* ── 一周菜单 / 点餐 ───────────────────────────────────────── */

export async function getWeekMenu() {
  return request('/menu');
}

export async function addItem(dishId, day, meal, qty = 1) {
  return request('/menu/items', { method: 'POST', body: { dishId, day, meal, qty } });
}

export async function setQuantity(dishId, day, meal, qty) {
  return request('/menu/items', { method: 'PATCH', body: { dishId, day, meal, qty } });
}

export async function removeItem(dishId, day, meal) {
  const params = new URLSearchParams({ dishId, day, meal });
  return request(`/menu/items?${params.toString()}`, { method: 'DELETE' });
}

export async function generateWeek() {
  return request('/menu/generate', { method: 'POST' });
}

export async function clearWeek() {
  return request('/menu/clear', { method: 'POST' });
}

/* ── 营养 ──────────────────────────────────────────────────── */

export async function getNutrition() {
  return request('/nutrition');
}

/* ── 收藏 ──────────────────────────────────────────────────── */

export async function listFavorites() {
  return request('/favorites');
}

export async function addFavorite(dishId) {
  return request('/favorites', { method: 'POST', body: { dishId } });
}

export async function removeFavorite(dishId) {
  return request(`/favorites/${encodeURIComponent(dishId)}`, { method: 'DELETE' });
}

export async function toggleFavorite(dishId) {
  return request(`/favorites/${encodeURIComponent(dishId)}/toggle`, { method: 'POST' });
}

/* ── 菜谱维护 ──────────────────────────────────────────────── */

/**
 * 菜谱系列接口。
 *
 * 可见性由后端按 token 判定，前端不传用户身份：
 *   · GET /recipes 返回「所有公共菜谱 + 我自己创建的全部菜谱」
 *   · 每条附带 isMine / canEdit / canSubmit / canReview 等能力位，
 *     前端据此决定按钮显隐，避免自己推断权限而产生越权请求。
 */

/** 我的 + 公共菜谱列表 */
export async function listRecipes() {
  return request('/recipes');
}

/** 新增菜谱（入参为完整菜谱字段） */
export async function createRecipe(payload) {
  return request('/recipes', { method: 'POST', body: payload });
}

/** 菜谱详情 */
export async function getRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}`);
}

/** 修改菜谱（局部字段） */
export async function updateRecipe(dishId, payload) {
  return request(`/recipes/${encodeURIComponent(dishId)}`, { method: 'PATCH', body: payload });
}

/** 下架（软删除，历史菜单不受影响） */
export async function archiveRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}/archive`, { method: 'POST' });
}

/** 恢复已下架菜谱 */
export async function restoreRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}/restore`, { method: 'POST' });
}

/** 提交审核 */
export async function submitRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}/submit`, { method: 'POST' });
}

/** 撤回审核 */
export async function withdrawRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}/withdraw`, { method: 'POST' });
}

/** 待审核列表：仅审核员可调用，非审核员后端返回 403 */
export async function listPendingRecipes() {
  return request('/recipes/pending');
}

/** 审核：approve 为 true 通过、false 驳回，note 为审核意见 */
export async function reviewRecipe(dishId, approve, note = '') {
  return request(`/recipes/${encodeURIComponent(dishId)}/review`, {
    method: 'POST',
    body: { approve, note }
  });
}

/** 物理删除（被菜单引用时后端会拒绝） */
export async function deleteRecipe(dishId) {
  return request(`/recipes/${encodeURIComponent(dishId)}`, { method: 'DELETE' });
}
