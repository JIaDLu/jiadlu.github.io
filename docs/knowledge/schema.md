# Knowledge 数据约定 · v1

所有文本是 UTF-8 纯文本；前端与静态生成器统一转义，不执行 HTML 或 Markdown 中的脚本。段落可包含换行，代码放入 `code`。数学表达可在段落或代码块中以 Unicode/纯文本表示；v1 不渲染 LaTeX。

唯一 ID 使用稳定英文 kebab-case，不带日期；文件名必须等于 ID。保留 `knowledge-root` 给树的虚拟根。笔记重命名标题不会改变 URL。删除或改 ID 必须同时修复所有日期、关联与分类引用；日常归档应优先保留 ID。

## 分类：content/knowledge/taxonomy.json

```json
{
  "version": 1,
  "timezone": "Asia/Shanghai",
  "branches": [
    {"id": "agents", "title": "Agent 算法", "parent": null, "description": "从推理到行动。"}
  ]
}
```

`parent` 是分支 ID 或 null。树必须无环，每个分支只有一个父分支。笔记的 `related` 承担跨分支关联，页面双向展示这些关联，无需手写双向副本。

## 笔记：content/knowledge/notes/<id>.json

完整实例见 [ReAct 示例](examples/notes/react-loop.json) 和 [SFT 示例](examples/notes/sft-loss-mask.json)。必需字段：

| 字段 | 类型 | 用途 |
| --- | --- | --- |
| id / title / summary | string | 稳定标识、标题、一句话概括 |
| branch | string | 主分类 ID |
| aliases | string[] | 搜索与语义查重辅助 |
| related | string[] | 其他知识点 ID，不可自引或悬空 |
| memory | string[1–2] | 可快速唤回理解的记忆点 |
| context | string | 当时的问题、误区或使用场景 |
| sections | object[] | 每项 `title`、`paragraphs: string[]`；核心解释与边界 |
| examples | object[] | 至少一项，包含完整步骤与结果 |
| recall | object | `question`、`answer`，主动回忆 |
| sources | object[] | `title`、`url`；只接受 http/https，可为空 |

每个 example 必须包含 `title`, `scenario`, `steps: string[]`, `code`, `language`, `result`。无代码时后两项用空字符串，仍保留完整场景、步骤和结果。大段内容可用多节、多示例组织。不要为了凑模板压缩掉代表性例子的关键步骤。

## 每日记录：content/knowledge/days/YYYY-MM-DD.json

```json
{
  "date": "2026-09-13",
  "summary": "分清工具动作与反馈循环",
  "entries": [
    {"note": "react-loop", "takeaway": "一次工具调用不是整个 Agent 循环。", "kind": "review"}
  ]
}
```

只引用知识点 ID；`takeaway` 保存当天的理解，`summary` 是当天的主题概括。知识正文只存于笔记。一个日期文件中的同一 note 只能出现一次。无学习日不建文件。所有笔记至少有一天记录；不允许未来真实记录。

## 收工 batch（仅本地，不公开）

```json
{
  "date": "2026-09-13",
  "summary": "当天主题",
  "branches": [],
  "notes": [],
  "entries": [
    {"note": "已存在的知识点 ID", "takeaway": "本次理解", "kind": "review"}
  ]
}
```

`branches` 是新增/更新分支，`notes` 是新增/更新的**完整**笔记对象；字段结构见上文。这里的 ID 占位文字应替换成真实稳定 ID。仅回顾而不修改正文时 `notes` 可以为空。每个编辑的笔记必须同时出现在本次 entries 中。

合并规则：分支和笔记按 ID upsert；当天 entries 按 note 合并，其余旧条目保留；当天 summary 使用本次版本。相同 batch 重复应用不产生变化。脚本先在临时目录验证完整候选数据，然后替换变动文件；异常时恢复，锁防止两个 ingest 同时执行。异常中断留下锁时应先检查进程和源数据，再清除锁。

## 生成结果

- `knowledge/data/graph.json`：分类、精简知识索引与日期列表；由源数据派生，不独立维护。
- `knowledge/notes/<id>/index.html`：独立、可直达、带各自元信息的详情。
- `knowledge/data/revision.json`：正文、索引、生成器与前端资源的内容指纹，用于线上校验。

真实数据与演示数据分别生成。`knowledge/demo/` 的统计完全隔离，演示日历以样例最后一天为“今天”，从而保留可复现的演示状态。
