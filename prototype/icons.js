/**
 * icons.js — 原型专用的图标增量（不改动原站 js/icons.js）
 *
 * 为什么单独放一份：
 *   本次改版要在家庭设置里做主题切换，需要「太阳 / 月亮 / 调色盘」三个图标。
 *   原站 icons.js 没有导出前两个，但 UI_ICONS 是模块级常量对象，
 *   import 之后往下挂即可——浏览器里 ES 模块是单例，
 *   后续 app.js 读到的就是补全后的同一份 UI_ICONS。
 *
 * 只被 prototype/theme.js 引用，线上页面不加载。
 */

import { UI_ICONS } from '../js/icons.js';

const wrap = (inner) =>
  `<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" aria-hidden="true" focusable="false">${inner}</svg>`;

const line = (inner) =>
  wrap(
    `<g stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none">${inner}</g>`
  );

/* 太阳：浅色主题 */
UI_ICONS.sun = line(`
  <circle cx="12" cy="12" r="4.4"/>
  <path d="M12 2.6v2.4M12 19v2.4M2.6 12H5M19 12h2.4M5.4 5.4l1.7 1.7M16.9 16.9l1.7 1.7M18.6 5.4l-1.7 1.7M7.1 16.9l-1.7 1.7"/>`);

/* 月亮：深色主题 */
UI_ICONS.moon = line(`<path d="M20.4 14.2A8.6 8.6 0 0 1 9.8 3.6a8.8 8.8 0 1 0 10.6 10.6Z"/>`);

/* 调色盘：主题设置区的小标题图标 */
UI_ICONS.palette = line(`
  <path d="M12 3.4a8.6 8.6 0 1 0 0 17.2c1.2 0 1.9-.8 1.9-1.8 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.2 0-1 .8-1.8 1.8-1.8h1.4a3.4 3.4 0 0 0 3.4-3.4c0-4.3-4.1-7.7-7.5-7.7Z"/>
  <circle cx="8.6" cy="9.4" r="1.1" fill="currentColor" stroke="none"/>
  <circle cx="12.4" cy="7.6" r="1.1" fill="currentColor" stroke="none"/>
  <circle cx="15.6" cy="10.2" r="1.1" fill="currentColor" stroke="none"/>`);

export { UI_ICONS };
