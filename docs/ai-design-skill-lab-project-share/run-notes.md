# Run Notes：AI Design Skill Lab 项目分享 HTML PPT

## 输入来源

主要参考：

- `MAP.md`
- `docs/OUTPUT_SKILL_SPEC.md`
- `README.md`
- `soul.md`
- `docs/xiaohongshu-repo-purpose-architecture-post/`

## 设计判断

这份 PPT 面向项目分享，不是小红书图文，所以采用横向 16:9 HTML deck。内容重点不是列出所有文件，而是让听众快速理解：

- 这个仓库为什么存在；
- Design Data Factory Pipeline 和 Harness Runtime 的区别；
- Output Skill 在输出层的位置；
- 为什么要把一次 AI 设计工作沉淀成可复用资产。

## 页表

| 页码 | 页面目的 | 版式 |
|---|---|---|
| 01 | 建立项目定位 | 深色封面 + 中心标识 |
| 02 | 说明痛点 | 三卡片 + 主判断 |
| 03 | 说明三类能力 | 三卡片 |
| 04 | 解释四层结构 | 四列分层图 |
| 05 | 解释 Pipeline | 五节点流程 |
| 06 | 解释 Harness | 五节点流程 |
| 07 | 说明当前与未来边界 | 双栏对比 |
| 08 | 说明 Output Skill | 三卡片 + 结论 |
| 09 | 说明端到端流动 | 五节点流程 |
| 10 | 说明目录地图 | 六宫格 |
| 11 | 说明团队价值 | 三卡片 |
| 12 | 总结 | 深色收束页 |

## 自检

- 每页只有一个主要判断。
- 关键架构边界与 `MAP.md` 保持一致：Harness 当前是 mock lifecycle，不调用 Pipeline CLI。
- Output Skill 定位与 `docs/OUTPUT_SKILL_SPEC.md` 保持一致：它是输出层协议，不是模板 vendor。
- HTML 使用内联 CSS 和少量原生 JS，无外部依赖。
- 支持键盘翻页和打印模式。
