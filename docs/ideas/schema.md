# Ideas 数据约定 · v1

`content/ideas/posts/<id>.json` 是一条已发表想法的唯一来源；时间流、归档、详情、搜索与 Atom 均由它派生。真实数据不允许 `draft` 状态。未发表内容和编辑依据只写入被忽略的 `.ideas-local/`。

## 站点设置

`content/ideas/settings.json` 保存 version、timezone（Asia/Shanghai）、title、description 和平铺的 tags：`{"id":"agents","label":"Agents"}`。Tag 用稳定英文 ID，标签名称可改；每条内容最多 3 个。初始话题是 Agents、Models、Infra、行业、工作与成长、日常。只有确实需要时增加，不按公司、月份、每个新模型不断膨胀分类。

## 公开 post

```json
{
  "id": "a-question-worth-keeping",
  "title": "",
  "date": "2026-09-20",
  "updated": "2026-09-20",
  "kind": "idea",
  "tags": ["agents"],
  "excerpt": "",
  "blocks": [{"type": "paragraph", "text": "这里替换成用户自己的想法。"}],
  "sources": [],
  "updates": []
}
```

此示例只解释结构，不是可直接发表的素材。ID 与文件名相同，使用 kebab-case；修改标题不改变 URL。`date` 是最初记录/发表日期，`updated` 是最后修订日期，均不允许真实未来日期。相同日期可有多条，使用 ID 保证稳定排序，不虚构小时精度。

`kind`：`idea`（短想法，允许空标题）、`note`（随记、观察、吐槽）、`essay`（长文）。它们控制阅读布局，不限制主题。`excerpt` 可空；非空时是作者视角的引子，最多 300 字，不是营销导语。无 excerpt 时自动使用正文首段。

### 内容 block

所有字段按原文转义，支持 Unicode 与换行，不执行原始 HTML。代码保持原样。v1 不解释 Markdown、LaTeX、任意 iframe 或远程脚本。

| type | 必需字段（除 type） | 说明 |
| --- | --- | --- |
| paragraph | text | 自然段；可选 refs: source ID[] |
| heading | text | 小节标题，自动生成锚点 |
| quote | text, attribution | 引用与归属；可选 refs |
| code | code, language | 完整代码/伪代码，可复制 |
| callout | label, text | 疑问、假设、边界、重点；可选 refs |
| list | items: string[], ordered: boolean | 列表；可选 refs |
| divider | — | 自然停顿 |

只用 paragraph 也完全有效。essay 至少三个小节时才显示目录；idea 不套用长文章布局。首页完整显示不超过 500 字、由纯段落构成的短 Idea，其他内容显示引子与详情入口。

### 来源与补记

source 结构：`id`, `title`, `url`, `publisher`, `published`（YYYY-MM-DD 或 null）, `accessed`（实际查阅日）。引用 block 用 `refs: ["source-id"]` 指向它。只允许 http/https URL，拒绝嵌入凭据与悬空引用。

updates 是 `{"date":"2026-09-21","text":"后来改变了哪些判断，以及为什么。"}` 的数组，按时间追加。ingest 强制保留旧补记与首次日期，正文修改需要新补记。每次正文修订或跨日修改都需要补记；说明可以很短，修正文案不必伪装成认知变化。补记中的旧版本全文由 Git 保留。

## 私有 batch

```json
{
  "posts": ["完整 post 对象，实际使用时不是这个字符串"],
  "tags": [],
  "voice": [
    {
      "post": "a-question-worth-keeping",
      "anchors": [{"quote": "当前 session 的真实用户原话", "supports": [0]}]
    }
  ],
  "review": {"voice_preserved": true, "facts_checked": true, "privacy_checked": true}
}
```

`supports` 是这句话支持的正文 block 下标（从 0 开始）。每个 post 至少有一个真实用户表达依据；所有个人立场应能回溯。AI 编造原话或无依据勾选 review 均违反 Skill。脚本检查完整性与对应关系，不能替代语义审校。

`tags` 是新增/调整的完整 tag 对象，可为空。post 按 ID upsert，相同 batch 重复应用不产生新内容。先在临时目录合并并校验，再替换公开 JSON；常规异常恢复备份，锁阻止并发 ingest。进程强制终止后需核查遗留锁与文件状态再恢复。

`voice`、`review`、session 标识不写入 content，也不生成到网页。只有用户授权发表才 `--apply`；仅草稿时保持在 `.ideas-local/`，即使全站构建也不会被读入。

## 派生文件与增长

- `/ideas/`、`/ideas/page/N/`：静态分页，每页 12 条，关闭 JS 也可浏览。
- `/ideas/archive/`：日期范围、月份、形态、tag、全文关键词组合筛选，URL 可分享，支持后退和结果分页。
- `/ideas/posts/<id>/`：独立静态详情、准确的文章元信息与 canonical。
- `/ideas/data/index.json`：搜索文本与已转义卡片，不存编辑依据。归档时才加载，首页不下载整个索引。v1 对归档使用单一索引；规模达到数千篇长文时可按年分片，无需改变作者数据。
- `/ideas/feed.xml`：最新 50 条 Atom 订阅，ID 与首次日期稳定。
- `/ideas/data/revision.json`：所有生成页面与资源的内容指纹，用于上线确认。
- `/ideas/demo/`：独立示例数据，所有页面标注演示并 noindex，不进入真实流或真实订阅。
