#!/usr/bin/env node
// push.js — 本技能自进化流程的落地点：门禁 → 提交 → 推送 → 打 tag
//
// 用法：
//   node push.js "<说明>"        正常自进化提交（门禁不过会拒绝推送）
//   node push.js --check         只跑门禁，不提交不推送
//   node push.js --force         门禁有红灯时强行提交（需显式给出，必须在汇报里说明原因）
//   node push.js --no-tag        提交推送但不打 tag（默认每次都打）
//
// 设计依据：references/自进化与维护.md §七
//   1. 门禁前置：引用断链 / 负向声明 / 字体白名单 / 体量红线，任一红灯拒绝推送
//   2. 仓库根校验：C:/Users/... 与 D:/CToD/... 是同一目录的两个视图，必须 realpath 归一后比对
//   3. origin 校验：只允许推本技能自己的仓库
//   4. tag 是回滚的唯一落点，tag 名带 SKILL.md 的 version，便于 `git checkout <tag> -- .` 回滚
//
// 退出码：0 成功 · 1 失败 · 2 门禁红灯（未 --force） · 3 仓库校验失败

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SKILL_DIR = path.resolve(__dirname);

// 本技能唯一允许的远端
const EXPECTED_ORIGIN = "git@github.com:steelan9199/math-animation-video-yashu.git";

const argv = process.argv.slice(2);
const FORCE = argv.includes("--force");
const CHECK_ONLY = argv.includes("--check");
const NO_TAG = argv.includes("--no-tag");
const message =
  argv.filter((a) => !a.startsWith("--"))[0] || `Update: ${new Date().toLocaleString("zh-CN")}`;

function die(code, msg) {
  console.error(`\x1b[31m${msg}\x1b[0m`);
  process.exit(code);
}

// 本机坑：node 运行时 spawn 任何子进程都可能返回 EBUSY（连不存在的可执行文件也是 EBUSY
// 而非 ENOENT），此时无法用脚本驱动 git。表现为 `spawnSync git EBUSY`。
// 对策：把等价的手工命令原样打出来，人/AI 在 PowerShell 里跑，不要在这里硬重试。
const SPAWN_BROKEN = Symbol("spawn-broken");

function runGit(args, options = {}) {
  const result = spawnSync("git", args, { encoding: "utf8", ...options });
  if (result.error) {
    if (result.error.code === "EBUSY" || result.error.code === "EAGAIN") throw SPAWN_BROKEN;
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(result.stderr?.trim() || `git ${args.join(" ")} failed`);
  }
  return result.stdout || "";
}

/** SPAWN_BROKEN 时打印可手工执行的等价命令 */
function manualFallback(pending) {
  console.error(
    [
      "",
      "\x1b[33m⚠ 本机 node 无法 spawn 子进程（EBUSY），脚本不能驱动 git。\x1b[0m",
      "  请在 PowerShell 里手工执行以下等价命令：",
      "",
      ...pending.map((a) => "    git " + a.map((x) => (/\s/.test(x) ? `"${x}"` : x)).join(" ")),
      "",
      "\x1b[90m  注意：先跑门禁 node scripts/skill_audit.js，通过后再执行上面两条。\x1b[0m",
      "",
    ].join("\n"),
  );
}

/** 读取 SKILL.md frontmatter 的 version，用作 tag 前缀 */
function readSkillVersion() {
  try {
    const txt = fs.readFileSync(path.join(SKILL_DIR, "SKILL.md"), "utf-8");
    const m = txt.match(/^version:\s*(\S+)/m);
    return m ? m[1] : "0.0.0";
  } catch {
    return "0.0.0";
  }
}

// ── 闸 0：确认脚本操作的确实是本技能仓库（不是别人的） ────────────────
function verifyRepo() {
  const top = runGit(["-C", SKILL_DIR, "rev-parse", "--show-toplevel"]).trim();
  // ⚠️ 同一目录有 C:/Users/... 与 D:/CToD/... 两个视图，必须 realpath 归一后比
  const realTop = fs.realpathSync(top);
  const realSkill = fs.realpathSync(SKILL_DIR);
  const norm = (p) => process.platform === "win32" ? p.toLowerCase() : p;
  if (norm(realTop) !== norm(realSkill)) {
    die(3, `仓库根校验失败：\n  skill_dir  realpath = ${realSkill}\n  git toplevel realpath = ${realTop}\n  两者不是同一目录，拒绝操作。`);
  }
  const origin = runGit(["-C", SKILL_DIR, "remote", "get-url", "origin"]).trim();
  if (origin !== EXPECTED_ORIGIN) {
    die(3, `origin 校验失败：\n  期望 ${EXPECTED_ORIGIN}\n  实际 ${origin}\n  拒绝推送到非本技能仓库。`);
  }
  return { top: realTop, origin };
}

// ── 闸 1：自进化门禁 ───────────────────────────────────────────────
function runAudit() {
  const script = path.join(SKILL_DIR, "scripts", "skill_audit.js");
  if (!fs.existsSync(script)) {
    console.log("\x1b[33m门禁脚本不存在，跳过（scripts/skill_audit.js）\x1b[0m");
    return 0;
  }
  console.log("\x1b[36mRunning self-evolution gate (skill_audit.js)...\x1b[0m");
  const r = spawnSync(process.execPath, [script], { encoding: "utf8", stdio: "inherit" });
  return r.status ?? 1;
}

function tagExists(tagName) {
  return spawnSync("git", ["-C", SKILL_DIR, "rev-parse", "--verify", `refs/tags/${tagName}`]).status === 0;
}

/** tag 名：v<SKILL.md version>-<时间戳>，便于按版本回滚 */
function generateTagName(version) {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  const stamp = `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
  const base = `v${version}-${stamp}`;
  let name = base;
  let i = 1;
  while (tagExists(name)) name = `${base}-${i++}`;
  return name;
}

function createAndPushTag(version) {
  const tagName = generateTagName(version);
  const tagMessage = `v${version} @ ${new Date().toLocaleString("zh-CN")}`;
  console.log(`\x1b[36mCreating tag: ${tagName}...\x1b[0m`);
  runGit(["-C", SKILL_DIR, "tag", "-a", tagName, "-m", tagMessage]);
  runGit(["-C", SKILL_DIR, "push", "origin", tagName], { stdio: "inherit" });
  console.log(`\x1b[32m✔ tag ${tagName} 已推送（回滚落点）\x1b[0m`);
  console.log(`\x1b[90m  回滚代码：git -C "${SKILL_DIR}" checkout ${tagName} -- .\x1b[0m`);
  return tagName;
}

/**
 * 主流程。
 * 注意 git 调用全部经由 runGit；一旦本机 spawn 不可用（EBUSY），
 * 走手工降级路径——打印等价命令让人执行，而不是在这里空转重试。
 */
function main() {
  // `--check` 只跑门禁，不碰 git（本机 node 可能spawn 不了 git，见 manualFallback）
  if (CHECK_ONLY) {
    const code = runAudit();
    console.log(code === 0 ? "\x1b[36m--check：门禁通过。\x1b[0m" : "\x1b[36m--check：门禁有红灯。\x1b[0m");
    process.exit(code);
  }

  // 阶段 0：闸门与仓库校验
  const repo = verifyRepo();
  console.log(`\x1b[36m仓库：${SKILL_DIR}\x1b[0m`);
  console.log(`\x1b[90morigin：${repo.origin}\x1b[0m`);

  const auditCode = runAudit();
  if (auditCode !== 0) {
    if (!FORCE) {
      die(2, `门禁未通过（退出码 ${auditCode}），已拒绝提交推送。\n  修完再推；确实需要强推用：node push.js --force "<说明>"`);
    }
    console.log("\x1b[33m⚠ --force：门禁有红灯仍继续提交。必须在汇报里说明原因。\x1b[0m");
  }

  // 阶段 2：提交推送
  const version = readSkillVersion();
  const status = runGit(["-C", SKILL_DIR, "status", "--porcelain"]);
  if (!status.trim()) {
    console.log("\x1b[32m无改动，无需提交。\x1b[0m");
    process.exit(0);
  }
  runGit(["-C", SKILL_DIR, "add", "-A"]);
  runGit(["-C", SKILL_DIR, "commit", "-m", message], { stdio: "inherit" });
  runGit(["-C", SKILL_DIR, "push"], { stdio: "inherit" });
  console.log("\x1b[32m✔ 已提交并推送。\x1b[0m");

  // 阶段 3：打回滚 tag
  if (NO_TAG) {
    console.log("\x1b[90m--no-tag：本次未打 tag。\x1b[0m");
  } else {
    createAndPushTag(version);
  }
}

try {
  main();
} catch (e) {
  if (e === SPAWN_BROKEN) {
    manualFallback([
      ["-C", SKILL_DIR, "status", "--porcelain"],
      ["-C", SKILL_DIR, "add", "-A"],
      ["-C", SKILL_DIR, "commit", "-m", message],
      ["-C", SKILL_DIR, "push"],
    ]);
    process.exit(4);
  }
  die(1, `push 失败：${e.message}`);
}
