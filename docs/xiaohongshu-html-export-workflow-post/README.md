# 小红书发布包：HTML 导出小红书图片工作流

这是一篇面向今天发布的小红书教程图文，主题从候选方向中筛选为：

**如何把 HTML 导出小红书图片。**

选择这个主题的原因：

- 比 Codex prompt 和 GPT Image prompt 更具体，收藏价值更高；
- 能延续前两篇 Codex 设计工作流内容；
- 可以自然引出下一篇“PPT 变完整提案”；
- 最符合本仓库 HTML/CSS -> Playwright -> PNG 的稳定图文生产方式。

## 文件说明

- `index.html`：5 张卡片的 HTML/CSS 源文件。
- `cards/card-01.png`：封面，别再让 AI 直接生成满屏中文。
- `cards/card-02.png`：解释纯生图和 HTML 各自适合什么。
- `cards/card-03.png`：说明 HTML 卡片结构。
- `cards/card-04.png`：说明 Playwright / 浏览器截图导出。
- `cards/card-05.png`：发布前检查清单。
- `post-copy.md`：小红书标题、正文、评论区引导和标签。

## 图片规格

- 数量：5 张
- 尺寸：1080 x 1350 px
- 比例：4:5
- 格式：PNG

## 编辑方式

如需调整文字或版式，编辑：

```text
docs/xiaohongshu-html-export-workflow-post/index.html
```

然后重新导出：

```bash
python3 -m http.server 8765
```

用 Playwright 或浏览器截图分别截取：

```text
#card-01
#card-02
#card-03
#card-04
#card-05
```

导出后用 `file cards/card-01.png` 检查 PNG 尺寸。
