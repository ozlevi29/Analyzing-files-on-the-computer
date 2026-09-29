"use strict";

const TOKEN = new URLSearchParams(location.hash.slice(1)).get("t") || "";
const $ = (s, el = document) => el.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let STATE = null;
let pollTimer = null;
let safetyFilter = "all";

// ---------------------------------------------------------------- utils
function fmt(bytes) {
  if (bytes == null) return "לא נמדד";
  const u = ["B", "KB", "MB", "GB", "TB"];
  let i = 0, n = bytes;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  // LRI ... PDI isolate direction so Hebrew text shows "12.7 GB", not "GB 12.7"
  const LRI = String.fromCharCode(0x2066), PDI = String.fromCharCode(0x2069);
  return LRI + (i >= 3 ? n.toFixed(1) : Math.round(n)) + " " + u[i] + PDI;
}

async function api(path, body) {
  const opts = { headers: { "X-Token": TOKEN } };
  if (body !== undefined) {
    opts.method = "POST";
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const r = await fetch(path, opts);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || "שגיאה");
  return data;
}

function toast(msg, ms = 4000) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.add("hidden"), ms);
}

const SAFETY = {
  safe: ["בטוח למחוק", "b-safe"],
  caution: ["בדוק לפני שמוחקים", "b-caution"],
  windows: ["לפנות רק דרך Windows", "b-windows"],
  keep: ["לא למחוק", "b-keep"],
};
const badge = (s) => `<span class="badge ${SAFETY[s][1]}">${SAFETY[s][0]}</span>`;

// --------------------------------------------------------- confirm modal
/** כל פעולה עוברת כאן: הסבר מה יקרה, ורק אחרי "כן" מתבצעת. */
function confirmAction(title, text, yesLabel = "כן, בצע", danger = false) {
  return new Promise((resolve) => {
    $("#mTitle").textContent = title;
    $("#mText").textContent = text;
    const yes = $("#mYes"), no = $("#mNo"), modal = $("#modal");
    yes.textContent = yesLabel;
    yes.className = "btn " + (danger ? "danger" : "primary");
    modal.classList.remove("hidden");
    no.focus();
    const done = (v) => {
      modal.classList.add("hidden");
      yes.onclick = no.onclick = modal.onclick = document.onkeydown = null;
      resolve(v);
    };
    yes.onclick = () => done(true);
    no.onclick = () => done(false);
    modal.onclick = (e) => { if (e.target === modal) done(false); };
    document.onkeydown = (e) => { if (e.key === "Escape") done(false); };
  });
}

// ------------------------------------------------------------- header
function renderDisk(d) {
  if (!d) return;
  const pct = d.used / d.total * 100;
  const freePct = 100 - pct;
  const cls = freePct < 10 ? "crit" : freePct < 20 ? "warn" : "";
  $("#diskbox").innerHTML = `
    <div class="disk-row"><b>כונן ${esc(d.root)}</b><span class="num">${fmt(d.free)} פנויים מתוך ${fmt(d.total)} (${freePct.toFixed(0)}% פנוי)</span></div>
    <div class="disk-bar ${cls}"><div style="width:${pct.toFixed(1)}%"></div></div>`;
}

function renderAdmin(isAdmin) {
  const b = $("#adminBadge");
  b.className = "badge " + (isAdmin ? "b-safe" : "b-neutral");
  b.textContent = isAdmin ? "פועל כמנהל" : "פועל כמשתמש רגיל";
  b.title = isAdmin ? "" : "חלק מהניקויים דורשים להפעיל את הכלי עם start-as-admin.bat";
}

// ------------------------------------------------------------- polling
async function refresh() {
  try {
    STATE = await api("/api/state");
  } catch (e) {
    return;
  }
  renderDisk(STATE.disk);
  renderAdmin(STATE.admin);
  const s = STATE.scan;
  if (s.status === "running") {
    showOnly("progress");
    $("#progLabel").textContent = `שלב ${s.stage || 1} מתוך 4: ${s.stage_label || "מתחיל"}`;
    $("#progBar").style.width = (s.pct || 0) + "%";
    $("#progPct").textContent = (s.pct || 0) + "%";
    $("#progFiles").textContent = s.files ? `${s.files.toLocaleString()} קבצים, ${fmt(s.scanned)}` : "";
    $("#progDetail").textContent = s.detail || "";
    $("#cancelBtn").classList.toggle("hidden", s.stage !== 3);
    schedule(700);
  } else if (s.status === "done" && STATE.results) {
    stopPoll();
    showOnly("results");
    renderAll();
    const tab = new URLSearchParams(location.hash.slice(1)).get("tab");
    if (tab) openTab(tab);
    const info = new URLSearchParams(location.hash.slice(1)).get("info");
    if (info) showStepInfo(info);
  } else if (s.status === "error") {
    stopPoll();
    showOnly("intro");
    toast("הסריקה נכשלה: " + s.error, 8000);
  } else {
    showOnly("intro");
  }
}
function schedule(ms) { stopPoll(); pollTimer = setTimeout(refresh, ms); }
function stopPoll() { clearTimeout(pollTimer); }
function showOnly(id) {
  for (const x of ["intro", "progress", "results"]) $("#" + x).classList.toggle("hidden", x !== id);
}

// ----------------------------------------------------------------- tabs
document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => openTab(t.dataset.tab)));
function openTab(name, anchor) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tabpane").forEach((p) => p.classList.toggle("hidden", p.id !== "tab-" + name));
  if (anchor) {
    const el = document.getElementById(anchor);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  } else window.scrollTo({ top: 0 });
}

function renderAll() {
  renderReport();
  renderClean();
  renderDiskTab();
  renderSystem();
}

// --------------------------------------------------------------- report
const SEV = { high: ["בעיה חמורה", "b-keep"], medium: ["כדאי לטפל", "b-caution"], low: ["לתשומת לבך", "b-windows"], ok: ["תקין", "b-safe"] };

function renderReport() {
  const R = STATE.results;
  const f = R.findings;
  const issues = f.filter((x) => x.severity === "high" || x.severity === "medium");
  const mem = R.diag.memory;
  const safeTotal = R.rules.filter((r) => r.safety === "safe" && r.action === "clean").reduce((a, r) => a + (r.size || 0), 0);
  let lead;
  if (!issues.length) lead = "לא נמצאו בעיות משמעותיות. למטה יש כמה טיפים שיכולים לעזור.";
  else lead = `נמצאו ${issues.length} סיבות עיקריות לאיטיות. הן מסודרות מהחשובה ביותר. ` +
    `ליד כל צעד יש כפתור "טפל", ולפני כל פעולה יופיע הסבר ותתבקש לאשר.`;

  $("#tab-report").innerHTML = `
    <div class="summary">
      <div class="stat"><div class="k">מקום פנוי בכונן C</div><div class="v num">${fmt(STATE.disk.free)}</div></div>
      <div class="stat"><div class="k">אפשר לפנות בבטחה</div><div class="v num">${fmt(safeTotal)}</div></div>
      <div class="stat"><div class="k">זיכרון בשימוש</div><div class="v num">${mem.load}%</div></div>
      <div class="stat"><div class="k">מעבד בזמן הסריקה</div><div class="v num">${R.diag.processes.total_cpu}%</div></div>
    </div>
    <p class="lead">${esc(lead)}</p>
    ${f.map(renderFinding).join("")}`;

  $("#tab-report").querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => doStep(b.dataset.step)));
  $("#tab-report").querySelectorAll("[data-info]").forEach((b) => b.addEventListener("click", () => showStepInfo(b.dataset.info)));
}

// ------------------------------------------------------- detailed info popup
const li = (arr, cls) => arr && arr.length ? `<ul class="${cls}">${arr.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "";
const sec = (title, html) => html ? `<div class="info-sec"><h4>${esc(title)}</h4>${html}</div>` : "";
const para = (t) => t ? `<p>${esc(t)}</p>` : "";

function verdictBox(text, safety) {
  if (!text) return "";
  const warn = safety && safety !== "safe";
  return `<div class="verdict ${warn ? "warn" : ""}"><b>זה יהרוס לי משהו?</b><span>${esc(text)}</span></div>`;
}

function howItRuns(r) {
  if (r.action === "clean") {
    let t = "הקבצים נמחקים לצמיתות, לא דרך סל המחזור, כי הם נבנים מחדש לבד. ";
    t += "קבצים שתוכנה פתוחה משתמשת בהם כרגע ידולגו, בלי שום נזק לתוכנה.";
    if (r.min_age_days) t += ` קבצים שנוצרו או שונו ב-${r.min_age_days === 1 ? "24 השעות" : r.min_age_days + " הימים"} האחרונים לא נמחקים.`;
    return t;
  }
  if (r.action === "recycle") return "סל המחזור מתרוקן דרך הפונקציה הרשמית של Windows, בדיוק כמו לחיצה ימנית על הסל > \"רוקן את סל המחזור\".";
  if (r.action === "command") return `ייפתח חלון פקודה${r.admin ? " (Windows יבקש אישור מנהל)" : ""} שיריץ את הפקודה הרשמית:\n${r.command}\nהכלי לא מוחק את הקבצים בעצמו: Windows או הכלי הרשמי עושים את זה.`;
  if (r.action === "open") return "ייפתח מסך של Windows. שום דבר לא יימחק אוטומטית. אתה מבצע את הפעולה במסך שנפתח.";
  return "";
}

function ruleInfoHtml(r) {
  const d = r.details || {};
  const paths = r.path_sizes && r.path_sizes.length
    ? `<div class="path-wrap"><table class="path-tbl">${r.path_sizes.map((p) =>
        `<tr><td class="mono">${esc(p.path)}</td><td class="num">${fmt(p.size)}</td></tr>`).join("")}</table></div>` : "";
  return verdictBox(d.verdict, r.safety) +
    sec("מה זה?", para(r.what) + (d.details ? `<p style="margin-top:6px">${esc(d.details)}</p>` : "")) +
    sec(r.action === "command" || r.action === "open" ? "מה נמצא שם עכשיו" : "מה בדיוק יימחק, ומאיפה", paths) +
    sec("איך זה מתבצע", `<div class="howbox" style="white-space:pre-wrap">${esc(howItRuns(r))}</div>`) +
    sec("מה לא ייפגע", li(d.not_affected, "ok-list")) +
    sec("מה כן ישתנה אחרי", li(d.after, "chg-list")) +
    sec("ואם אתחרט?", para(d.undo));
}

function openInfo(title, bodyHtml, actLabel, onAct) {
  $("#iTitle").textContent = title;
  $("#iBody").innerHTML = bodyHtml;
  $("#iBody").scrollTop = 0;
  const modal = $("#info"), act = $("#iAct");
  act.classList.toggle("hidden", !actLabel);
  act.textContent = actLabel || "";
  modal.classList.remove("hidden");
  $("#iNo").focus();
  const close = () => {
    modal.classList.add("hidden");
    act.onclick = $("#iNo").onclick = $("#iClose").onclick = modal.onclick = document.onkeydown = null;
  };
  act.onclick = () => { close(); onAct && onAct(); };
  $("#iNo").onclick = $("#iClose").onclick = close;
  modal.onclick = (e) => { if (e.target === modal) close(); };
  document.onkeydown = (e) => { if (e.key === "Escape") close(); };
}

function showStepInfo(id) {
  const s = findStep(id);
  if (!s) return;
  let html = "";
  if (s.info_rules && s.info_rules.length) {
    const rs = s.info_rules.map((rid) => STATE.results.rules.find((r) => r.id === rid)).filter(Boolean);
    if (rs.length === 1) {
      html = ruleInfoHtml(rs[0]);
    } else {
      const total = rs.reduce((a, r) => a + (r.size || 0), 0);
      html = verdictBox("לא. כל הסוגים ברשימה הם קבצים זמניים, מטמונים וקבצי קריסה. אף אחד מהם לא מכיל מידע אישי, " +
          "וכל תוכנה יוצרת מחדש את מה שהיא צריכה.", "safe") +
        sec("מה הפעולה עושה", para(`הפעולה מנקה ${rs.length} סוגים של קבצי פסולת, בסך הכול ${fmt(total)}. ` +
          "לחץ על כל סוג כדי לראות מה הוא, מאילו תיקיות בדיוק הוא נמחק, ומה לא ייפגע."))+
        sec("מה לא ייפגע בשום מקרה", li([
          "המסמכים, התמונות, הסרטונים וההורדות שלך",
          "התוכנות המותקנות. כולן ממשיכות לעבוד",
          "בדפדפנים: סיסמאות, סימניות, היסטוריה, התחברויות לאתרים ותוספים",
          "פרויקטים וקוד (CapCut, Android, VS Code, Node)",
          "Windows, עדכונים מותקנים והגדרות"], "ok-list")) +
        sec("לפני שמתחילים", para("כדאי לסגור את Chrome, Edge, CapCut ו-VS Code. זה לא חובה, אבל כך יימחקו גם הקבצים שהם מחזיקים פתוחים עכשיו.")) +
        rs.map((r) => `<details class="rule-sec"><summary><span>${esc(r.title)}</span>${badge(r.safety)}<span class="sz">${fmt(r.size)}</span></summary>
          <div class="rule-sec-body">${ruleInfoHtml(r)}</div></details>`).join("");
    }
  } else if (s.info) {
    const d = s.info;
    html = verdictBox(d.verdict, "safe") +
      sec("מה זה?", para(d.details)) +
      sec("איפה זה מוגדר", d.where ? `<div class="path-wrap"><table class="path-tbl">${d.where.map((w) => `<tr><td class="mono">${esc(w)}</td></tr>`).join("")}</table></div>` : "") +
      sec("מה לא ייפגע", li(d.not_affected, "ok-list")) +
      sec("מה כן ישתנה אחרי", li(d.after, "chg-list")) +
      sec("ואם אתחרט?", para(d.undo));
  }
  const canAct = !s.disabled_reason;
  openInfo(s.title, html, canAct ? s.button : "", () => doStep(id));
}

function showRuleInfo(id) {
  const r = STATE.results.rules.find((x) => x.id === id);
  if (!r) return;
  const act = ACTION_LABEL[r.action] && !r.needs_admin_now && !(r.action === "clean" && !r.size) ? ACTION_LABEL[r.action] : "";
  openInfo(r.title, ruleInfoHtml(r), act, () => doRule(id));
}

function renderFinding(f) {
  let n = 0;
  const steps = (f.steps || []).map((s) => {
    n++;
    const done = STATE.done_steps[s.id];
    const res = done ? resultText(done) : "";
    const act = s.disabled_reason
      ? `<span class="note">${esc(s.disabled_reason)}</span>`
      : `<button class="btn ${s.action.type === "goto" ? "ghost" : "primary"} small" data-step="${esc(s.id)}">${done ? "שוב" : esc(s.button)}</button>`;
    const hasInfo = s.info || (s.info_rules && s.info_rules.length);
    const btn = `<div class="step-actions">${hasInfo ? `<button class="i-btn" data-info="${esc(s.id)}" title="מידע מפורט" aria-label="מידע מפורט על ${esc(s.title)}">i</button>` : ""}${act}</div>`;
    return `<div class="step ${done ? "done" : ""}">
      <div class="step-n">${done ? "✓" : n}</div>
      <div class="step-body">
        <div class="step-title">${esc(s.title)}</div>
        <div class="step-desc">${esc(s.desc)}</div>
        ${res ? `<div class="step-result">${esc(res)}</div>` : ""}
      </div>
      ${btn}
    </div>`;
  }).join("");
  const extra = f.extra && f.extra.length ? `<div class="small muted" style="margin-top:6px">נפתחות עכשיו: ${esc(f.extra.join(", "))}</div>` : "";
  return `<article class="finding sev-${f.severity}">
    <div class="f-head">
      <div style="flex:1">
        <h3>${esc(f.title)}</h3>
        <p class="f-why">${esc(f.why)}</p>
        ${extra}
      </div>
      <span class="badge ${SEV[f.severity][1]}">${SEV[f.severity][0]}</span>
    </div>
    ${steps ? `<div class="steps"><div class="steps-title">צעדים לטיפול</div>${steps}</div>` : ""}
  </article>`;
}

function resultText(r) {
  if (r.freed != null) return `בוצע. פונו ${fmt(r.freed)}` + (r.skipped ? ` (${r.skipped.toLocaleString()} קבצים בשימוש דולגו)` : "");
  if (r.recycled != null) return `הועבר לסל המחזור (${fmt(r.recycled)}). כדי לפנות את המקום בפועל, רוקן את סל המחזור.`;
  return r.message || "בוצע";
}

function findStep(id) {
  for (const f of STATE.results.findings) for (const s of f.steps || []) if (s.id === id) return s;
  return null;
}

async function doStep(id) {
  const s = findStep(id);
  if (!s) return;
  if (s.action.type === "goto") return openTab(s.action.tab, s.action.anchor);
  const ok = await confirmAction("האם אתה בטוח? " + s.title, s.confirm, "כן, בצע", s.action.type === "restart");
  if (!ok) return;
  toast("מבצע…", 60000);
  try {
    const r = await api("/api/fix", { step: id });
    STATE.done_steps[id] = r.result;
    if (r.disk) { STATE.disk = r.disk; renderDisk(r.disk); }
    toast(resultText(r.result), 6000);
    renderReport();
  } catch (e) {
    toast("לא הצליח: " + e.message, 8000);
  }
}

// ------------------------------------------------------ what can be deleted
const CAT_ORDER = ["system", "browser", "apps", "dev", "big"];
const ACTION_LABEL = { clean: "נקה", recycle: "רוקן", command: "הפעל", open: "פתח" };

function renderClean() {
  const R = STATE.results;
  const counts = { all: R.rules.length };
  for (const r of R.rules) counts[r.safety] = (counts[r.safety] || 0) + 1;
  const chips = [["all", "הכל"], ["safe", "בטוח למחוק"], ["caution", "בדוק לפני"], ["windows", "דרך Windows"], ["keep", "לא למחוק"]]
    .map(([k, l]) => `<button class="chip ${safetyFilter === k ? "on" : ""}" data-f="${k}">${l} (${counts[k] || 0})</button>`).join("");

  let html = `<p class="lead">כל מקום שהכלי מכיר במחשב, מה גודלו, מה זה, והאם בטוח למחוק. ממוין מהגדול לקטן בכל קבוצה.</p>
    <div class="filters">${chips}</div>`;
  for (const cat of CAT_ORDER) {
    const items = R.rules.filter((r) => r.category === cat && (safetyFilter === "all" || r.safety === safetyFilter))
      .sort((a, b) => (b.size || 0) - (a.size || 0));
    if (!items.length) continue;
    html += `<div class="cat-title">${esc(items[0].category_label)}</div>` + items.map(ruleCard).join("");
  }
  if (safetyFilter === "all" || safetyFilter === "caution") html += downloadsSection(R.downloads);
  $("#tab-clean").innerHTML = html;
  $("#tab-clean").querySelectorAll("[data-f]").forEach((c) => c.addEventListener("click", () => { safetyFilter = c.dataset.f; renderClean(); }));
  $("#tab-clean").querySelectorAll("[data-rule]").forEach((b) => b.addEventListener("click", () => doRule(b.dataset.rule)));
  $("#tab-clean").querySelectorAll("[data-rinfo]").forEach((b) => b.addEventListener("click", () => showRuleInfo(b.dataset.rinfo)));
  bindFileButtons($("#tab-clean"));
}

function ruleCard(r) {
  const act = ACTION_LABEL[r.action];
  let btn = "";
  if (act) {
    if (r.needs_admin_now) btn = `<span class="note small muted">דורש להפעיל את הכלי כמנהל (start-as-admin.bat)</span>`;
    else if (r.action === "clean" && !r.size) btn = `<span class="small muted">ריק, אין מה לנקות</span>`;
    else btn = `<button class="btn ${r.safety === "safe" ? "primary" : ""} small" data-rule="${esc(r.id)}">${act}</button>`;
  }
  const paths = r.paths && r.paths.length
    ? `<details class="paths"><summary>מיקום (${r.paths.length})</summary><ul>${r.paths.map((p) => `<li class="mono">${esc(p)}</li>`).join("")}</ul></details>` : "";
  return `<div class="card">
    <div class="card-head"><h3>${esc(r.title)}</h3>${badge(r.safety)}<span class="size">${fmt(r.size)}</span>
      <button class="i-btn" data-rinfo="${esc(r.id)}" title="מידע מפורט" aria-label="מידע מפורט על ${esc(r.title)}">i</button></div>
    <dl class="explain">
      <dt>מה זה?</dt><dd>${esc(r.what)}</dd>
      <dt>האם בטוח למחוק?</dt><dd>${esc(r.if_deleted)}</dd>
      <dt>איך מנקים</dt><dd>${esc(r.how)}</dd>
    </dl>
    ${paths}
    <div class="card-actions">${btn}</div>
  </div>`;
}

async function doRule(id) {
  const r = STATE.results.rules.find((x) => x.id === id);
  let text;
  if (r.action === "clean") {
    text = `יימחק לצמיתות (לא דרך סל המחזור) התוכן של:\n${r.paths.slice(0, 15).map((p) => "• " + p).join("\n")}` +
      (r.paths.length > 15 ? `\n…ועוד ${r.paths.length - 15}` : "") +
      `\n\nגודל: ${fmt(r.size)}\n\nמה המשמעות: ${r.if_deleted}`;
  } else if (r.action === "recycle") {
    text = `כל הפריטים בסל המחזור (${fmt(r.size)}) יימחקו לצמיתות, ולא יהיה אפשר לשחזר אותם.\n\nאם אתה לא בטוח מה יש שם, לחץ "ביטול" ופתח קודם את סל המחזור.`;
  } else if (r.action === "command") {
    text = `ייפתח חלון פקודה${r.admin ? " עם בקשת הרשאות מנהל" : ""} שיריץ:\n${r.command}\n\nמה המשמעות: ${r.if_deleted}`;
  } else {
    text = `ייפתח מסך של Windows. שום דבר לא יימחק אוטומטית.\n\nמה לעשות שם: ${r.how}`;
  }
  const ok = await confirmAction("האם אתה בטוח? " + r.title, text);
  if (!ok) return;
  toast("מבצע…", 60000);
  try {
    const res = await api("/api/rule", { rule: id });
    if (res.disk) { STATE.disk = res.disk; renderDisk(res.disk); }
    if (res.result.freed != null && r.action !== "command") r.size = Math.max(0, (r.size || 0) - res.result.freed);
    toast(resultText(res.result), 6000);
    renderClean();
  } catch (e) {
    toast("לא הצליח: " + e.message, 8000);
  }
}

function downloadsSection(list) {
  if (!list || !list.length) return "";
  return `<div class="cat-title">תיקיית ההורדות: קבצים שלא נגעת בהם יותר מחודש</div>
    <p class="section-sub">הכלי לא מוחק כאן כלום לבד. בדוק כל קובץ, ואם הוא מיותר העבר אותו לסל המחזור.</p>
    ${fileTable(list, true)}`;
}

// ------------------------------------------------------ files / folders
function fileTable(list, showDate) {
  return `<table class="tbl"><thead><tr><th>קובץ</th><th>גודל</th><th>האם בטוח למחוק</th><th></th></tr></thead><tbody>
    ${list.map((x) => `<tr>
      <td><div class="mono small">${esc(x.path)}</div>${showDate && x.mtime ? `<div class="small muted">שונה לאחרונה: ${new Date(x.mtime * 1000).toLocaleDateString("he-IL")}</div>` : ""}</td>
      <td class="num">${fmt(x.size)}</td>
      <td>${badge(x.safety)}<div class="small">${esc(x.hint)}</div></td>
      <td class="act">
        <button class="btn small ghost" data-open="${esc(x.path)}">פתח מיקום</button>
        ${x.safety === "keep" ? "" : `<button class="btn small" data-recycle="${esc(x.path)}" data-size="${x.size}" data-hint="${esc(x.hint)}">לסל המחזור</button>`}
      </td></tr>`).join("")}
  </tbody></table>`;
}

function bindFileButtons(root) {
  root.querySelectorAll("[data-open]").forEach((b) => b.addEventListener("click", async () => {
    const ok = await confirmAction("פתיחת מיקום", `ייפתח סייר הקבצים במיקום:\n${b.dataset.open}\n\nשום דבר לא יימחק.`, "פתח");
    if (!ok) return;
    api("/api/open_location", { path: b.dataset.open }).catch((e) => toast(e.message));
  }));
  root.querySelectorAll("[data-recycle]").forEach((b) => b.addEventListener("click", async () => {
    const p = b.dataset.recycle;
    const ok = await confirmAction("להעביר לסל המחזור?",
      `הקובץ יועבר לסל המחזור:\n${p}\nגודל: ${fmt(+b.dataset.size)}\n\nעל הקובץ: ${b.dataset.hint}\n\n` +
      `אפשר לשחזר אותו מסל המחזור עד שתרוקן אותו. המקום בדיסק יתפנה רק אחרי ריקון הסל.\n` +
      `שים לב: קובץ גדול מהמקום שמוקצה לסל המחזור עלול להימחק לצמיתות.`, "כן, העבר לסל המחזור");
    if (!ok) return;
    try {
      const r = await api("/api/recycle_file", { path: p });
      b.closest("tr").remove();
      if (r.disk) renderDisk(r.disk);
      toast(resultText(r.result), 6000);
    } catch (e) { toast("לא הצליח: " + e.message, 8000); }
  }));
  root.querySelectorAll("[data-nm]").forEach((b) => b.addEventListener("click", async () => {
    const p = b.dataset.nm;
    const ok = await confirmAction("למחוק את node_modules?",
      `התיקייה תימחק לצמיתות (לא דרך סל המחזור, כי יש בה עשרות אלפי קבצים):\n${p}\nגודל: ${fmt(+b.dataset.size)}\n\n` +
      `מה המשמעות: הקוד של הפרויקט לא נפגע. כשתחזור לעבוד על הפרויקט, הרץ בתיקייה שלו npm install (או pnpm install / yarn) ` +
      `כדי להוריד את החבילות מחדש. אל תמחק אם הפרויקט רץ עכשיו.`, "כן, מחק", true);
    if (!ok) return;
    toast("מוחק…", 60000);
    try {
      const r = await api("/api/delete_nm", { path: p });
      b.closest("tr").remove();
      if (r.disk) renderDisk(r.disk);
      toast(resultText(r.result), 6000);
    } catch (e) { toast("לא הצליח: " + e.message, 8000); }
  }));
}

function renderDiskTab() {
  const D = STATE.results.disk;
  const el = $("#tab-disk");
  if (!D) {
    el.innerHTML = `<div class="empty">הסריקה המלאה של הכונן לא הופעלה. לחץ "סריקה חוזרת" וסמן "סריקה מלאה".</div>`;
    return;
  }
  const nmTotal = D.node_modules.reduce((a, x) => a + x.size, 0);
  el.innerHTML = `
    <h2 class="section-title">איפה המקום הלך?</h2>
    <p class="section-sub">תיקיות מעל 200 MB בכונן. לחץ על החץ כדי להיכנס פנימה. ${D.denied ? `(${D.denied.toLocaleString()} תיקיות מערכת לא נסרקו בגלל הרשאות.)` : ""}</p>
    <div class="tree" id="treeRoot"></div>

    <h2 class="section-title" id="large">קבצים גדולים (מעל 500 MB)</h2>
    <p class="section-sub">ליד כל קובץ יש הסבר אם בטוח למחוק אותו. הכלי לא מוחק קבצים אישיים לבד: אתה מחליט, והקובץ עובר לסל המחזור.</p>
    ${D.large_files.length ? fileTable(D.large_files) : `<div class="empty">לא נמצאו קבצים מעל 500 MB.</div>`}

    <h2 class="section-title" id="nm">תיקיות node_modules (${fmt(nmTotal)})</h2>
    <p class="section-sub">חבילות של פרויקטי JavaScript. אפשר למחוק בפרויקטים שאתה לא עובד עליהם, ולשחזר בכל רגע עם npm install.</p>
    ${D.node_modules.length ? `<table class="tbl"><thead><tr><th>פרויקט</th><th>גודל</th><th></th></tr></thead><tbody>
      ${D.node_modules.map((x) => `<tr><td class="mono small">${esc(x.project)}</td><td class="num">${fmt(x.size)}</td>
        <td class="act"><button class="btn small ghost" data-open="${esc(x.path)}">פתח מיקום</button>
        <button class="btn small" data-nm="${esc(x.path)}" data-size="${x.size}">מחק</button></td></tr>`).join("")}
    </tbody></table>` : `<div class="empty">לא נמצאו.</div>`}`;
  bindFileButtons(el);
  loadTree(D.root, $("#treeRoot"), D.total);
}

async function loadTree(path, container, parentSize) {
  const kids = await api("/api/tree?path=" + encodeURIComponent(path));
  if (!kids.length) { container.innerHTML = `<div class="small muted" style="padding:4px 12px">אין תת-תיקיות גדולות.</div>`; return; }
  container.innerHTML = kids.map((k, i) => `
    <div class="node">
      <div class="node-row">
        <button class="twisty" data-i="${i}" ${k.has_children ? "" : "disabled style='visibility:hidden'"} aria-label="פתח">◀</button>
        <span class="node-name" title="${esc(k.path)}">${esc(k.name)}</span>
        <span class="node-size">${fmt(k.size)}</span>
        <span class="node-bar"><div style="width:${Math.min(100, k.size / parentSize * 100).toFixed(1)}%"></div></span>
        <span class="node-hint">${esc(k.hint)}</span>
      </div>
      <div class="children hidden"></div>
    </div>`).join("");
  container.querySelectorAll(".twisty").forEach((b) => b.addEventListener("click", async () => {
    const k = kids[+b.dataset.i];
    const ch = b.closest(".node").querySelector(".children");
    const open = ch.classList.toggle("hidden") === false;
    b.textContent = open ? "▼" : "◀";
    if (open && !ch.dataset.loaded) { ch.dataset.loaded = 1; await loadTree(k.path, ch, k.size); }
  }));
}

// --------------------------------------------------------------- system
function renderSystem() {
  const d = STATE.results.diag;
  const p = d.processes;
  const net = d.network;
  $("#tab-system").innerHTML = `<div class="grid2">
    <div class="card"><h3>זיכרון</h3><div class="kv" style="margin-top:8px">
      <span class="k">בשימוש</span><span class="num">${d.memory.load}% (${fmt(d.memory.total - d.memory.avail)} מתוך ${fmt(d.memory.total)})</span>
      <span class="k">זמן מאז הפעלה</span><span class="num">${(d.uptime_h / 24).toFixed(1)} ימים</span>
      <span class="k">חשמל</span><span>${d.power.on_battery ? "על סוללה (" + d.power.battery + "%)" : "מחובר לחשמל"}</span>
      <span class="k">תוכנית חשמל</span><span class="small">${esc(d.power.scheme)}</span>
    </div></div>
    <div class="card"><h3>דיסק ורשת</h3><div class="kv" style="margin-top:8px">
      ${d.disks.map((x) => `<span class="k">${esc(x.name)}</span><span>${esc(x.media)}, תקינות: ${x.health === "Healthy" ? "תקין" : esc(x.health)}</span>`).join("")}
      <span class="k">Wi-Fi</span><span>${net.wifi_signal != null ? net.wifi_signal + "% " + (net.wifi_band || "") : "לא מחובר ב-Wi-Fi"}</span>
      <span class="k">זמן תגובה</span><span class="num">${net.avg_ms != null ? `ממוצע ${net.avg_ms}ms, מקסימום ${net.max_ms}ms` : "אין חיבור"}</span>
      <span class="k">אנטי-וירוס</span><span>${d.antivirus.map((a) => esc(a.name) + (a.active ? " (פעיל)" : "")).join(", ")}</span>
    </div></div>
  </div>
  <h2 class="section-title">מי תופס הכי הרבה זיכרון</h2>
  <table class="tbl"><thead><tr><th>תוכנה</th><th>זיכרון</th><th>תהליכים</th><th>מעבד</th></tr></thead><tbody>
    ${p.by_mem.map((x) => `<tr><td>${esc(x.name)}</td><td class="num">${fmt(x.mem)}</td><td class="num">${x.count}</td><td class="num">${x.cpu_pct}%</td></tr>`).join("")}
  </tbody></table>
  <h2 class="section-title">תוכנות שנפתחות עם המחשב</h2>
  <table class="tbl"><thead><tr><th>שם</th><th>מצב</th><th>המלצה</th></tr></thead><tbody>
    ${d.startup.map((s) => `<tr><td>${esc(s.display)}<div class="mono small muted">${esc(s.command)}</div></td>
      <td>${s.enabled ? "פעיל" : "מושבת"}</td><td class="small">${esc(s.advice || "")}</td></tr>`).join("")}
  </tbody></table>`;
}

// -------------------------------------------------------------- buttons
async function startScan(deep) {
  const ok = await confirmAction("להתחיל סריקה?",
    "הכלי יבדוק זיכרון, מעבד, תוכנות הפעלה, רשת ותיקיות מוכרות" + (deep ? ", ויסרוק את כל הקבצים בכונן C (כמה דקות)" : "") +
    ".\n\nהסריקה רק קוראת מידע. שום דבר לא נמחק ולא משתנה.", "התחל סריקה");
  if (!ok) return;
  try {
    await api("/api/scan", { deep });
    showOnly("progress");
    refresh();
  } catch (e) { toast(e.message); }
}
$("#scanBtn").addEventListener("click", () => startScan($("#deepChk").checked));
$("#rescanBtn").addEventListener("click", () => { showOnly("intro"); });
$("#cancelBtn").addEventListener("click", async () => {
  const ok = await confirmAction("לדלג על הסריקה המלאה?", "הסריקה המלאה של הכונן תיעצר. הדוח יוצג עם מה שנסרק עד עכשיו. רשימת הקבצים הגדולים תהיה חלקית.", "כן, דלג");
  if (ok) api("/api/cancel", {});
});
$("#quitBtn").addEventListener("click", async () => {
  const ok = await confirmAction("לצאת מהתוכנה?", "התוכנה תיסגר. אפשר לפתוח אותה שוב עם start.bat.", "יציאה");
  if (!ok) return;
  await api("/api/quit", {}).catch(() => {});
  document.body.innerHTML = `<main><div class="panel intro"><h2>התוכנה נסגרה</h2><p>אפשר לסגור את הלשונית.</p></div></main>`;
});

if (!TOKEN) {
  document.body.innerHTML = `<main><div class="panel intro"><h2>חסר מפתח גישה</h2><p>פתח את התוכנה דרך start.bat. הכתובת הנכונה מודפסת בחלון השחור.</p></div></main>`;
} else {
  refresh();
}
