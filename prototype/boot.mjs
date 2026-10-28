/**
 * boot.mjs — 可爱风原型注入脚本（在 demo.html 里运行）
 *
 * 分两步：
 *   A. 静态注入（改 HTML 文本）
 *      1. 资源路径修正：document.write 之后文档的 base 是 demo.html，
 *         ./js/app.js 会被解析到 /prototype/js/ 下面，必须改成站点根绝对路径
 *      2. 在原有的 main.css 之后追加 cute.css
 *   B. 运行时增强
 *      家庭页的卡片、成员行都是 app.js 渲染出来的，静态替换抓不到，
 *      所以监听 DOM，在家庭区域出现/重绘时把头像换成 Q 版形象。
 *
 * 关键坑：模块必须在 document.write 之前 import 完。
 * document.close() 会结束当前文档，之后再发起的动态 import 会直接中断，
 * 表现为「样式生效了但头像永远不出现」。
 *
 * 只在 demo.html 里引用，线上页面完全不加载它。
 */

import { cutePairHtml, memberAvatarHtml, miniPairHtml } from './avatars.js';
import { themePickerHtml, bindThemePicker } from './theme.js';

const CUTE_CSS = './cute.css';

/** 头像位放谁：默认一对「妈妈 + 爸爸」，可用 ?members=妈妈,爸爸 覆盖 */
const DEMO_MEMBERS = ['妈妈', '爸爸'];

/**
 * 是否启用「演示双人」。
 * 只在我本人这个只有 1 名成员的家庭上开启——演示数据里正好是这个家庭，
 * 用来向评审展示"两人家庭"的完整形态；真实成员 ≥2 时永远用真实名字。
 * 想关掉：地址后面加 ?demo=0。
 */
const DEMO_FAMILY = 'f_033c0944bfb6';

function pickNames(memberNamesFromPage = []) {
  const params = new URLSearchParams(location.search);
  const raw = params.get('members');
  if (raw) {
    const list = raw.split(',').map((s) => s.trim()).filter(Boolean);
    if (list.length) return list;
  }
  // 真实成员 ≥2：直接用真实名字
  if (memberNamesFromPage.length >= 2) return memberNamesFromPage;
  const demoOn = params.get('demo') !== '0';
  return demoOn ? DEMO_MEMBERS : memberNamesFromPage;
}

/* ── A. 静态注入 ─────────────────────────────────────────────── */

function patchHtml(html) {
  let out = html;
  out = out.replace(/(href|src)="\.\/(css|js)\//g, '$1="/$2/');
  out = out.replace(/<\/head>/, `  <link rel="stylesheet" href="${CUTE_CSS}" />\n</head>`);

  /* 主题切换搬进「家庭设置」后，顶栏那个日月按钮就没有第二个入口的必要了。
     原型里直接标成 hidden：app.js 的 click 绑定不受影响，只是不再露出。 */
  out = out.replace(
    /(<button class="icon-btn" id="themeToggle")/,
    '<button class="icon-btn" id="themeToggle" hidden data-moved-to-settings="1"'
  );

  /* 原型专属的可爱文案：让评审看到的「文案气质」也对 */
  out = out.replace(
    /<p class="hint-card__title">[\s\S]*?<\/p>\s*<p class="hint-card__text">[\s\S]*?<\/p>/,
    `<p class="hint-card__title">今天也要好好吃饭呀</p>
          <p class="hint-card__text">每天记得喝够 2000 ml 水，深色蔬菜吃两口，甜点留到周末～</p>`
  );
  return out;
}

/* ── B. 运行时增强 ───────────────────────────────────────────── */

function enhance() {
  /** 页面上真实渲染出的成员名（家庭页数据回填后才拿得到） */
  function pageMemberNames() {
    return [...document.querySelectorAll('.member-row__name')]
      .map((el) => el.textContent.trim().split(/\s+/)[0])
      .filter(Boolean);
  }

  function patchHero() {
    document.querySelectorAll('.family-hero').forEach((hero) => {
      if (hero.querySelector('.cute-pair')) return;
      const old = hero.querySelector('.family-hero__avatar');
      if (!old) return;

      const slot = document.createElement('span');
      slot.innerHTML = cutePairHtml(pickNames(pageMemberNames()));
      old.replaceWith(slot.firstElementChild);
    });
  }

  function patchMembers() {
    document.querySelectorAll('.member-row__avatar').forEach((el, i) => {
      if (el.dataset.cute) return;
      el.dataset.cute = '1';
      el.innerHTML = memberAvatarHtml(el.textContent.trim() || '小朋友', i + 1);
    });
  }

  /** 家庭切换列表：每项左侧放一对迷你头像 */
  function patchFamilyCards() {
    document.querySelectorAll('.family-card').forEach((card) => {
      if (card.querySelector('.family-mini-avatars')) return;
      const body = card.querySelector('.family-card__body');
      if (!body) return;
      const slot = document.createElement('span');
      slot.innerHTML = miniPairHtml(pickNames(pageMemberNames()));
      body.before(slot.firstElementChild);
    });
  }

  /**
   * 家庭设置里的「界面主题」面板。
   *
   * 挂载位置（按优先级）：
   *   1. 「我的家庭」面板之前 —— 主题是设备级偏好，不该被家庭归属，
   *      放最前面最容易找到，也不会随着家庭详情卡（重建频率高）一起被冲掉
   *   2. 家庭页根节点末尾（兜底）
   * 已经存在就跳过，避免 MutationObserver 反复重跑时重复插入。
   */
  function patchAppearancePanel() {
    const view = document.querySelector('#view-family');
    if (!view || view.querySelector('#appearancePanel')) {
      if (view) bindThemePicker(view);
      return;
    }

    const holder = document.createElement('div');
    holder.innerHTML = themePickerHtml();
    const panel = holder.firstElementChild;

    const panels = [...view.querySelectorAll(':scope > .panel')];
    // 找到「我的家庭」那一块；找不到就接在最后一个 panel 后面
    const target = panels.find((p) => /我的家庭/.test(p.querySelector('.panel__head h3')?.textContent || ''));
    if (target) {
      target.before(panel);
    } else if (panels.length) {
      panels[panels.length - 1].after(panel);
    } else {
      view.append(panel);
    }

    bindThemePicker(view);
  }

  function run() {
    patchHero();
    patchMembers();
    patchFamilyCards();
    patchAppearancePanel();
  }

  run();

  // 家庭页异步渲染完成后会整体替换 innerHTML，这里跟着重跑
  new MutationObserver(run).observe(document.body, { childList: true, subtree: true });
}

/* ── 启动 ───────────────────────────────────────────────────── */

fetch('/index.html', { cache: 'no-store' })
  .then((r) => {
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.text();
  })
  .then((html) => {
    document.open();
    document.write(patchHtml(html));
    document.close();
    enhance();
  })
  .catch((err) => {
    document.body.innerHTML =
      '<div style="padding:40px;font-family:sans-serif;color:#c94e34">' +
      '原型加载失败：' + err.message +
      '</div>';
  });
