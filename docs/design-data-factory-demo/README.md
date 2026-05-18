# Design Data Factory HTML Demo

## 类型

`Presentation Output / HTML 演示页 / PPT 风格页面`

## 样例说明

这是一个可直接在浏览器打开的单文件 HTML 演示页，用来展示 `AI Design Skill Lab / Design Data Factory` 的项目定位、仓库结构、Pipeline / Harness / Output 的关系，以及输出样例归档方式。

它属于 Output Skill 的输出样例，不属于主流程代码。

## 源文件

- 原始来源：`/Users/ming/Desktop/临时/Design Data Factory_ming.html`
- 归档副本：`docs/design-data-factory-demo/index.html`

## 本地打开

直接在浏览器中打开：

```bash
open docs/design-data-factory-demo/index.html
```

## PDF 输出

- 输出路径：`docs/design-data-factory-demo/exports/design-data-factory-demo.pdf`
- 生成页数：12 页
- 生成工具：`weasyprint`
- 打印样式：使用临时样式表设置横向 `16in x 9in` 页面尺寸

## 资源检查

归档前检查了 `index.html`，未发现外链 CSS / JS / 图片，也未发现本地绝对路径资源引用。页面是自包含 HTML。

## 与 `docs/OUTPUT_SKILL_SPEC.md` 的关系

本样例对应 `docs/OUTPUT_SKILL_SPEC.md` 中的 `Presentation Output` 路线，用来验证：

- HTML 演示页如何被组织成可交付资产
- 如何从 HTML 导出 PDF
- 如何把输出样例和归档目录一起沉淀
- 如何保持输出样例和主流程代码分离

## 为什么它是输出样例，不是主流程代码

- 它是单独的成品演示页，不承担 Pipeline / Harness 的执行逻辑
- 它不修改仓库核心运行时，也不提供新的任务路由
- 它的价值在于展示输出能力、归档格式和复用方式，而不是定义新的业务流程

