---
name: shougong
description: 当用户在 jiadlu.github.io workspace 结束当天学习或讨论并说“收工”、要求归档当天 Codex session 或显式调用 $shougong 时，自动把学懂的知识归入 Knowledge，把用户的判断、疑问、吐槽与 brainstorm 归入 Ideas；两者都有则分别整理，校验后 commit 并 push。不用于普通代码任务的结束语，除非用户明确要沉淀内容。
---

# 收工

当前 session 的统一归档入口：Knowledge 记录 **What I learned**，Ideas 记录 **What I think**。按每段讨论的实际内容分流，不给整个 session 强选一个类别。

## 自动分流

| 当前讨论中的内容 | 去向 |
| --- | --- |
| 学懂的概念、机制、完整示例和适用边界 | Knowledge |
| 用户的热点评论、判断、疑问、吐槽、情绪和 brainstorm | Ideas |
| 同一话题同时有知识理解与个人思考 | 分别整理，两边各自完整，不复制同一篇正文 |

例如：弄懂某个 Agent 的规划机制进入 Knowledge；用户认为它的演示掩盖了落地成本进入 Ideas；同一次讨论两者都有，就各留一份。已解答的机制性提问随知识解释归档；个人质疑或尚不成熟的猜想可以独立成为 Idea。依据语义与用户表达判断，不能只凭“为什么”等关键词。

- 只有新闻材料、AI 自己的观点、普通网站工程任务时，不硬造 Ideas 或算法学习记录。“继续讲”不代表用户认同 AI 的判断。
- “收工”授权本 session 符合条件的两个方向整理、commit 和正常 push，无需再次询问。用户明确限定“只归档 Knowledge / 只发 Ideas”时遵从范围；“只整理 / 不发布”只写相应本地忽略目录并 dry-run，不写公开 content 或生成页面。
- 有 Knowledge 内容时，读 `docs/knowledge/README.md` 与 `docs/knowledge/schema.md`，执行下面的知识流程。领域与层级随实际知识增长，不把现有顶层类别当作固定边界。
- 有 Ideas 内容时，读取并执行同项目 `.agents/skills/ideas-editor/SKILL.md` 的声源、事实核查、编辑与 batch 流程。由当前 Codex 执行，无需重新触发一个 session；继承本次发布授权及限制，不递归调用“收工”。
- 任一方向无合适内容就跳过，不创建空记录。缺上下文、无法核实或不适合公开的部分留本地草稿，说明缺口；其余可独立成立的内容仍可归档。两边都为空则说明未归档。

## 两边都有时的执行顺序

先分别准备 `.knowledge-local/` 和 `.ideas-local/` 的 batch，按各自 schema 去重、dry-run 并审阅，再应用和构建。先运行 Knowledge 发布器，确认正常 push 成功后，再运行 Ideas 发布器；只有一边时只运行那一边。不要并行操作 Git，也不要合并为绕过发布器检查的手工提交。

两个发布器只接受各自类型的待推送提交。因此第一个 push 失败时，应修复并重试同一个发布器，成功之前不提交第二边。已推送但 Pages 待更新不阻止第二边 push。第二边失败时保留第一边结果与本地成果，明确报告部分成功；重试复用 ID 与已创建的提交。最终分别验证两个页面版本，不把一次成功当成两边成功。

以下为 Knowledge 部分；Ideas 的具体编辑与发布步骤以 Ideas editor 为准。

## 回顾与提炼

1. 以 `Asia/Shanghai` 确定学习日期；跨午夜时依据本次学习的日期或用户指定日期，不要擅自把昨日 session 改记为今天。
2. 回顾当前 session 可访问的完整对话、压缩摘要及本 session 的 `.knowledge-local/` 检查点。覆盖所有已讨论且值得复用的知识点，保留关键纠正、假设、反例和结论。不要把搭建这个网站的工程讨论当成算法学习。
3. 上下文不足以忠实还原完整示例时，优先读取明确属于当前 session、且已授权可访问的会话记录；不要遍历其他日期或其他 session。若仍缺失，说明具体缺口，请用户补充后再归档受影响的知识点；不要声称已完整回顾。可以先提炼已确定的部分到本地草稿。
4. 每个知识点应包含：一句精炼解释；当时的问题；必要的机制与适用边界；至少一个完整、有代表性的示例（输入、步骤、代码如适用、结果与解释）；一到两句记忆点；一个主动回忆问题和答案。保留 session 中真正有帮助的示例，不用无关模板替换。未验证的推断明确标注；不把讨论中的错误结论当成事实。
5. 示例中的凭据、私人路径、隐私和未公开资料要去除或匿名化。只发布整理后的学习笔记，不上传完整聊天记录。这里是公开 GitHub 仓库和公开网页。

## 分类与增量更新

- 先读取 taxonomy 与已有笔记的标题、别名、摘要，按语义查重。复学同一概念复用稳定 ID，更新原笔记，保留仍有效的内容与代表性示例；不要以日期创建重复概念。
- 每个概念选一个主要父分支，跨领域关系通过 `related` 表示。分类要表达知识关系，不按日期或来源分组。找不到合理分支时添加适度粒度的父分支；同义类别不要重复创建。
- 每次归档执行 [知识树分类 SOP](references/taxonomy.md)：先判断技术属性，再检查父子关系与相邻笔记，必要时拆分、迁移或扩展顶层。不要把同类知识不断追加到一个大类下，也不要为凑层级逐篇建分类。
- 区分 Agent 系统与工程（运行时、Harness、框架、编排）与 Agent 算法及能力训练（策略学习、奖励、优化）；通用训练和评测方法不因示例使用 Agent 就归入 Agent 工程。
- 纯分类迁移直接更新 taxonomy 和笔记的 `branch`，作为结构维护审查、构建和发布；不将未复学的旧笔记加入当天 entries。学习内容的新增或实质修订仍使用下述 batch。
- 日期记录中的 `takeaway` 写“这一次理解了什么”。它与知识点当前摘要不同，应保留历史；同一天再收工，只更新对应条目并合并新增条目。`kind` 是本次 `learn` 或 `review`，依据已有历史判断。
- 若没有值得沉淀的学习，不创建空记录，不增加连续学习天数；继续处理符合条件的 Ideas。
- 生成 schema 所定义的 batch JSON，放到 `.knowledge-local/`，其中 `notes` 使用完整笔记对象。不要直接编辑 `knowledge/data/` 或生成的 HTML。

## 校验与发布

以下应用与发布命令仅用于已授权发布的 Knowledge 部分。只整理时在第一条 dry-run 后停止，草稿保持本地。两边都有时遵循上面的顺序。

从仓库根目录执行：

```sh
python3 scripts/knowledge_ingest.py .knowledge-local/YYYY-MM-DD.batch.json
python3 scripts/knowledge_ingest.py .knowledge-local/YYYY-MM-DD.batch.json --apply
python3 scripts/knowledge.py validate
python3 scripts/knowledge.py build
python3 -m unittest discover -s tests -v
node --check knowledge/assets/app.js
```

先检查 dry-run 列出的变更，再应用。随后检查 diff：概念归属、示例完整性、当日条目是否齐全、旧记录是否保留、是否有重复/隐私内容。对新增示例执行有意义且安全的验证；不可执行的示例解释其性质。

本地校验通过后执行：

```sh
python3 scripts/knowledge_publish.py --date YYYY-MM-DD
```

它只 stage 内容与生成页面，要求 `furbish` 分支、正确的 origin、没有预先暂存的修改，并检查远端分歧和待推送提交。不要使用 `git add .`、force push、reset、自动 stash 或覆盖用户改动。出现非学习改动或远端分歧时，保留当前成果，解决授权范围内的问题；无法安全解决时说明确切阻碍。失败后修复原因再重试，不盲目循环。

推送之后检查 Pages 是否完成：

```sh
python3 scripts/knowledge_publish.py --verify
```

如果仍在构建，可隔约 20 秒检查一次，最多约 3 分钟。验证失败不撤销已完成的内容提交；返回明确的“已推送，线上待确认”，附 Actions 链接。不要把 push 成功等同于部署成功。

结束时分别列出：Knowledge 的新增/回顾知识点与分类变化；Ideas 新增或修改的想法；各自日期、commit、发布状态与页面链接。Ideas 修改直接更新正文，不附修改说明或追溯板块。未归档或仍为草稿的部分简要说明。保持 `.knowledge-local/`、`.ideas-local/` 为本地忽略文件，不随 commit 发布。
