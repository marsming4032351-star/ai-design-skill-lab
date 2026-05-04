# Design Asset Classification Rules

Use these rules for first-pass classification. The goal is a useful staging taxonomy, not perfect final curation.

## Evidence Priority

1. Folder names and nearby project context.
2. File extension and media type.
3. Filename tokens.
4. Extracted text from PDF or document files, when available.
5. Visual analysis or OCR, when explicitly enabled later.

## Category Rules

### poster

Signals: `poster`, `海报`, `keyvisual`, `kv`, `campaign`, `event`, `banner`, `social`, `print`, `主视觉`, `活动`.

Common files: `.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.psd`, `.ai`, `.pdf`.

### space

Signals: `space`, `interior`, `retail`, `exhibition`, `booth`, `store`, `render`, `3d`, `空间`, `展厅`, `展陈`, `门店`, `效果图`, `施工`, `平面`.

Common files: renders, floor plans, elevations, PDFs, CAD exports.

### soft-decoration

Signals: `soft`, `furniture`, `material`, `textile`, `fabric`, `lighting`, `prop`, `moodboard`, `软装`, `家具`, `面料`, `材质`, `灯具`, `摆件`, `配色`.

Common files: reference images, material boards, vendor PDFs.

### brand

Signals: `brand`, `logo`, `identity`, `vi`, `guideline`, `typography`, `color`, `packaging`, `品牌`, `标志`, `字体`, `色彩`, `包装`, `视觉识别`.

Common files: brand books, logo exports, color cards, identity layouts.

### proposal

Signals: `proposal`, `deck`, `plan`, `方案`, `报价`, `提案`, `汇报`, `presentation`, `brief`.

Common files: `.pdf`, `.ppt`, `.pptx`, `.doc`, `.docx`, `.key`.

### process

Signals: `draft`, `v1`, `v2`, `rev`, `sketch`, `wireframe`, `screenshot`, `过程`, `草稿`, `修改`, `迭代`, `截图`.

Common files: working images, screenshots, editable design files.

### reference

Signals: `reference`, `benchmark`, `inspiration`, `research`, `mood`, `案例`, `参考`, `竞品`, `灵感`, `资料`, `调研`.

Common files: downloaded images, screenshots, saved articles, research PDFs.

## Confidence

- `high`: folder and filename both agree, or document text strongly matches one category.
- `medium`: one strong signal appears.
- `low`: only extension/media type is known.
- `needs_review`: multiple categories conflict, source is ambiguous, or classification would affect archive placement.

## Grouping

Prefer grouping related files by shared basename, folder, or version pattern. For example, `project-kv-v1.jpg`, `project-kv-v2.jpg`, and `project-kv-final.pdf` should be treated as one asset family with multiple variants.
