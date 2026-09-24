---
name: tcm-clinic
version: 1.0.0
description: 一人中医诊所全流程管理工具。通过自然语言对话完成患者管理、病历记录（四诊信息、辨证论治、处方）、中药库存管理（入库、盘点、低库存预警）、预约排班、财务记账与统计。数据以 Excel 格式存储。Use when: 用户提到患者、病历、处方、中药、库存、预约、挂号、排班、收费、财务、诊所、诊金、药费，或需要诊所日常经营管理操作。NOT for: 中医学理论探讨、方剂学术研究、中药材药理学分析。
author: Phal studio
license: MIT
homepage: https://github.com/your-username/tcm-clinic
category: healthcare
tags: ["中医", "诊所", "病历", "处方", "库存", "预约", "财务"]
allowed-tools: [bash, read_file, write_to_file, search_content]
---

# 中医诊所管理系统 (TCM Clinic)

## 概述

本 Skill 为一人经营的中医诊所提供轻量级全流程管理能力，涵盖五大模块：

| 模块 | 触发词示例 |
|------|-----------|
| 🏥 患者档案 | 新患者、建档、查患者、找患者 |
| 📋 病历记录 | 写病历、四诊、辨证、处方、历史病历、电子病历、导出PDF |
| 🌿 中药库存 | 入库、进药、查库存、低库存预警、配药扣减 |
| 📅 预约排班 | 预约、挂号、今日预约、排班 |
| 💰 财务收费 | 收费、记账、统计、月报、报表 |
| 📊 汇总报表 | 生成报表、汇总表、打印报表、导出Excel、经营概况 |

所有数据以结构化 Excel 文件存储在 `clinic_data/` 目录下。

## When to Run

- 用户要求登记新患者或查询患者信息
- 用户需要记录或查看病历、处方
- 用户提到中药入库、查库存、缺药预警
- 用户需要管理预约、查看今日排班
- 用户要求收费记账、生成收入报表
- 用户发起"接诊"请求（一站式看诊流程）
- 用户要求"初始化诊所"（首次使用）
- 用户要求生成汇总报表、打印数据表、导出经营概况
- 用户要求生成电子病历 PDF、导出病历发给患者

## Workflow

### 决策路由

根据用户意图路由到对应模块：

```
用户请求
├── 患者相关？ → 患者管理模块
│   ├── "新患者建档" → 创建患者记录
│   ├── "查患者" / "找患者" → 按姓名/手机号/ID 查询
│   ├── "改患者信息" → 更新患者档案
│   └── "患者列表" / "所有患者" → 输出患者汇总
├── 病历相关？ → 病历记录模块
│   ├── "写病历" / "记病历" → 新增病历（含四诊、辨证、处方）
│   ├── "查病历" / "历史病历" → 按患者查询历史就诊记录
│   ├── "改病历" → 修改已有病历
│   ├── "电子病历" / "导出PDF" / "发给患者" → 生成 PDF 电子病历
│   └── "病历汇总" → 生成患者全部病历 PDF
├── 药材相关？ → 中药库存模块
│   ├── "入库" / "进药" / "采购" → 新增药材或增加库存
│   ├── "查库存" / "药材库存" → 查询库存状况
│   ├── "低库存" / "缺药" → 低库存预警报告
│   ├── "出库" / "配药扣减" → 减少库存
│   └── "库存盘点" → 生成库存盘点表
├── 预约相关？ → 预约排班模块
│   ├── "预约" / "挂号" / "排班" → 新增预约
│   ├── "今日预约" / "今天的病人" → 查看当日排班
│   └── "改预约" / "取消预约" → 修改预约状态
├── 财务相关？ → 财务记账模块
│   ├── "收费" / "记账" / "收诊金" → 新增财务记录
│   ├── "查账" / "收入" / "流水" → 查询财务记录
│   ├── "统计" / "报表" / "月报" → 生成收入统计报表
│   └── "患者费用" / "欠费" → 查询患者费用汇总
├── 报表相关？ → 报表生成模块
│   ├── "生成报表" / "导出Excel" → 生成诊所汇总报表
│   ├── "打印报表" / "打印数据" → 生成适合打印的汇总表
│   └── "经营概况" / "诊所概况" → 生成经营分析报表
└── 综合请求？ → 多模块联动
    ├── "接诊" → 预约→病历→收费 一站式流程
    ├── "诊所报表" / "经营分析" → 综合经营数据报告
    └── "今日汇总" → 当日各模块数据汇总
```

### 初始化新诊所

首次使用或用户要求"初始化"时，执行：

```bash
python3 SKILL_DIR/scripts/clinic_manager.py init
```

这将在当前工作目录下创建 `clinic_data/` 文件夹，包含 5 个空数据表（仅含表头行）。

### 脚本调用规范

使用 `bash` 工具执行以下命令格式：

```bash
python3 SKILL_DIR/scripts/clinic_manager.py <module> <action> [options...]
```

> **`SKILL_DIR`** 需要替换为 Skill 的实际安装路径。
> 例如：`~/.codebuddy/skills/tcm-clinic` 或 `~/.openclaw/workspace/skills/tcm-clinic`

#### 常用命令

```bash
# 初始化
python3 SKILL_DIR/scripts/clinic_manager.py init

# 患者管理
python3 SKILL_DIR/scripts/clinic_manager.py patients add --name "张三" --gender "男" --phone "13800138000"
python3 SKILL_DIR/scripts/clinic_manager.py patients search --name "张"
python3 SKILL_DIR/scripts/clinic_manager.py patients list

# 病历管理
python3 SKILL_DIR/scripts/clinic_manager.py records add --patient-id "P20260402001" --complaint "头痛三日" --diagnosis "风寒头痛"
python3 SKILL_DIR/scripts/clinic_manager.py records search --patient-id "P20260402001"

# 中药库存
python3 SKILL_DIR/scripts/clinic_manager.py herbs add --name "黄芪" --quantity 500 --unit "g" --category "补气药" --purchase-price 0.15 --min-stock 100
python3 SKILL_DIR/scripts/clinic_manager.py herbs update --herb-id "H001" --quantity -50
python3 SKILL_DIR/scripts/clinic_manager.py herbs alerts
python3 SKILL_DIR/scripts/clinic_manager.py herbs list

# 预约排班
python3 SKILL_DIR/scripts/clinic_manager.py appointments add --patient-id "P20260402001" --time-slot "上午"
python3 SKILL_DIR/scripts/clinic_manager.py appointments today

# 财务统计
python3 SKILL_DIR/scripts/clinic_manager.py finance add --patient-id "P20260402001" --type "挂号费" --amount 50 --payment-method "微信"
python3 SKILL_DIR/scripts/clinic_manager.py finance summary --period day
python3 SKILL_DIR/scripts/clinic_manager.py finance summary --period month --month 2026-04

# 生成汇总报表（打印用）
python3 SKILL_DIR/scripts/clinic_manager.py report
python3 SKILL_DIR/scripts/clinic_manager.py report --limit 50  # 病历/预约显示50条

# 生成电子病历 PDF（用于微信发送）
python3 SKILL_DIR/scripts/clinic_manager.py records export-pdf --patient-id "P20260402001"
python3 SKILL_DIR/scripts/clinic_manager.py records export-pdf --patient-id "P20260402001" --record-id "R20260409001"
```

### 使用策略

- **简单查询和标准 CRUD**：直接调用脚本命令，解析 JSON 输出结果
- **复杂业务逻辑**（如一站式接诊、多模块联动）：结合对话式交互与脚本命令，先查询数据再处理
- **报表生成**：脚本提供基础统计，进一步格式化为 Markdown 表格
- **打印报表**：使用 `report` 命令生成格式美观的 Excel 汇总表，适合查阅和打印

### 数据操作原则

1. **首次使用前检查**：确认 `clinic_data/` 目录存在，不存在则提示用户初始化
2. **新增操作**：自动生成 ID，校验必填字段，追加新行
3. **修改操作**：根据 ID 定位目标行，仅更新指定字段
4. **删除操作**：标记为"作废"或"取消"，不物理删除
5. **关联更新**：新增病历时自动更新患者的 `last_visit_date` 和 `visit_count`

### 一站式接诊流程

当用户发起"接诊"请求时，按以下顺序执行：

1. 确认或选择患者（从已有患者中选择或新建档案）
2. 查看该患者的历史病历摘要（最近一次诊断和处方）
3. 记录本次就诊的四诊信息（望闻问切）、辨证论治和处方
4. 计算费用（挂号费 + 药费等）并生成财务记录
5. 若涉及中药处方，自动扣减对应药材库存并检查低库存
6. 输出本次接诊的完整摘要

### ID 生成规则

- 患者ID: `P` + `YYYYMMDD` + 3位序号（如 `P20260402001`）
- 病历ID: `R` + `YYYYMMDD` + 3位序号
- 预约ID: `A` + `YYYYMMDD` + 3位序号
- 财务ID: `F` + `YYYYMMDD` + 3位序号
- 药材ID: `H` + 3位序号（如 `H001`，不按日期）
- 序号从现有数据中自动递增

## 数据字段参考

执行数据操作前，读取 `references/data-schema.md` 获取完整的字段定义（字段名、类型、是否必填、取值范围）。

主要数据表：
- `clinic_data/patients.xlsx` — 患者信息（姓名、性别、年龄、联系方式、体质类型、过敏史等）
- `clinic_data/medical_records.xlsx` — 病历记录（四诊信息、辨证、处方、医嘱）
- `clinic_data/herbs_inventory.xlsx` — 中药库存（药材名、规格、库存量、价格、保质期、最低库存）
- `clinic_data/appointments.xlsx` — 预约排班（日期、时段、患者、状态）
- `clinic_data/finances.xlsx` — 财务记录（就诊ID、费用类型、金额、支付方式）

## Output Format

- 查询结果使用 Markdown 表格展示，关键数据 **加粗**
- 涉及金额时精确到分（如 `¥120.50`）
- 涉及日期时统一使用 `YYYY-MM-DD` 格式
- 低库存预警使用 ⚠️ 标记
- 操作成功使用 ✅ 标记
- 错误信息使用 ❌ 标记
- 对话中使用中医专业术语（四诊合参、辨证论治、理法方药）

## 交互风格

- 对话简洁专业
- 录入数据时，若用户未提供必填字段，主动询问补充
- 执行写操作前，简要确认操作内容
- 报表统计按费用类型和支付方式分组，显示占比

## 汇总报表格式

生成的 `诊所汇总报表_YYYY-MM-DD.xlsx` 包含以下工作表：

| 工作表 | 内容 | 格式特点 |
|--------|------|----------|
| 患者总览 | 全部患者档案 | 隐藏内部ID字段，冻结首行 |
| 近期病历 | 最近 N 条病历（默认30） | 按日期倒序，显示关键诊疗信息 |
| 中药库存 | 当前库存全表 | **低库存行红色背景高亮** |
| 预约记录 | 最近 N 条预约 | 按日期倒序 |
| 收入统计 | 按月汇总的收入数据 | 费用类型分列，含合计行 |
| 经营概况 | 综合仪表盘数据 | 本月就诊数、收入、库存预警等 |

**打印适配**：
- A4 横向纸张，页边距 0.5 英寸
- 自动缩放为页面宽度
- 标题行和表头行冻结
- 斑马纹行底色增强可读性

## 电子病历 PDF 导出

为指定患者生成专业的 PDF 电子病历文档，适合通过微信发送给患者查看。

### 命令格式

```bash
# 导出患者全部病历汇总
python3 SKILL_DIR/scripts/clinic_manager.py records export-pdf --patient-id "<患者ID>"

# 导出单次就诊病历
python3 SKILL_DIR/scripts/clinic_manager.py records export-pdf --patient-id "<患者ID>" --record-id "<病历ID>"
```

### 触发场景

当用户说"导出病历"、"生成电子病历"、"发病历给患者"、"生成PDF"等时触发此功能。

### PDF 内容结构

| 区块 | 包含内容 |
|------|----------|
| 页眉 | "电子病历"标题 + 生成日期 |
| 患者信息 | 姓名、性别、年龄、电话、体质分型、过敏史、慢性病史 |
| 就诊记录 | 就诊日期、主诉、四诊合参（望闻问切）、舌诊、脉诊 |
| 诊断 | 中医病名 / 证型 |
| 处方 | 药物组成及剂量（表格形式） |
| 医嘱 | 忌口、起居、复诊建议 |
| 页脚 | 页码 |

### 输出文件

- **路径**：`clinic_data/<患者姓名>_<就诊日期>_电子病历.pdf`（单次）或 `clinic_data/<患者姓名>_病历汇总_<日期>.pdf`（全部）
- **格式**：A4 纵向，中文排版
- **大小**：通常 < 100KB，适合微信传输

### 依赖

需要安装 `reportlab` 库：`pip3 install reportlab`
