---
name: shougong
description: 当用户在 jiadlu.github.io workspace 结束当天学习并说“收工”、要求归档当天 Codex 学习或显式调用 $shougong 时，提炼当前 session 的知识、更新知识树与每日记录，校验后 commit 并 push 到现有 GitHub Pages 分支。不用于普通代码任务的结束语，除非用户明确要归档学习。
---

# 收工

把当前学习 session 的有效理解沉淀到 `/knowledge/`。重点是 Agent 算法与大模型训练，但允许按内容扩展其他领域。先读仓库的 `docs/knowledge/README.md` 与 `docs/knowledge/schema.md`；结构以 `scripts/knowledge.py` 的校验为准。

## 回顾与提炼

1. 以 `Asia/Shanghai` 确定学习日期；跨午夜时依据本次学习的日期或用户指定日期，不要擅自把昨日 session 改记为今天。
2. 回顾当前 session 可访问的完整对话、压缩摘要及本 session 的 `.knowledge-local/` 检查点。覆盖所有已讨论且值得复用的知识点，保留关键纠正、假设、反例和结论。不要把搭建这个网站的工程讨论当成算法学习。
3. 上下文不足以忠实还原完整示例时，优先读取明确属于当前 session、且已授权可访问的会话记录；不要遍历其他日期或其他 session。若仍缺失，说明具体缺口，请用户补充后再归档受影响的知识点；不要声称已完整回顾。可以先提炼已确定的部分到本地草稿。
4. 每个知识点应包含：一句精炼解释；当时的问题；必要的机制与适用边界；至少一个完整、有代表性的示例（输入、步骤、代码如适用、结果与解释）；一到两句记忆点；一个主动回忆问题和答案。保留 session 中真正有帮助的示例，不用无关模板替换。未验证的推断明确标注；不把讨论中的错误结论当成事实。
5. 示例中的凭据、私人路径、隐私和未公开资料要去除或匿名化。只发布整理后的学习笔记，不上传完整聊天记录。这里是公开 GitHub 仓库和公开网页。

## 分类与增量更新

- 先读取 taxonomy 与已有笔记的标题、别名、摘要，按语义查重。复学同一概念复用稳定 ID，更新原笔记，保留仍有效的内容与代表性示例；不要以日期创建重复概念。
- 每个概念选一个主要父分支，跨领域关系通过 `related` 表示。分类要表达知识关系，不按日期或来源分组。找不到合理分支时添加适度粒度的父分支；同义类别不要重复创建。
- 日期记录中的 `takeaway` 写“这一次理解了什么”。它与知识点当前摘要不同，应保留历史；同一天再收工，只更新对应条目并合并新增条目。`kind` 是本次 `learn` 或 `review`，依据已有历史判断。
- 若没有值得沉淀的学习，不创建空记录，不增加连续学习天数，直接说明。
- 生成 schema 所定义的 batch JSON，放到 `.knowledge-local/`，其中 `notes` 使用完整笔记对象。不要直接编辑 `knowledge/data/` 或生成的 HTML。

## 校验与发布

用户在这个项目调用“收工”即授权本次知识归档、commit 和正常 push；已授权时不重复请求确认。若明确说“只整理、不发布”，则完成归档和构建，到发布前停止。

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

结束时简短给出：归档日期、新增/回顾的知识点、分类变化、commit、发布状态与当天页面链接。保持 `.knowledge-local/` 草稿为本地忽略文件，不随 commit 发布。
