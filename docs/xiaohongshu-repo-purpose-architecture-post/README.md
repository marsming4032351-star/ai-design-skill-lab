# 小红书发布包：理解 AI Design Skill Lab

这是一套面向小白的小红书图文包，用来解释当前项目的目的、架构和运行原理。

## 文件说明

- `index.html`：可编辑源文件，包含 5 张 1080 x 1350 卡片。
- `cards/`：Playwright / 浏览器导出的 PNG。
- `post-copy.md`：发布标题、正文、评论区引导和标签。
- `assets/`：预留素材目录；当前版本使用 HTML/CSS 信息图，不依赖外部图片素材。

## 卡片结构

- `card-01.png`：这个仓库到底在干嘛
- `card-02.png`：四层结构：资料层、资产层、生产层、输出层
- `card-03.png`：Pipeline 和 Harness 的区别
- `card-04.png`：一次任务如何从资料流向复用
- `card-05.png`：为什么它能把 AI 设计变成可复盘系统

## 内容来源

主要参考：

- `MAP.md`
- `docs/OUTPUT_SKILL_SPEC.md`
- `README.md`
- `soul.md`

## 图片规格

- 数量：5 张
- 尺寸：1080 x 1350 px
- 比例：4:5
- 格式：PNG
- 风格：浅色说明书、信息图、项目架构可视化

## 导出方式

使用真实浏览器打开 `index.html`，按 `#card-01` 到 `#card-05` 分别截图导出到 `cards/`。

导出后检查：

- PNG 文件存在。
- 每张图片尺寸为 1080 x 1350。
- 中文清晰可读。
- 卡片内容与 `post-copy.md` 一致。
