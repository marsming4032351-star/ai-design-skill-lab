# Obsidian Schema

Generated notes should be stable, linkable, and easy to query with Dataview or plain search.

## Folder Proposal

```text
DesignOS/
  00_Inbox_Staging/
  10_Projects/
  20_Assets/
    poster/
    space/
    soft-decoration/
    brand/
    proposal/
    process/
    reference/
  30_Patterns/
  90_Index/
```

The first implementation should write only to `00_Inbox_Staging/` unless the user confirms archive placement.

## Asset Note Frontmatter

```yaml
---
type: design-asset
project: ""
client: ""
category: poster
status: staged
confidence: medium
source_path: ""
source_hash: ""
source_modified: ""
created_at: ""
tags:
  - design-os
  - design-asset
---
```

## Asset Note Body

```markdown
# Asset Title

## Summary

Short factual description of the asset.

## Classification

- Category:
- Confidence:
- Evidence:
- Needs review:

## Visual / Content Notes

- Composition:
- Color:
- Typography:
- Materials:
- Spatial cues:
- Cultural references:

## Reuse Potential

- Useful for:
- Pattern candidates:
- Archive decision:

## Source

- Original path:
- Hash:
- Modified:
```

## Index Note

Create `asset-index.md` with:

- Run metadata.
- Counts by category.
- Low-confidence review queue.
- Links to generated asset notes.

## Naming

Use a readable slug derived from project, category, and original filename. Keep original filename in frontmatter. Do not overwrite existing notes; append a short hash suffix on collision.
