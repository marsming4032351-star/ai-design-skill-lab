# LLM Wiki 与 GBrain 小红书图文包

这是一组 3 张以内的小红书知识分享卡，主题是 `LLM Wiki`、`GBrain` 与 `Obsidian` 笔记管理。

## 文件

- `index.html`：可编辑的版式源文件。
- `assets/`：Codex Image / GPT Image 生成的底图。
- `cards/`：最终导出的 1080 x 1350 发布图。
- `post-copy.md`：小红书标题、正文、评论引导、标签。

## 内容逻辑

1. 第 1 张：用“AI 不只是聊天框”的钩子解释 LLM Wiki + GBrain 的总体意义。
2. 第 2 张：拆成两层，LLM Wiki 负责外部知识库，GBrain 负责长期记忆层。
3. 第 3 张：关联 Obsidian，把它落到普通人的笔记管理和 AI 第二大脑工作流。

## 生成方式

底图使用 Codex 内的 `imagegen` skill 调用 GPT Image 生成；中文标题和信息层用 HTML/CSS 覆盖后由 Playwright 截图导出，避免中文在 AI 图片里出现乱码。

## 参考语境

- `LLM Wiki` 公开项目语境通常强调“由 LLM 辅助生成/维护的 Markdown 知识库”，可用于个人知识管理、可检索资料库和 Obsidian 工作流。参考：[LLM Wiki](https://llm-wiki.net/)、[obsidian-llm-wiki](https://pypi.org/project/obsidian-llm-wiki/)、[nvk/llm-wiki](https://github.com/nvk/llm-wiki)。
- `GBrain` 在公开讨论中更常被用作“AI Agent 的长期记忆/本地知识脑”概念或项目名。本文按这个通用解释进行科普，不把它定义为唯一标准。参考：[garrytan/gbrain](https://github.com/garrytan/gbrain)、[AgenticExamples gbrain](https://agenticexamples.co/agent/gbrain.html)。
