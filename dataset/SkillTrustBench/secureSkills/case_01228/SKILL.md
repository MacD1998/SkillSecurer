---
name: catl-wiki
description: |
  CATL (宁德时代) project wiki knowledge base — shared across all agents.
  Activate when: (1) looking up CATL client info, project docs, industry research, content assets, or SOPs,
  (2) adding/updating wiki content for the CATL project, (3) user mentions 宁德wiki, 知识库, client profile,
  项目文档, 行业研究, or any CATL project knowledge query. Provides wiki node mapping, read/write workflows,
  and mandatory changelog tracking. NOT for: non-CATL wikis, general feishu doc editing unrelated to the
  knowledge base, or feishu drive/permission management.
---

# CATL Wiki Knowledge Base

Shared knowledge base for the 宁德时代 (CATL) project team, hosted on Feishu Wiki.

## Quick Reference

- **Space ID**: 7624480701739519200
- **Modules**: 客户档案 / 项目文档 / 行业研究 / 内容资产 / 流程规范 / 变更记录

Full node token mapping: see [references/wiki-structure.md](references/wiki-structure.md)

## Reading Content

1. Identify the module from the table in wiki-structure.md
2. Get the doc token:
   
3. Read content:
   
4. For sub-pages, list children:
   

## Writing / Updating Content

1. Get obj_token (same as reading step 2)
2. Write content:
   
3. **MANDATORY — Log the change** (both steps required):

### Step A: Local changelog
Done: [2026-04-07 07:23 UTC] <your_agent_name> -> <module>: <summary>

### Step B: Feishu wiki changelog page
Append a line to the 变更记录 wiki page:

The changelog node token is in wiki-structure.md.

> **Skipping changelog = violation.** Every wiki edit must be logged in both places.

## Creating New Pages

To add a sub-page under an existing module:

After creating, update wiki-structure.md with the new node token, and log the change.

## Module Guide

| Module | What belongs here |
|--------|-------------------|
| 客户档案 | CATL company info, products, contacts, collaboration history |
| 项目文档 | KOC plans, RFP proposals, meeting notes, deliverables |
| 行业研究 | Market data, competitor intel, policy trends, tech analysis |
| 内容资产 | Topic pools, scripts, content ratios, case studies |
| 流程规范 | Workflows, tool guides, best practices, templates |
| 变更记录 | Auto-maintained — do not manually edit except via changelog process |

## Notes

- Feishu docx blocks batch limit: ≤20 per API call
- Block type 2 (text) is the safe default for children blocks
- Insert at index=0 for prepend, omit for append
