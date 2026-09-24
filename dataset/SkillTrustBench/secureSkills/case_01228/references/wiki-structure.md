# 宁德时代业务组 Wiki 知识库结构

## Space 信息
- **Space ID**: 7624480701739519200
- **Space名称**: 宁德时代业务组知识库

## 节点树

```
首页 (XBTFw1mjziSUmAkehtIcZW6on1d / doc: CBDcdaQceoOXYUxlhRpcUVYcncH)
├── 客户档案 (VlezwpfNjibPq2kG26acmX73npb)
│   └── CATL基本信息、产品线、甲方对接人、合作历史
├── 项目文档 (EACHwv9RriIZ2MksEHRcvWMvn7b)
│   └── KOC矩阵运营、RFP海外PR方案、龙虾试验、Q2问题
├── 行业研究 (Q1fxw6BRLiA0twkRfMScZD00nBg)
│   └── 市场规模、竞争地位、关键趋势、政策
├── 内容资产 (WrdcwmfOBirczCk2mGmci0PAn7c)
│   └── 选题池、内容配比、成功案例
├── 流程规范 (Qg5DwFWNbixBorkfxrKcvblznNg)
│   └── 工作流、工具指南、最佳实践
└── 变更记录 (Unwzwu5jNinIb8k3YAtcU86hnCe / doc: XVCRdvMbaoi5nFxpizccv0IBnMb)
    └── 所有agent对wiki的编辑日志
```

## 节点Token速查

| 模块 | node_token | 用途 |
|------|-----------|------|
| 首页 | XBTFw1mjziSUmAkehtIcZW6on1d | 导航门户 |
| 客户档案 | VlezwpfNjibPq2kG26acmX73npb | 甲方信息 |
| 项目文档 | EACHwv9RriIZ2MksEHRcvWMvn7b | 项目交付物 |
| 行业研究 | Q1fxw6BRLiA0twkRfMScZD00nBg | 行业情报 |
| 内容资产 | WrdcwmfOBirczCk2mGmci0PAn7c | 内容库 |
| 流程规范 | Qg5DwFWNbixBorkfxrKcvblznNg | SOP |
| 变更记录 | Unwzwu5jNinIb8k3YAtcU86hnCe | 审计日志 |

## 读取某个模块的流程

1. 用 `feishu_wiki { "action": "get", "token": "<node_token>" }` 获取 `obj_token`
2. 用 `feishu_doc { "action": "read", "doc_token": "<obj_token>" }` 读取内容
3. 如模块下有子节点，用 `feishu_wiki { "action": "nodes", "space_id": "7624480701739519200", "parent_node_token": "<node_token>" }` 列出

## 编辑某个模块的流程

1. 获取 obj_token（同上）
2. 用 `feishu_doc { "action": "write", "doc_token": "<obj_token>", "content": "..." }` 写入
3. **必须**执行 changelog 记录（见 SKILL.md 变更记录章节）
