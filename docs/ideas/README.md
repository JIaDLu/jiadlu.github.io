# Ideas

**Knowledge = What I learned. Ideas = What I think.** 两者同属个人站点，数据与页面独立，日常可通过“收工”统一分流。Ideas 是一个人的思考流：短想法、疑问、吐槽、随记、技术/行业观察和长文都可以共存。

## 页面

- `/ideas/`：最新时间流。短 Idea 可直接读，长内容显示引子；静态分页，每页 12 条。
- `/ideas/archive/`：全文搜索、日期范围、月份、形态与平铺 tag 组合过滤，可分享筛选 URL，支持后退与分页。
- `/ideas/posts/<id>/`：内容决定版式；短 Idea 无大段导语，长文可有目录、引用、代码、callout、来源。
- `/ideas/feed.xml`：Atom 订阅。
- `/ideas/demo/`：四条虚构演示，展示不同长度的内容；不代表作者立场，不进入真实记录。
- `/blog/`：兼容入口，跳转 `/ideas/`。

首页与详情是静态 HTML，关闭 JavaScript 仍可阅读与翻页。归档交互增强由独立 JS 提供。首页使用用户提供的原图 `ideas/assets/lose-yourself.jpg`，保持完整比例；标题与导航保持简短，移除装饰性标语。视觉保留克制色彩和留白；没有知识树、打卡 KPI 或传统博客侧栏组件堆积。

## 日常闭环

```text
看看 AI 动态 → 一手信息与值得问的问题 → 与 Codex 讨论
    → 用户自己的判断 / 疑问 / 吐槽 / Idea
        → 私有声源映射与编辑 → 本地 batch
            → dry-run → 授权发布时 apply
                → content/ideas/posts（唯一来源）
                    → 静态时间流 / 归档 / 详情 / Atom
                        → 校验 → commit → push furbish → Pages 版本确认
```

项目 Skill：`.agents/skills/ideas-editor/SKILL.md`。可以调用 `$ideas-editor`，也可以自然说：

- **看看 AI 动态**：联网追踪最近有价值的线索，带来源和时间，重点找值得讨论的问题。不会自动发表。
- **先整理成草稿**：从当前对话整理，草稿与原话依据只保存到 `.ideas-local/`。
- **记一笔**：整理并发表当前 session 的想法，包含正常 commit/push 授权；没有真实观点则不造内容。
- **修改某篇**：保留首次日期和链接，直接更新正文，不记录或展示修改过程。

“收工”是统一整理与发布入口：学懂的概念、机制、示例进入 Knowledge；用户的热点评论、判断、疑问、吐槽与 brainstorm 进入 Ideas；两者都有就分别整理、校验并发布。“记一笔”仍可单独发布 Ideas，“只整理、不发布”只保留本地草稿。不为没有内容的一侧创建记录。没有定时爬取、X API、后台模型或社交平台发帖；自动化由 workspace 内的 Codex 指令驱动。访问不了 X 时说明覆盖限制并转向可访问的一手渠道，不能假装已经跟踪。

[数据格式](schema.md) · [编辑与保留声音](editorial.md)

## 数据与隐私

已发表正文在 `content/ideas/posts/<id>.json`，平铺标签在 settings；其他界面都派生。内容块可自由组合，短内容不必凑模板。每个公开观点必须来自用户原话或用户明确认可；私有 batch 的 `voice` 映射只用于审校，脚本不会发布它。

`.ideas-local/` 被 Git 忽略，也由 Pages 排除。未发表内容绝不写入会随 Git 公开的 content，真实空间初始为空。仓库本身公开，已提交的数据即使被 Pages 排除也仍公开。避免提交整段聊天。

## 开发与校验

Python 3.12+ 标准库；浏览器运行无 npm 依赖。临时 DOM 测试使用固定 `jsdom@24.1.3`，安装在临时目录并清理，不写入项目。

```sh
python3 scripts/ideas.py validate
python3 scripts/ideas.py build
python3 -m unittest discover -s tests -v
node --check ideas/assets/app.js
python3 scripts/ideas_dom_check.py
python3 -m http.server 8765 --bind 127.0.0.1
```

预览 `/ideas/` 和 `/ideas/demo/`。构建不会读取 `.ideas-local`，不会修改 Knowledge 内容。代码、测试和生成页面一起提交，保留现有分支发布方式。

发布：`python3 scripts/ideas_publish.py`。发布器运行验证与 DOM 检查，仅 stage Ideas 源与生成物。拒绝错分支、错远端、已暂存的用户修改、远端领先和无关待推送提交。push 失败保留 commit；重试不会重复文章。`--verify` 返回 0 代表线上版本一致，2 表示待确认。

CI 的 Ideas integrity 检查数据、测试、DOM 与生成文件一致性。它不阻塞 GitHub 自带 Pages 的独立部署，本地发布器因此必须先校验再 push。每日编辑不应夹带代码/Skill 改动；首次系统实现使用单独的实现提交。

## 设计参考

实际浏览后提取组织方式，不复制品牌、内容或页面：

- [Simon Willison](https://simonwillison.net/)：同一时间轴容纳长文、短笔记和链接讨论。
- [Maggie Appleton’s Garden](https://maggieappleton.com/garden)：允许未完成的思考持续演化。
- [Lil’Log](https://lilianweng.github.io/)：清晰的长文层级与来源阅读。
- [Anthropic Engineering](https://www.anthropic.com/engineering)：内容优先、克制的技术表达。

首版边界：无评论/登录/点赞；不渲染任意 HTML 或 LaTeX；归档全文索引仅在归档页加载。任何未来扩展都应保持作者数据与页面派生关系。
