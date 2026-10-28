/**
 * icons.js — 内联 SVG 图标集
 *
 * 为什么不用 emoji：
 *   不同系统/字体对 emoji 的渲染差异大（部分设备显示为黑白剪影或不支持），
 *   在正式产品里做"菜品缩略图"不可控。这里用 SVG 统一视觉，
 *   颜色通过 currentColor 或内联变量叠加，跟随主题。
 *
 * 每个图标为 24×24 视口的路径集合，统一 fill 语义。
 */

const wrap = (inner) =>
  `<svg viewBox="0 0 24 24" width="100%" height="100%" fill="none" aria-hidden="true" focusable="false">${inner}</svg>`;

/* ———————————— 菜品图标 ———————————— */

const ICONS = {
  /* 汤锅 / 汤羹（锅身 + 锅盖提手 + 双耳，整体为明确剪影） */
  pot: wrap(`
    <path d="M4.8 10.6h14.4a1.4 1.4 0 0 1 1.4 1.4v2.4a5.4 5.4 0 0 1-5.4 5.4H8.8a5.4 5.4 0 0 1-5.4-5.4V12a1.4 1.4 0 0 1 1.4-1.4Z"
          fill="var(--ic-fill, currentColor)"/>
    <path d="M2.4 12.4h1.6M20 12.4h1.6" stroke="var(--ic-fill, currentColor)" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M9.6 10.4V8.2h4.8v2.2" fill="none" stroke="var(--ic-fill, currentColor)" stroke-width="2"/>
    <path d="M12 4.4v2" stroke="var(--ic-fill, currentColor)" stroke-width="2" stroke-linecap="round"/>
    <path d="M8.4 13.6c.7 1.6.7 3.2 0 4.6M13 13.6c.7 1.6.7 3.2 0 4.6"
          stroke="var(--ic-stroke, #fff)" stroke-width="1.5" stroke-linecap="round" opacity=".8"/>`),

  /* 番茄 */
  tomato: wrap(`
    <circle cx="12" cy="14" r="7.5" fill="var(--ic-fill, currentColor)" opacity=".92"/>
    <path d="M12 6.5c-1.8-2-4.4-2.2-5.4-1.4 1.6.2 2.6 1 3.2 1.9-1.6-.5-3.2-.2-4 .8 1.9.3 3.3 1 4.2 2"
          stroke="var(--ic-stroke, #2f9e6f)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M12 6.5c1.8-2 4.4-2.2 5.4-1.4-1.6.2-2.6 1-3.2 1.9" stroke="var(--ic-stroke, #2f9e6f)"
          stroke-width="1.7" stroke-linecap="round"/>`),

  /* 西兰花 / 蔬菜 */
  veg: wrap(`
    <path d="M12 9.5c-2.6-3-6.6-2-6.6 1.2 0 1.3.8 2.3 2 2.7-.3 1.9 1 3.3 2.9 3.3h3.4c1.9 0 3.2-1.4 2.9-3.3 1.2-.4 2-1.4 2-2.7 0-3.2-4-4.2-6.6-1.2Z"
          fill="var(--ic-fill, currentColor)" opacity=".92"/>
    <path d="M12 13.5v7" stroke="var(--ic-stroke, currentColor)" stroke-width="2" stroke-linecap="round" opacity=".65"/>`),

  /* 鱼 */
  fish: wrap(`
    <path d="M3.4 12s3.2-4.6 8-4.6 7 4.6 7 4.6-2.6 4.6-7 4.6S3.4 12 3.4 12Z"
          fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M18.4 12 22 8.8v6.4L18.4 12Z" fill="var(--ic-fill, currentColor)" opacity=".75"/>
    <circle cx="8" cy="11.4" r="1" fill="var(--ic-stroke, #fff)"/>`),

  /* 鸡 / 肉 */
  chicken: wrap(`
    <path d="M15.2 3.4a5.2 5.2 0 0 1 3.2 8.9l-4.7 4.7a3.2 3.2 0 1 1-2.5-2.5l4.7-4.7a5.2 5.2 0 0 0-.7-6.4Z"
          fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M7.6 14.6 3.9 18.3a2.6 2.6 0 1 0 3.7 3.7l3.7-3.7" stroke="var(--ic-fill, currentColor)"
          stroke-width="2" stroke-linecap="round" opacity=".65"/>`),

  /* 米饭 / 面 */
  rice: wrap(`
    <path d="M3.6 12h16.8c0 4.4-3.8 7.6-8.4 7.6S3.6 16.4 3.6 12Z" fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M7 12c0-2.8 2.2-5 5-5s5 2.2 5 5" stroke="var(--ic-fill, currentColor)" stroke-width="2" opacity=".55"/>
    <path d="M4.5 21h15" stroke="var(--ic-stroke, currentColor)" stroke-width="2" stroke-linecap="round" opacity=".5"/>`),

  /* 饺子 */
  dumpling: wrap(`
    <path d="M2.8 16.5c0-3.8 4.1-7 9.2-7s9.2 3.2 9.2 7c0 .9-.7 1.4-1.6 1.4H4.4c-.9 0-1.6-.5-1.6-1.4Z"
          fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M7 12.2c.6 1.2.6 2.6 0 3.8M12 11.6c.6 1.5.6 3.2 0 4.6M17 12.2c.6 1.2.6 2.6 0 3.8"
          stroke="var(--ic-stroke, #fff)" stroke-width="1.5" stroke-linecap="round" opacity=".85"/>`),

  /* 面条碗 */
  bowl: wrap(`
    <path d="M3.2 11.5h17.6c0 4.7-3.9 8-8.8 8s-8.8-3.3-8.8-8Z" fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M7.5 8.6c0-1.2 1-1.8 1-3M12 7.9c0-1.2 1-1.8 1-3M16.5 8.6c0-1.2 1-1.8 1-3"
          stroke="var(--ic-stroke, currentColor)" stroke-width="1.7" stroke-linecap="round" opacity=".6"/>`),

  /* 餐具碗（品牌标识用：碗 + 热气，线条风格） */
  bowlLine: wrap(`
    <g stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M3.4 11.4h17.2c0 4.5-3.8 7.8-8.6 7.8s-8.6-3.3-8.6-7.8Z"/>
      <path d="M2.2 11.4h19.6"/>
      <path d="M8.6 6.6c0-1.6 1.4-2.2 1.4-3.8M13.4 6.6c0-1.6 1.4-2.2 1.4-3.8" opacity=".7"/>
    </g>`),

  /* 粥 */
  congee: wrap(`
    <path d="M3.6 13h16.8v1.4c0 3.6-3 6-8.4 6s-8.4-2.4-8.4-6V13Z" fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M2 13h20" stroke="var(--ic-stroke, currentColor)" stroke-width="2" stroke-linecap="round" opacity=".6"/>
    <circle cx="9" cy="9.6" r="1.1" fill="var(--ic-fill, currentColor)" opacity=".55"/>
    <circle cx="14.4" cy="8.6" r="1.4" fill="var(--ic-fill, currentColor)" opacity=".55"/>`),

  /* 鸡蛋 */
  egg: wrap(`
    <path d="M12 3.2c3.4 0 6.2 4.4 6.2 8.6 0 4-2.6 7-6.2 7s-6.2-3-6.2-7c0-4.2 2.8-8.6 6.2-8.6Z"
          fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <ellipse cx="10" cy="10.5" rx="2" ry="2.8" fill="var(--ic-stroke, #fff)" opacity=".5"/>`),

  /* 面包 / 吐司 */
  bread: wrap(`
    <path d="M3.6 9.6c0-2.6 1.8-4.4 4.4-4.4h8c2.6 0 4.4 1.8 4.4 4.4 0 1.5-.6 2.4-1.4 3v6.2c0 .8-.6 1.4-1.4 1.4H6.4c-.8 0-1.4-.6-1.4-1.4v-6.2c-.8-.6-1.4-1.5-1.4-3Z"
          fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M7.4 12.4h9.2" stroke="var(--ic-stroke, #fff)" stroke-width="1.6" stroke-linecap="round" opacity=".6"/>`),

  /* 水果拼盘 */
  fruit: wrap(`
    <circle cx="9" cy="14.5" r="5.4" fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <circle cx="16.4" cy="12.4" r="3.6" fill="var(--ic-fill, currentColor)" opacity=".6"/>
    <path d="M12 8.6c.6-2.2 2.4-3.6 4.6-3.6-.4 2.4-2.2 3.8-4.6 3.6Z" fill="var(--ic-stroke, #2f9e6f)"
          opacity=".9"/>`),

  /* 汤勺 / 通用 */
  spoon: wrap(`
    <ellipse cx="9.4" cy="8.4" rx="5.2" ry="4.6" fill="var(--ic-fill, currentColor)" opacity=".9"/>
    <path d="M12.6 12.2 19.4 19" stroke="var(--ic-fill, currentColor)" stroke-width="2.4" stroke-linecap="round" opacity=".65"/>`)
};

/* ———————————— 菜品 ID → 图标 + 配色 ———————————— */
/**
 * 用色取自该菜品主色，避免所有缩略图同色。
 * bg 为浅底，fg 为图标主色。
 */
export const DISH_ICON = {
  'tomato-beef': { icon: 'pot', fg: '#d9553c', bg: '#fdeee9' },
  'garlic-broccoli': { icon: 'veg', fg: '#2f8f4e', bg: '#e9f6ed' },
  'steamed-fish': { icon: 'fish', fg: '#2f7fc1', bg: '#e8f2fb' },
  'mapo-tofu': { icon: 'pot', fg: '#c2410c', bg: '#fdeee5' },
  'oat-congee': { icon: 'congee', fg: '#b08340', bg: '#faf3e6' },
  'boiled-egg': { icon: 'egg', fg: '#d9a220', bg: '#fdf6e0' },
  'soy-milk': { icon: 'congee', fg: '#a08850', bg: '#f7f2e6' },
  'scallion-pancake': { icon: 'bread', fg: '#c98a15', bg: '#fdf4e0' },
  'kung-pao-chicken': { icon: 'chicken', fg: '#c2410c', bg: '#fdede3' },
  'vinegar-cabbage': { icon: 'veg', fg: '#4d8a3f', bg: '#eef5e9' },
  rice: { icon: 'rice', fg: '#b08340', bg: '#f8f2e6' },
  'shrimp-noodle': { icon: 'bowl', fg: '#d9553c', bg: '#fdeee9' },
  'cucumber-salad': { icon: 'veg', fg: '#3f9e6a', bg: '#e9f6ed' },
  'millet-porridge': { icon: 'congee', fg: '#cf9a2c', bg: '#fdf5e3' },
  'steamed-bun': { icon: 'dumpling', fg: '#b08340', bg: '#f7f2e6' },
  'braised-pork': { icon: 'pot', fg: '#a0522d', bg: '#f7ede5' },
  'stir-greens': { icon: 'veg', fg: '#4d8a3f', bg: '#eef5e9' },
  'tofu-soup': { icon: 'pot', fg: '#d9553c', bg: '#fdeee9' },
  'cold-noodle': { icon: 'bowl', fg: '#b08340', bg: '#f7f2e6' },
  'egg-custard': { icon: 'egg', fg: '#d9a220', bg: '#fdf6e0' },
  'whole-wheat-toast': { icon: 'bread', fg: '#a0703c', bg: '#f6efe6' },
  'pepper-pork': { icon: 'chicken', fg: '#7c3aed', bg: '#f3ecfd' },
  'chicken-soup': { icon: 'pot', fg: '#b08d57', bg: '#faf4e8' },
  'spinach-vermicelli': { icon: 'veg', fg: '#3f8f5a', bg: '#e9f6ed' },
  'red-bean-soup': { icon: 'congee', fg: '#a33a3a', bg: '#fbecec' },
  'tea-egg': { icon: 'egg', fg: '#8a5a2b', bg: '#f6efe6' },
  'sweet-sour-ribs': { icon: 'chicken', fg: '#d9553c', bg: '#fdeee9' },
  'oil-bean-sprouts': { icon: 'veg', fg: '#5a9e3f', bg: '#eff6e9' },
  dumplings: { icon: 'dumpling', fg: '#8a6a4a', bg: '#f5f0e9' },
  'seaweed-egg-soup': { icon: 'pot', fg: '#2f7fc1', bg: '#e8f2fb' },
  'pancake-fruit': { icon: 'bread', fg: '#c98a15', bg: '#fdf4e0' },
  'fruit-plate': { icon: 'fruit', fg: '#e0654a', bg: '#fdeee9' },
  'braised-chicken': { icon: 'chicken', fg: '#a0522d', bg: '#f7ede5' },
  'lotus-root': { icon: 'veg', fg: '#4d8a3f', bg: '#eef5e9' },
  'beef-noodle': { icon: 'bowl', fg: '#8a4b2a', bg: '#f6ece5' },
  'radish-pickle': { icon: 'veg', fg: '#3f9e6a', bg: '#e9f6ed' },
  'pumpkin-soup': { icon: 'pot', fg: '#cf8a2c', bg: '#fdf3e3' },
  'veggie-sandwich': { icon: 'bread', fg: '#4d8a3f', bg: '#eef5e9' }
};

/** 取图标定义，未登记时回落到通用勺形 */
export function getDishIcon(id) {
  const meta = DISH_ICON[id] || { icon: 'spoon', fg: '#e0654a', bg: '#fdeee9' };
  return { svg: ICONS[meta.icon] || ICONS.spoon, fg: meta.fg, bg: meta.bg };
}

/* ———————————— 界面线性图标 ———————————— */
/** 线性图标：统一 1.8 stroke，currentColor 继承文字颜色 */
const line = (inner) =>
  wrap(
    `<g stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none">${inner}</g>`
  );

export const UI_ICONS = {
  /* 菜单 / 日历 */
  calendar: line(`
    <rect x="3.2" y="5" width="17.6" height="15.8" rx="3"/>
    <path d="M8 3.2v3.6M16 3.2v3.6M3.2 10h17.6"/>
    <path d="M7.6 14h2M12 14h2M7.6 17.4h2"/>`),

  /* 食谱 / 书 */
  book: line(`
    <path d="M12 6.6C10.4 5.2 8.3 4.6 5.4 4.7A1.4 1.4 0 0 0 4 6.1v11.2c0 .9.7 1.5 1.6 1.4 2.6-.2 4.7.4 6.4 1.6 1.7-1.2 3.8-1.8 6.4-1.6.9.1 1.6-.5 1.6-1.4V6.1c0-.9-.6-1.5-1.4-1.4-2.9-.1-5 .5-6.6 1.9Z"/>
    <path d="M12 6.6v13.7"/>`),

  /* 营养 / 叶子 */
  leaf: line(`
    <path d="M20 4c-8.4-.6-13.6 3-13.6 8.4A6.4 6.4 0 0 0 13 18.8C18.4 18.8 21 12.4 20 4Z"/>
    <path d="M4 20.4c1.4-4.6 4.6-8 9.2-10"/>`),

  /* 收藏 / 星标（线性） */
  star: line(`
    <path d="m12 3.6 2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.2-4.1 5.8-.8L12 3.6Z"/>`),

  /* 收藏 / 星标（实心，用于已收藏） */
  starFill: wrap(`
    <path d="m12 3.6 2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.8-5.2 2.8 1-5.8-4.2-4.1 5.8-.8L12 3.6Z"
          fill="currentColor"/>`),

  /* 家庭 / 多用户 */
  users: line(`
    <circle cx="9.2" cy="8.4" r="3.4"/>
    <path d="M3.2 19.6c0-3.1 2.7-5.4 6-5.4s6 2.3 6 5.4"/>
    <path d="M16.4 5.4a3.2 3.2 0 0 1 0 6.2M17.6 14.6c1.9.5 3.2 2 3.2 4.2"/>`),

  /* 用户 / 单人 */
  user: line(`
    <circle cx="12" cy="8" r="3.8"/>
    <path d="M5 20c0-3.4 3.1-5.8 7-5.8s7 2.4 7 5.8"/>`),

  /* 切换 / 双向箭头 */
  swap: line(`
    <path d="M4.4 8.4h13.2l-3.2-3.2M19.6 15.6H6.4l3.2 3.2"/>`),

  /* 皇冠 / 家长 */
  crown: wrap(`
    <path d="M3.2 7.4 6.6 12 12 5l5.4 7 3.4-4.6-1.6 10.4a1.4 1.4 0 0 1-1.4 1.2H6.2a1.4 1.4 0 0 1-1.4-1.2L3.2 7.4Z"
          fill="currentColor" opacity=".9"/>`),

  /* 早餐 / 日出 */
  sunrise: line(`
    <path d="M12 3.6v3.2M5.4 6.6l2.2 2.2M18.6 6.6l-2.2 2.2"/>
    <path d="M3.4 17.4h17.2M6.6 17.4a5.4 5.4 0 0 1 10.8 0"/>
    <path d="M2.6 20.6h18.8"/>`),

  /* 午餐 / 太阳 */
  sun: line(`
    <circle cx="12" cy="12" r="4.2"/>
    <path d="M12 2.8v2.6M12 18.6v2.6M2.8 12h2.6M18.6 12h2.6M5.5 5.5l1.9 1.9M16.6 16.6l1.9 1.9M18.5 5.5l-1.9 1.9M7.4 16.6l-1.9 1.9"/>`),

  /* 晚餐 / 月亮 */
  moon: line(`<path d="M20.4 14.2A8.6 8.6 0 0 1 9.8 3.6a8.8 8.8 0 1 0 10.6 10.6Z"/>`),

  /* 小贴士 / 灯泡 */
  bulb: line(`
    <path d="M9 17.4a6 6 0 1 1 6 0v1.4a1.6 1.6 0 0 1-1.6 1.6h-2.8A1.6 1.6 0 0 1 9 18.8v-1.4Z"/>
    <path d="M10 21.4h4"/>`),

  /* 时钟 */
  clock: line(`
    <circle cx="12" cy="12" r="8.4"/>
    <path d="M12 7.4V12l3.2 1.9"/>`),

  /* 火苗 / 热量 */
  flame: wrap(`
    <path d="M12 2.8c3 5 6.4 6.4 6.4 10.8A6.4 6.4 0 0 1 12 21.2 6.4 6.4 0 0 1 5.6 13.6C5.6 9.2 9 7.8 12 2.8Z"
          fill="currentColor" opacity=".9"/>`),

  /* 辣度：整颗辣椒轮廓（朝右下） */
  chili: line(`
    <path d="M6.4 9.6c-.6 3.2.8 6.4 3.4 8 3.2 2 7.4 1.4 9.8-1.4 1-1.2 1.4-2.6 1.2-4-.2-1.6-1.4-2.6-2.8-2.6"/>
    <path d="M6.6 9.4c-1.6-.6-2.6-1.8-2.8-3.2 1.6.2 2.8 1 3.4 2.2"/>`),

  /* 搜索 */
  search: line(`
    <circle cx="11" cy="11" r="7"/>
    <path d="M20 20l-3.6-3.6"/>`),

  /* 点餐 / 餐盘加号 */
  order: line(`
    <circle cx="12" cy="12" r="8.4"/>
    <path d="M12 8.4v7.2M8.4 12h7.2"/>`),

  /* 购物清单 / 已点菜品 */
  cart: line(`
    <path d="M3.2 4.4h2.4l2.2 10.4a1.6 1.6 0 0 0 1.6 1.3h7.4a1.6 1.6 0 0 0 1.6-1.2l1.6-6.6H6.4"/>
    <circle cx="9.6" cy="19.6" r="1.4"/>
    <circle cx="17.2" cy="19.6" r="1.4"/>`),

  /* 加号 */
  plus: line(`<path d="M12 5.6v12.8M5.6 12h12.8"/>`),

  /* 减号 */
  minus: line(`<path d="M5.6 12h12.8"/>`),

  /* 关闭 */
  close: line(`<path d="M6.4 6.4l11.2 11.2M17.6 6.4 6.4 17.6"/>`),

  /* 对勾 */
  check: line(`<path d="m5 12.6 4.6 4.6L19 6.8"/>`),

  /* 一键生成 / 魔法棒 */
  spark: line(`
    <path d="M13.2 4.4 15 8.6l4.2 1.8-4.2 1.8-1.8 4.2-1.8-4.2L7.2 10.4l4.2-1.8 1.8-4.2Z"/>
    <path d="M5.6 15.2 6.6 17.4l2.2 1-2.2 1-1 2.2-1-2.2-2.2-1 2.2-1 .9-2.2Z"/>`),

  /* 垃圾桶（菜单里删除某道菜） */
  trash: line(`
    <path d="M4.6 6.8h14.8M9.4 6.6V4.8a1 1 0 0 1 1-1h3.2a1 1 0 0 1 1 1v1.8"/>
    <path d="M6.6 6.8 7.4 19a1.4 1.4 0 0 0 1.4 1.3h6.4a1.4 1.4 0 0 0 1.4-1.3l.8-12.2"/>
    <path d="M10.4 10.4v6M13.6 10.4v6"/>`),

  /* 品牌标识：碗 + 热气（线性，跟随 primary 色） */
  brand: wrap(`
    <g stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <path d="M3.4 11.4h17.2c0 4.5-3.8 7.8-8.6 7.8s-8.6-3.3-8.6-7.8Z"/>
      <path d="M2.2 11.4h19.6"/>
      <path d="M8.6 6.6c0-1.6 1.4-2.2 1.4-3.8M13.4 6.6c0-1.6 1.4-2.2 1.4-3.8" opacity=".7"/>
    </g>`),

  /* 调色盘（外观设置区的小标题图标） */
  palette: line(`
    <path d="M12 3.4a8.6 8.6 0 1 0 0 17.2c1.2 0 1.9-.8 1.9-1.8 0-.5-.2-.9-.5-1.3-.3-.4-.5-.8-.5-1.2 0-1 .8-1.8 1.8-1.8h1.4a3.4 3.4 0 0 0 3.4-3.4c0-4.3-4.1-7.7-7.5-7.7Z"/>
    <circle cx="8.6" cy="9.4" r="1.1" fill="currentColor" stroke="none"/>
    <circle cx="12.4" cy="7.6" r="1.1" fill="currentColor" stroke="none"/>
    <circle cx="15.6" cy="10.2" r="1.1" fill="currentColor" stroke="none"/>`)
};

/** 已收藏 / 未收藏的星标 HTML（保持尺寸随字号） */
export function starHtml(filled, size = '1em') {
  const svg = filled ? UI_ICONS.starFill : UI_ICONS.star;
  return `<span class="star-ico" style="width:${size};height:${size}">${svg}</span>`;
}

export default ICONS;
