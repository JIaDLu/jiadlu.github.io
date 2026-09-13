# Knowledge

一个随每天的学习持续生长的个人知识系统。当前站点是原生静态 HTML，Knowledge 保持这一架构，采用独立 CSS、JavaScript 与 Python 标准库工具；不需要数据库、API key 或常驻服务。

## 体验路径

- `/knowledge/`：真实学习日历、间隔与连续学习、每日摘要、关键词/领域过滤。
- `/knowledge/tree/?node=<id>`：完整知识树，自动展开祖先并居中定位；拖动、滚轮/双指缩放、节点展开/收起、搜索、上下文侧栏、键盘及大纲入口。
- `/knowledge/notes/<id>/`：当时的问题、解释、可折叠完整示例、记忆点、主动回忆、关联与历史。静态 HTML 即可阅读，无需 JS。
- `/knowledge/demo/`：明确标记的演示空间，不计入真实记录。

在树中第一次点击节点会选择并展示上下文；侧栏“进入知识详情”或再次点击已选知识点进入详情。分支的圆形加减号控制展开。日期点击与过滤状态体现在 URL 中，可分享和浏览器后退恢复。

## 来源与架构

```text
当天 Codex session
  └─ 收工 Skill：回顾 → 提炼 → 分类 → 本地 batch
      └─ knowledge_ingest.py：查结构、合并、幂等更新
          └─ content/knowledge/
              ├─ taxonomy.json       唯一分类结构
              ├─ notes/<id>.json     唯一知识正文
              └─ days/<date>.json    每日理解 + note 引用
                  └─ knowledge.py：校验 → 生成索引与静态详情
                      └─ knowledge_publish.py：commit → push furbish
                          └─ 现有 GitHub Pages → revision 校验
```

机器脚本检查结构与引用，语义归类与查重由 Codex 完成。缺失上下文时 Skill 说明缺口，不编造历史。项目 [AGENTS.md](../../AGENTS.md) 指引学习过程中保留本 session 的本地检查点，供上下文压缩后恢复。

数据格式见 [schema.md](schema.md)。JSON 是主数据格式，避免在 Markdown frontmatter、日历与树之间维护三份内容。历史 takeaway 保存当天理解；正文提供持续修订的当前解释。完整旧正文可通过 Git 历史找回，v1 不提供逐日正文快照界面。

## 每日使用

在这个 workspace 的当天学习 session 中直接输入 **收工**，或显式调用 `$shougong`。项目 Skill 位于 `.agents/skills/shougong/`，AGENTS.md 也为已有 session 提供明确路由。Skill 应用 batch 后构建、校验和检查 diff，再发布。没有知识内容则不打卡。

自动化是由“收工”触发，并非午夜定时任务；session 不会在后台自动读取。真实学习从空白开始。演示笔记来自产品教学案例，来源链接附在各自详情中。

## 本地预览与验证

在仓库根目录：

```sh
python3 scripts/knowledge.py validate
python3 scripts/knowledge.py build
python3 -m unittest discover -s tests -v
node --check knowledge/assets/app.js
python3 -m http.server 8765 --bind 127.0.0.1
```

浏览 `http://127.0.0.1:8765/knowledge/`，演示地址为 `/knowledge/demo/`。生成文件与源数据一起提交。站点运行无 npm 依赖；可选 DOM 交互测试使用临时安装的 `jsdom@24.1.3`（CI 自动执行 `tests/knowledge.dom.cjs`），不打包到网页。Python 3.10+（需系统 IANA 时区数据），Node 仅供 JavaScript 语法检查。

## 发布与故障恢复

2026-09-13 已核实：现有 Pages 部署来源为 `furbish`，根目录主页与线上一致。保留 GitHub 的分支发布，不切换部署服务。`.github/workflows/knowledge-check.yml` 是只读完整性检查；**它不阻塞 GitHub 自带 Pages 的独立部署**，因此发布脚本和 Skill 的本地校验是正常发布的前置条件。

- 日常发布：`python3 scripts/knowledge_publish.py --date YYYY-MM-DD`。
- 核实上线：`python3 scripts/knowledge_publish.py --verify`，非零返回表示尚未确认。
- 代码/Skill 实现变动需单独提交；日常发布器不夹带这些内容。
- push 网络失败：已有 commit 保留。修复网络后再执行发布器，它能识别已提交的知识变更并重试 push。
- 远端有新提交、切错分支、预暂存用户修改、存在无关待推送提交：停止并说明，不能 force push 或覆盖。
- 本地源数据提交后不能跳过 build：CI 会检查源与生成结果是否一致。
- `.knowledge-local/` 永不提交；`_config.yml` 将作者工具和源目录从 Pages 站点构建中排除。但 GitHub 仓库本身是公开的，提交到 Git 的内容仍然公开。

Pages 工作流：https://github.com/JIaDLu/jiadlu.github.io/actions

官方参考：[Codex Skills](https://developers.openai.com/codex/skills/)、[GitHub Pages 发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。
