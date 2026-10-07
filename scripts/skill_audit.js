#!/usr/bin/env node
// skill_audit.js — 自进化门禁 / 上下文成本审计器
//
// 为什么存在：本技能是「活文档」，每次自进化都要往 references/ 里加知识、删错误。
// 如果没有测量，加知识就没有上限，文档很快膨胀到读不动、检索不到、命中率崩掉。
// 本脚本把《references/自进化与维护.md》里的规则变成四道可执行的闸：
//
//   1. 引用断链   —— SKILL.md / references 里提到的文件是否真实存在
//   2. 负向声明   —— 全库有无「已废弃 / 勿再使用 / 已推翻 / 曾要求」类痕迹
//   3. 字体白名单 —— 全库只允许 Noto Sans SC / LXGW WenKai GB两个名字，
//      出现在任何位置（font=、正文、表格、注释、反例）都算违规，无豁免
//   4. 体量红线—— 常驻层 SKILL.md（字符数）与单篇 references/*.md 是否超线
//
// 用法：
//   node scripts/skill_audit.js            摘要（默认）
//   node scripts/skill_audit.js --top      附体量 TOP 8 与断链明细
//   node scripts/skill_audit.js --json     机器可读
//   node scripts/skill_audit.js --save     记一条历史，作为下次对比基准
//
// 退出码：0 全过 · 1 有红灯（push.js 会据此拒绝推送）

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname, "..");

// ── 红线（与《自进化与维护.md》§九 必须同步改）────────────────────────
// 所有文档统一 10000 字符红线（SKILL.md 与 references/*.md 同限）。
// 超了就拆分，不上调阈值——见《自进化与维护.md》§九。
const BUDGET = {
  docChars: 10000, // SKILL.md 与每篇 references/*.md 的字符数上限
};

// 「整篇读」阈值：超过此值，SKILL.md 路由表应标注「先 Grep 局部读」。
// 必须小于 docChars，否则永远不会触发。
const GREP_FIRST_CHARS = 8000;

// ── 字体白名单（与 SKILL.md 硬约束同步）──────────────────────────────
const FONT_ALLOW = new Set(["Noto Sans SC", "LXGW WenKai GB"]);

// ── 负向声明词表（《自进化与维护.md》§三）──────────────────────────────
// 本文件必须引述这些词形才能说明禁令 ⇒ 自身豁免
const NEGATIVE_WORDS = ["已废弃", "勿再使用", "已推翻", "曾要求", "已失效", "不再支持"];
const NEGATIVE_EXEMPT = new Set(["自进化与维护.md", "skill_audit.js"]);

const HISTORY_FILE = path.join(__dirname, ".skill-audit-history.jsonl");

function readText(p) {
  try {
    return fs.readFileSync(p, "utf-8");
  } catch {
    return "";
  }
}

function allDocs() {
  // 扫整个技能目录（排除 .git / 产物目录），不只references/ 与 scripts/——
  // 否则根目录下的 .md 会成为藏违规字体名的盲区。
  const SKIP_DIRS = new Set([".git", "node_modules", "__pycache__", "media", "_media", "_backup"]);
  const docs = [];
  const walkAll = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) {
        if (SKIP_DIRS.has(e.name)) continue;
        walkAll(path.join(dir, e.name));
      } else if (/\.(md|py|js)$/.test(e.name)) {
        docs.push(path.join(dir, e.name));
      }
    }
  };
  walkAll(SKILL_DIR);
  return docs.filter((f) => fs.existsSync(f));
}

const rel = (p) => path.relative(SKILL_DIR, p).split(path.sep).join("/");

// ── 闸 1：引用断链 ──────────────────────────────────────────────────
const REF_RE =
  /(?:references|scripts)\/[A-Za-z0-9_\u4e00-\u9fff\-/]+\.(?:md|py|js)/g;

function checkBrokenRefs(docs) {
  const broken = new Map();
  for (const d of docs) {
    if (!d.endsWith(".md")) continue;
    for (const m of readText(d).matchAll(REF_RE)) {
      const target = m[0];
      if (!fs.existsSync(path.join(SKILL_DIR, target))) {
        if (!broken.has(target)) broken.set(target, new Set());
        broken.get(target).add(rel(d));
      }
    }
  }
  return broken;
}

// ── 闸 2：负向声明 ──────────────────────────────────────────────────
function checkNegative(docs) {
  const hits = [];
  for (const d of docs) {
    if (NEGATIVE_EXEMPT.has(path.basename(d))) continue;
    readText(d)
      .split(/\r?\n/)
      .forEach((line, i) => {
        for (const w of NEGATIVE_WORDS) {
          if (line.includes(w)) {
            hits.push({ file: rel(d), line: i + 1, word: w, text: line.trim().slice(0, 70) });
          }
        }
      });
  }
  return hits;
}

// ── 闸 3：字体白名单 —— 零容忍 ──────────────────────────────────────
// SKILL.md 硬约束 1：全库只允许两个白名单字体名。
// 白名单外的字体名**在任何位置都不许出现**，包括正文、表格、注释、反例。
// 因此不设行级豁免：想提别的字体就不写，想教人别写就不举那个名字。
// ⚠️ 唯一例外是本文件自身：FONT_FAMILY_NAMES 必须**逐个字面列出**被拦的族名，
//    否则这张表写不出来（实测：豁免前本文件报 22 处，全是自己的表和注释）。
//    这与 NEGATIVE_EXEMPT 同一道理——禁令的载体必须能引述被禁的词形。
const FONT_RE = /(?:font|set_font\(\s*font)\s*[=:]\s*["']([^"']+)["']/gi;
// 反查用：扫描全文任意位置的疑似字体名（限「已知族名 + 可选后缀词」形态，避免误伤普通英文词）。
//
// 为什么用「枚举族名 + 可选后缀」而不是「首词前缀」：
//   首词式前缀表有两个实测漏洞——① 「厂商前缀 + 字体名」型（微软雅黑的全名就是这种，
//   本机字体安装器也用这种写法）会整个绕过；② 末尾固定两段词时，**裸名**
//   （两字族名而非三字）匹配不到。枚举式两种都能覆盖。
// ⚠️ 族名表必须覆盖白名单两个字体的首词，否则「白名单内字体名写错后缀」这类反例
//   （如楷体名漏掉尾部 GB）会绕过闸 3 —— 本技能自己就犯过这个错。
// ⚠️ 本表里的名字就是被拦对象，所以本文件必须自豁免（见 NEGATIVE_EXEMPT 同理）。
//    想举反例别把真名写出来，用「微软雅黑全名」「某楷体名」这种描述性说法。
const FONT_FAMILY_NAMES = [
  "Microsoft YaHei", "Microsoft JhengHei", // 厂商前缀型，漏了最容易被钻
  "Noto Sans", "Noto Serif", "LXGW WenKai", "Source Han", "思源黑体",
  "Alibaba PuHui", "PuHuiTi", "YaHei", "PingFang", "SimHei", "SimSun",
  "DengXian", "STSong", "STHeiti", "STFangsong", // ctex 默认 CJK 族名
  "Helvetica", "Arial", "Times New Roman", "Courier New",
];
const FONT_NAME_SCAN = new RegExp(
  "\\b(?:" + FONT_FAMILY_NAMES.map((n) => n.replace(/ /g, "\\s+")).join("|") + ")" +
    "(?:[\\s一-鿿]+[A-Za-z一-鿿][A-Za-z0-9]*){0,2}",
  "g",
);

function checkFonts(docs) {
  const bad = [];
  for (const d of docs) {
    // 本文件自身豁免：它必须逐字列出被拦的族名（见上方 FONT_FAMILY_NAMES 处的说明）。
    if (path.basename(d) === "skill_audit.js") continue;
    // .js 也要扫：文档里写了「全目录、.js 也扫」，窄化到 .py/.md 会让闸 3 形同虚设
    // （已实测：坏字体名写在 .js 里不报，改成 .py 才报）。
    if (!(d.endsWith(".py") || d.endsWith(".md") || d.endsWith(".js"))) continue;
    readText(d)
      .split(/\r?\n/)
      .forEach((line, i) => {
        for (const m of line.matchAll(FONT_RE)) {
          if (!FONT_ALLOW.has(m[1])) {
            bad.push({ file: rel(d), line: i + 1, font: m[1], kind: "font=" });
          }
        }
        for (const m of line.matchAll(FONT_NAME_SCAN)) {
          if (!FONT_ALLOW.has(m[0].trim())) {
            bad.push({ file: rel(d), line: i + 1, font: m[0].trim(), kind: "全文出现" });
          }
        }
      });
  }
  return bad;
}

// ── 闸 4：体量红线 ──────────────────────────────────────────────────
// 所有文档同限 10000 字符，超了必须拆分。
function checkSize(docs) {
  const red = [];
  const rows = [];
  for (const d of docs) {
    const text = readText(d);
    const r = rel(d);
    rows.push({ file: r, chars: text.length });

    const isDoc = r === "SKILL.md" || (r.startsWith("references/") && r.endsWith(".md"));
    if (isDoc && text.length > BUDGET.docChars) {
      red.push({
        what: r,
        detail: `${text.length} > ${BUDGET.docChars}字符 ⇒ 拆分，不要上调阈值`,
      });
    }
  }
  return { red, rows };
}

function main() {
  const argv = process.argv.slice(2);
  const docs = allDocs();
  const red = [];

  const broken = checkBrokenRefs(docs);
  if (broken.size) red.push("引用断链");

  const neg = checkNegative(docs);
  if (neg.length) red.push("负向声明");

  const badFont = checkFonts(docs);
  const fontRed = badFont.filter((h) => !h.exempt);
  if (fontRed.length) red.push("字体白名单");

  const { red: sizeRed, rows } = checkSize(docs);
  red.push(...sizeRed.map((r) => r.what));

  const skillChars = rows.find((r) => r.file === "SKILL.md")?.chars ?? 0;

  console.log("\x1b[36m══ skill_audit：自进化门禁 ══\x1b[0m");
  console.log(`技能目录：${SKILL_DIR}`);
  console.log(
    `\n体量红线：每篇文档 ≤ ${BUDGET.docChars} 字符（超了拆分）` +
      `  ·  SKILL.md 现 ${skillChars}` +
      (argv.includes("--top") ? "\n单篇文档：" : ""),
  );
  for (const r of rows.filter((x) => x.file.endsWith(".md") && x.file !== "SKILL.md")) {
    const mark = r.chars > GREP_FIRST_CHARS ? "  ⚠️ 建议标注「先 Grep 局部读」" : "";
    console.log(`  ${String(r.chars).padStart(6)} 字符  ${r.file}${mark}`);
  }

  console.log(`\n[引用断链] ${broken.size ? `❌ ${broken.size} 处` : "✅ 无"}`);
  for (const [target, srcs] of broken) {
    console.log(`  ❌ ${[...srcs].join(", ")} 引用了不存在的 ${target}`);
  }

  console.log(`[负向声明] ${neg.length ? `❌ ${neg.length} 处` : "✅ 全库无痕迹"}`);
  for (const h of neg.slice(0, 15)) console.log(`  ❌ ${h.file}:${h.line}  [${h.word}] ${h.text}`);

  console.log(
    `[字体白名单] ${fontRed.length ? `❌ ${fontRed.length} 处` : "✅ 全库仅两个白名单字体名"}`,
  );
  for (const h of badFont.slice(0, 15)) {
    console.log(`  ❌ ${h.file}:${h.line}  [${h.kind}] ${h.font}`);
  }

  console.log(`[体量红线] ${sizeRed.length ? `❌ ${sizeRed.length} 处` : "✅ 全部达标"}`);
  for (const r of sizeRed) console.log(`  ❌ ${r.what}  ${r.detail}`);

  if (argv.includes("--top")) {
    console.log("\n体量 TOP 8：");
    for (const r of [...rows].sort((a, b) => b.chars - a.chars).slice(0, 8)) {
      console.log(`  ${String(r.chars).padStart(6)}  ${r.file}`);
    }
  }

  if (argv.includes("--save")) {
    fs.appendFileSync(
      HISTORY_FILE,
      JSON.stringify({ ts: new Date().toISOString(), skillChars, docs: rows.length, red: red.length }) + "\n",
    );
    console.log(`\n已记历史 → scripts/${path.basename(HISTORY_FILE)}`);
  }

  if (argv.includes("--json")) {
    console.log(
      JSON.stringify(
        { ok: red.length === 0, red, broken: [...broken.keys()], negative: neg, badFont, sizeRed },
        null,
        2,
      ),
    );
  }

  if (red.length) {
    console.log(`\n\x1b[31m🚫 ${red.length} 项红灯，先修再提交（node push.js 会拒绝推送）\x1b[0m`);
    process.exit(1);
  }
  console.log("\n\x1b[32m✅ 全绿\x1b[0m");
  process.exit(0);
}

main();
