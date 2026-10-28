/**
 * avatars.js — 可爱风格 Q 版头像（原型专用）
 *
 * 为什么是手绘 SVG 而不是图片/emoji：
 *   · 零外部依赖，随主题色变化，任意尺寸都清晰
 *   · 颜色来自 CSS 变量，深色模式自动适配
 *   · 造型可复用：家庭主卡用大号、成员行用小号、家庭列表用迷你号
 *
 * 提供的形象：
 *   mom     —— 双丸子头 + 发夹 + 蝴蝶结
 *   dad     —— 圆脸 + 侧分短发 + 小胡子
 *   kid     —— 娃娃头 + 呆毛 + 腮红
 *   grandma —— 发髻 + 圆框眼镜
 *   grandpa —— 侧边白发 + 圆框眼镜
 *   cat     —— 猫咪（成员数只有 1 人时的「独居小可爱」形象）
 *
 * 每个形象只换「发型 + 眼型」，脸部、腮红、嘴巴共用，保证一组头像画风统一。
 */

const SKIN = '#ffdcc6';
const SKIN_SHADE = '#ffc9ad';
const BLUSH = '#ff9db4';
const INK = '#5a4552';

/* 共用：脸 + 耳朵 + 腮红 + 嘴巴 */
function face({ eye = 'dot', mouth = 'smile' } = {}) {
  const eyes =
    eye === 'happy'
      ? /* 弯弯笑眼 */
        `<path d="M31 47c2.2-2.6 6-2.6 8.2 0" fill="none" stroke="${INK}" stroke-width="2.6" stroke-linecap="round"/>
         <path d="M57 47c2.2-2.6 6-2.6 8.2 0" fill="none" stroke="${INK}" stroke-width="2.6" stroke-linecap="round"/>`
      : eye === 'star'
        ? `<path d="M35 44.5l1.5 2.9 3.1.45-2.25 2.2.55 3.1-2.9-1.55-2.9 1.55.55-3.1-2.25-2.2 3.1-.45z" fill="${INK}"/>
           <path d="M61 44.5l1.5 2.9 3.1.45-2.25 2.2.55 3.1-2.9-1.55-2.9 1.55.55-3.1-2.25-2.2 3.1-.45z" fill="${INK}"/>`
        : /* 圆豆眼 + 高光 */
          `<ellipse cx="35" cy="48" rx="4.2" ry="4.8" fill="${INK}"/>
           <ellipse cx="61" cy="48" rx="4.2" ry="4.8" fill="${INK}"/>
           <circle cx="33.6" cy="46.2" r="1.5" fill="#fff"/>
           <circle cx="59.6" cy="46.2" r="1.5" fill="#fff"/>`;

  const mouthPath =
    mouth === 'open'
      ? `<path d="M43 58c1.9 3 8.1 3 10 0-1.6-1.4-8.4-1.4-10 0Z" fill="#e2647f"/>
         <path d="M45.4 59.6c1.6 1.4 3.6 1.4 5.2 0" stroke="#fff" stroke-width="1.1" fill="none" stroke-linecap="round"/>`
      : `<path d="M44.5 57.5c1.4 2.4 6.6 2.4 8 0" fill="none" stroke="${INK}" stroke-width="2.2" stroke-linecap="round"/>`;

  return `
    <ellipse cx="48" cy="50" rx="24" ry="22" fill="${SKIN}"/>
    <ellipse cx="24" cy="52" rx="4.4" ry="5.6" fill="${SKIN}"/>
    <ellipse cx="72" cy="52" rx="4.4" ry="5.6" fill="${SKIN}"/>
    <ellipse cx="26.5" cy="57" rx="5.4" ry="3.4" fill="${BLUSH}" opacity=".55"/>
    <ellipse cx="69.5" cy="57" rx="5.4" ry="3.4" fill="${BLUSH}" opacity=".55"/>
    ${eyes}
    ${mouthPath}`;
}

/* 身体：圆领小衣服，颜色由 accent 决定 */
function body(accent, collar = '#ffffff') {
  return `
    <path d="M28 84c0-8.8 9-14.5 20-14.5S68 75.2 68 84v12H28z" fill="${accent}"/>
    <path d="M41 70.5c1.2 3.4 12.8 3.4 14 0" fill="none" stroke="${collar}" stroke-width="2.4" stroke-linecap="round"/>`;
}

export const CUTE_AVATARS = {
  /* 妈妈：双丸子 + 蝴蝶结 + 珍珠发夹 */
  mom: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      ${body('#ff8fb0')}
      <circle cx="21" cy="26" r="10" fill="#7a4a52"/>
      <circle cx="75" cy="26" r="10" fill="#7a4a52"/>
      <path d="M24 44c0-14.5 10.8-24 24-24s24 9.5 24 24c0 6-1.6 10.6-4 13.6-3.6-9-11.6-14.4-20-14.4S31.6 48.6 28 57.6c-2.4-3-4-7.6-4-13.6Z" fill="#7a4a52"/>
      ${face({ eye: 'dot', mouth: 'smile' })}
      <path d="M66 30c3-3.4 8.6-2 8.6 2.6 0 3.4-4.4 6.4-8.6 9-4.2-2.6-8.6-5.6-8.6-9 0-4.6 5.6-6 8.6-2.6Z" fill="#ffd166"/>
      <circle cx="66" cy="33.6" r="2.1" fill="#fff3c4"/>
      <circle cx="24.5" cy="40" r="2.2" fill="#ffffff" opacity=".9"/>
      <circle cx="21" cy="26" r="3.4" fill="#ffd166"/>
      <circle cx="75" cy="26" r="3.4" fill="#ffd166"/>
    </svg>`,

  /* 爸爸：侧分短发 + 小胡子 */
  dad: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      ${body('#6cc5f2')}
      <path d="M23 46c0-15 11.2-25.5 25-25.5S73 31 73 46c0 3.4-.5 6.4-1.4 9-2.4-2-4-5.4-4.6-9.4-6-2.6-9.4-6.6-11-11.6-4 6.6-12 10-21 11.2-1 3.2-2.2 6.2-3.6 8.2-.9-2.3-1.4-5-1.4-7.4Z" fill="#4a3b45"/>
      ${face({ eye: 'dot', mouth: 'smile' })}
      <path d="M40.5 57.5c2.2-1.6 4.8-1.6 7 0M48.5 57.5c2.2-1.6 4.8-1.6 7 0" fill="none" stroke="#4a3b45" stroke-width="2.1" stroke-linecap="round"/>
      <path d="M44.5 63c1.4 2 5.6 2 7 0" fill="none" stroke="${INK}" stroke-width="2" stroke-linecap="round"/>
    </svg>`,

  /* 小朋友：娃娃头 + 呆毛 + 大腮红 */
  kid: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      ${body('#ffd166')}
      <path d="M23 50c0-16 11.4-27 25-27s25 11 25 27c0 4-1 7.6-2.6 10.4-2.6-9.6-11-16.4-22.4-16.4s-19.8 6.8-22.4 16.4C24 57.6 23 54 23 50Z" fill="#5b4030"/>
      <path d="M48 23c-.8-4.2 1.6-7.4 6-8.2-.4 4.2-2.6 7-6 8.2Z" fill="#5b4030"/>
      ${face({ eye: 'star', mouth: 'open' })}
      <circle cx="26.5" cy="57" r="6" fill="${BLUSH}" opacity=".62"/>
      <circle cx="69.5" cy="57" r="6" fill="${BLUSH}" opacity=".62"/>
      <path d="M60 34c2.4-2.6 6.4-2.2 7.6 1" fill="none" stroke="#ff8fb0" stroke-width="2.2" stroke-linecap="round"/>
    </svg>`,

  /* 奶奶：发髻 + 圆框眼镜 */
  grandma: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      ${body('#a78bfa')}
      <circle cx="48" cy="16" r="9" fill="#d9d4e0"/>
      <path d="M24 48c0-15 10.8-25 24-25s24 10 24 25c0 5-1.2 9.2-3.2 12.4-3.4-8.4-11-14-20.8-14s-17.4 5.6-20.8 14C25.2 57.2 24 53 24 48Z" fill="#d9d4e0"/>
      ${face({ eye: 'happy', mouth: 'smile' })}
      <circle cx="35" cy="48" r="7.2" fill="none" stroke="#8b6f7d" stroke-width="1.8" opacity=".8"/>
      <circle cx="61" cy="48" r="7.2" fill="none" stroke="#8b6f7d" stroke-width="1.8" opacity=".8"/>
      <path d="M42.2 48h11.6" stroke="#8b6f7d" stroke-width="1.8" opacity=".8"/>
    </svg>`,

  /* 爷爷：侧白发型 + 圆框眼镜 */
  grandpa: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      ${body('#5ccfb0')}
      <path d="M23 47c0-15 11.2-25.5 25-25.5S73 32 73 47c0 3.4-.5 6.4-1.4 9-2.4-2-4-5.4-4.6-9.4-6-2.6-9.4-6.6-11-11.6-4 6.6-12 10-21 11.2-1 3.2-2.2 6.2-3.6 8.2-.9-2.3-1.4-5-1.4-7.4Z" fill="#cfc9d6"/>
      ${face({ eye: 'happy', mouth: 'smile' })}
      <circle cx="35" cy="48" r="7" fill="none" stroke="#8b6f7d" stroke-width="1.8" opacity=".85"/>
      <circle cx="61" cy="48" r="7" fill="none" stroke="#8b6f7d" stroke-width="1.8" opacity=".85"/>
      <path d="M42 48h12" stroke="#8b6f7d" stroke-width="1.8" opacity=".85"/>
      <path d="M31 60c4.4 2.6 29.6 2.6 34 0" fill="none" stroke="#cfc9d6" stroke-width="4.6" stroke-linecap="round"/>
    </svg>`,

  /* 猫咪：1 人小家庭时的可爱替补 */
  cat: `
    <svg viewBox="0 0 96 100" xmlns="http://www.w3.org/2000/svg">
      <path d="M28 84c0-8.8 9-14.5 20-14.5S68 75.2 68 84v12H28z" fill="#ffb37a"/>
      <circle cx="48" cy="50" r="23" fill="#ffcd9e"/>
      <path d="M28 34l-2-14 14 7.5z" fill="#ffcd9e"/>
      <path d="M68 34l2-14-14 7.5z" fill="#ffcd9e"/>
      <path d="M30.5 30l-1-8 7.5 4.5z" fill="#ff9db4"/>
      <path d="M65.5 30l1-8-7.5 4.5z" fill="#ff9db4"/>
      <ellipse cx="36" cy="47" rx="3.6" ry="4.4" fill="${INK}"/>
      <ellipse cx="60" cy="47" rx="3.6" ry="4.4" fill="${INK}"/>
      <circle cx="34.8" cy="45.4" r="1.3" fill="#fff"/>
      <circle cx="58.8" cy="45.4" r="1.3" fill="#fff"/>
      <ellipse cx="27" cy="55" rx="5" ry="3.2" fill="${BLUSH}" opacity=".6"/>
      <ellipse cx="69" cy="55" rx="5" ry="3.2" fill="${BLUSH}" opacity=".6"/>
      <path d="M46 54h4l-2 2.6z" fill="#ff7fa5"/>
      <path d="M48 56.6c0 2-2.6 3.4-5 2.2M48 56.6c0 2 2.6 3.4 5 2.2" fill="none" stroke="${INK}" stroke-width="1.8" stroke-linecap="round"/>
      <path d="M24 52h-8M24 57l-8 2M72 52h8M72 57l8 2" stroke="#c98a5a" stroke-width="1.6" stroke-linecap="round" opacity=".8"/>
    </svg>`
};

/* 姓名/昵称 → 形象：先做关键词匹配，再按顺序兜底取不同形象 */
const KEYWORDS = [
  [/(妈妈|母亲|外婆|姥姥|mom|mama|mother)/i, 'mom'],
  [/(奶奶|婆婆|grandma|nainai)/i, 'grandma'],
  [/(爸爸|父亲|外公|姥爷|dad|papa|father)/i, 'dad'],
  [/(爷爷|公公|grandpa|yeye)/i, 'grandpa'],
  [/(宝|孩子|儿子|女儿|小|仔|娃|kid|baby|boy|girl)/i, 'kid'],
  [/(猫|喵|cat|kitty)/i, 'cat']
];

/** 兜底顺序：保证同一页里多个人不会撞脸 */
const FALLBACK = ['kid', 'mom', 'dad', 'cat', 'grandma', 'grandpa'];

/** 记录每个形象被用了几次，用于兜底时错开 */
const usedCount = new Map();

export function pickAvatarName(name = '', seedIndex = 0) {
  const raw = String(name);
  for (const [re, key] of KEYWORDS) {
    if (re.test(raw)) return key;
  }
  // 关键词没命中：按页面内出现顺序依次取，避免两个人都变成同一张脸
  if (seedIndex > 0) {
    const n = Number.isFinite(seedIndex) ? seedIndex : 1;
    return FALLBACK[(n - 1) % FALLBACK.length];
  }
  let hash = 0;
  for (let i = 0; i < raw.length; i += 1) hash = (hash * 31 + raw.charCodeAt(i)) >>> 0;
  return FALLBACK[hash % FALLBACK.length];
}

/** 取头像 SVG 字符串 */
export function avatarSvg(key) {
  return CUTE_AVATARS[key] || CUTE_AVATARS.kid;
}

/**
 * 大号头像（家庭主卡里并排两个）
 * @param {string[]} names 成员名列表，最多取前两个
 */
export function cutePairHtml(names = []) {
  const picked = names.slice(0, 2).map((n, i) => ({ name: n, key: pickAvatarName(n, i) }));

  // 只有一个人：给一个更大的单人头像 + 一只小猫咪陪伴
  if (picked.length <= 1) {
    const main = picked[0]?.key || 'kid';
    return `
      <div class="cute-pair is-lone" aria-hidden="true">
        <span class="cute-pair__spark">✦</span>
        <span class="avatar-cute avatar-cute--lone">${avatarSvg(main)}</span>
        <span class="avatar-cute avatar-cute--pet">${avatarSvg('cat')}</span>
      </div>`;
  }

  return `
    <div class="cute-pair" aria-hidden="true">
      <span class="cute-pair__spark">✦</span>
      <span class="avatar-cute avatar-cute--a">${avatarSvg(picked[0].key)}</span>
      <span class="avatar-cute avatar-cute--b">${avatarSvg(picked[1].key)}</span>
      <span class="cute-pair__heart">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-8.2-4.9-8.2-10.3A4.8 4.8 0 0 1 12 7.4a4.8 4.8 0 0 1 8.2 3.3C20.2 16.1 12 21 12 21Z"/></svg>
      </span>
    </div>`;
}

/** 成员行里的小头像 */
export function memberAvatarHtml(name, index = 0) {
  return `<span class="avatar-cute">${avatarSvg(pickAvatarName(name, index))}</span>`;
}

/** 家庭列表里的迷你双人头像 */
export function miniPairHtml(names = []) {
  const picked = names.slice(0, 2);
  const list = picked.length ? picked : ['', ''];
  return `<span class="family-mini-avatars" aria-hidden="true">${list
    .map((n, i) => `<span class="avatar-cute">${avatarSvg(pickAvatarName(n, i))}</span>`)
    .join('')}</span>`;
}
