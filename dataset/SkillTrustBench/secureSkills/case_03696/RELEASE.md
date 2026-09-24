# TCM Clinic - Skill 发布信息

## 📦 基本信息

| 项目 | 内容 |
|------|------|
| **名称** | tcm-clinic |
| **版本** | 1.0.0 |
| **描述** | 一人中医诊所全流程管理工具 |
| **分类** | 医疗健康 / 诊所管理 |
| **标签** | 中医, 诊所, 病历, 处方, 库存, 预约, 财务 |
| **许可证** | MIT |
| **文件大小** | 26 KB |

## 📋 功能清单

### 核心模块
- ✅ 患者档案管理（登记、查询、搜索）
- ✅ 病历记录管理（四诊信息、辨证论治、处方、PDF 导出）
- ✅ 中药库存管理（入库、出库、预警）
- ✅ 预约排班管理（登记、查询、今日队列）
- ✅ 财务收费管理（收费、日/月/患者统计）
- ✅ 汇总报表生成（Excel 多工作表）

### 特色功能
- ⭐ **电子病历 PDF 导出** - 支持微信发送给患者
- ⭐ **完整四诊信息** - 望闻问切舌脉记录
- ⭐ **中医证型支持** - 9 种体质分型
- ⭐ **库存预警** - 低库存和保质期提醒

## 📁 文件结构

```
tcm-clinic-v1.0.0/
├── SKILL.md              # Skill 定义文件（元数据、触发词、使用说明）
├── README.md             # 使用文档
├── LICENSE               # MIT 许可证
├── scripts/
│   └── clinic_manager.py # 主脚本（~64KB，包含所有功能）
└── references/
    └── data-schema.md    # 数据表结构参考文档
```

## 🔧 技术栈

- **语言**: Python 3
- **依赖**: openpyxl (Excel 读写), reportlab (PDF 生成)
- **数据存储**: Excel 文件（clinic_data/ 目录）
- **PDF 生成**: reportlab + 系统自带中文字体

## 🚀 快速开始

```bash
# 安装依赖
pip install openpyxl reportlab

# 初始化
python3 scripts/clinic_manager.py init

# 使用示例
python3 scripts/clinic_manager.py patients add --name "张三" --gender "男"
python3 scripts/clinic_manager.py records export-pdf --patient-id "P20260409001"
```

## 📝 发布历史

### v1.0.0 (2026-04-09)
- 初始版本发布
- 包含 6 大核心模块
- 新增电子病历 PDF 导出功能
- 支持微信发送场景

## 🎯 适用平台

- [x] CodeBuddy (腾讯云代码助手)
- [x] OpenClaw
- [x] 其他支持 SKILL.md 标准的 AI Agent

## 📞 联系方式

- GitHub: [your-repo]
- Email: [your-email]

---

**打包时间**: 2026-04-09  
**打包者**: Skill Developer
