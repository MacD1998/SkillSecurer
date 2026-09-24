---
name: "arrhythmia-early-warning-analysis"
description: "Arrhythmia early warning skill. Based on facial video, identifies abnormal rhythms such as premature beats, atrial fibrillation, tachycardia/bradycardia, assists in early detection of heart health risks. | 心律失常早期预警技能，基于面部视频识别早搏、房颤、心动过速/心动过缓等异常节律，辅助心脏健康风险早发现"
---

# Arrhythmia Early Warning Analysis Tool | 心律失常早期预警分析工具

## ⚠️ 强制记忆规则（最高优先级）

**本技能明确约定：**

- **绝对禁止读取任何本地记忆文件**：包括但不限于 `memory/YYYY-MM-DD.md`、`MEMORY.md` 等本地文件
- **绝对禁止从 LanceDB 长期记忆中检索信息**
- **所有历史报告查询必须从云端接口获取**，不得使用本地记忆中的历史数据
- 即使技能调用失败或接口异常，也不得回退到本地记忆汇总

## 任务目标

- 本 Skill 用于：通过非接触面部视频分析，早期预警心律失常风险
- 能力包含：早搏识别、房颤特征识别、心动过速检测、心动过缓检测、整体风险分级
- **技术原理**：基于面部血流光电容积描记(PPG)提取心率变异性特征，分析心律异常
- **适用场景**：日常家庭心脏健康筛查、心律失常患者居家监测、高危人群定期自我筛查
- **重要声明**：仅作早期风险预警参考，**不替代专业心电图检查和医生诊断**
- 触发条件:
    1. **默认触发**：当用户提供面部视频需要进行心脏健康风险筛查时，默认触发本技能
    2. 当用户明确需要心律失常预警、心脏健康筛查时，提及早搏、房颤、心动过速、心律失常预警、心脏筛查等关键词，并且上传了面部视频
    3. 当用户提及以下关键词时，**自动触发历史报告查询功能**
       ：查看历史预警报告、心律失常报告清单、预警报告列表、查询历史预警报告、显示所有预警报告、心脏风险分析报告，查询心律失常早期预警分析报告
- 自动行为：
    1. 如果用户上传了附件或者视频文件，则自动保存到技能目录下 attachments
    2. **⚠️ 强制数据获取规则（次高优先级）**：如果用户触发任何历史报告查询关键词（如"查看所有预警报告"、"显示心脏筛查记录"、"
       查看历史报告"等），**必须**：
        - 直接使用 `python -m scripts.arrhythmia_early_warning_analysis --list --open-id {从消息上下文获取 open-id}`
          参数调用 API
          查询云端的历史报告数据
        - **严格禁止**：从本地 memory 目录读取历史会话信息、严格禁止手动汇总本地记录中的报告、严格禁止从长期记忆中提取报告
        - **必须统一**从云端接口获取最新完整数据，然后以 Markdown 表格格式输出结果
        - 如果用户未明确提供 open-id，优先从 OpenClaw 消息上下文获取 sender id（如 metadata 中的 id 字段），然后尝试从当前消息上下文的环境变量
          OPENCLAW_SENDER_ID 或者 sender_id 获取，无法获取时则**必须用户提供用户名或者手机号**作为 open-id

## 前置准备

- 依赖说明:scripts 脚本所需的依赖包及版本
  ```
  requests>=2.28.0
  ```

## 采集要求（获得准确结果的前提）

为了获得相对准确的分析结果，请确保：

1. **面部完整出镜**，光线均匀充足，避免背光和强烈阴影
2. **保持相对静止**，视频采集时间建议 **10-30 秒**
3. **避免剧烈运动后立即采集**，建议安静休息几分钟后再采集

## 操作步骤

### 🔒 open-id 获取流程控制（强制执行，防止遗漏）

**在执行心律失常早期预警分析前，必须按以下优先级顺序获取 open-id：**

```
第 1 步：检查用户是否在消息中明确提供了 open-id
        ↓ (未提供)
第 2 步：从当前消息上下文的环境变量中获取 OPENCLAW_SENDER_ID
        ↓ (无法获取)
第 3 步：从当前消息上下文的环境变量中获取 sender_id
        ↓ (无法获取)
第 4 步：从 OpenClaw 消息元数据中获取 id 字段（如 metadata 中的 id/session_id/user_id等）作为 open-id
        ↓ (无法获取)
第 5 步：❗ 必须暂停执行，明确提示用户提供用户名或手机号作为 open-id
```

**⚠️ 关键约束：**

- **禁止**自行假设或生成 open-id 值（如 heart123、arrhythmia456 等）
- **禁止**跳过 open-id 验证直接调用 API
- **必须**在获取到有效 open-id 后才能继续执行分析
- 如果用户拒绝提供 open-id，说明用途（用于保存和查询预警报告记录），并询问是否继续

---

- 标准流程:
    1. **准备面部视频输入**
        - 提供本地视频文件路径或网络视频 URL
        - 确保面部完整出镜，光线充足，采集时长10-30秒
    2. **获取 open-id（强制执行）**
        - 按上述流程控制获取 open-id
        - 如无法获取，必须提示用户提供用户名或手机号
    3. **执行心律失常早期预警分析**
        - 调用 `-m scripts.arrhythmia_early_warning_analysis` 处理视频（**必须在技能根目录下运行脚本**）
        - 参数说明:
            - `--input`: 本地视频文件路径（使用 multipart/form-data 方式上传）
            - `--url`: 网络视频 URL 地址（API 服务自动下载）
            - `--open-id`: 当前用户的 OpenID/UserId（必填，按上述流程获取）
            - `--list`: 显示历史心律失常早期预警分析报告列表清单（可以输入起始日期参数过滤数据范围）
            - `--api-key`: API 访问密钥（可选）
            - `--api-url`: API 服务地址（可选，使用默认值）
            - `--detail`: 输出详细程度（basic/standard/json，默认 json）
            - `--output`: 结果输出文件路径（可选）
    4. **查看分析结果**
        - 接收结构化的心律失常早期预警分析报告
        - 包含：采集基本信息、平均心率、异常类型识别、风险等级、生活建议和就医提示

## 资源索引

- 必要脚本：见 [scripts/arrhythmia_early_warning_analysis.py](scripts/arrhythmia_early_warning_analysis.py)(用途：调用 API
  进行心律失常早期预警分析，本地文件使用 multipart/form-data 方式上传，网络 URL 由 API 服务自动下载)
- 配置文件：见 [scripts/config.py](scripts/config.py)(用途：配置 API 地址、默认参数和格式限制)
- 领域参考：见 [references/api_doc.md](references/api_doc.md)(何时读取：需要了解 API 接口详细规范和错误码时)

## 注意事项

- 仅在需要时读取参考文档，保持上下文简洁
- 支持格式：mp4/avi/mov，最大 100MB
- API 密钥可选，如果通过参数传入则必须确保调用鉴权成功，否则忽略鉴权
- **⚠️ 非常重要声明**：本分析结果仅供健康风险早期预警参考，**不能替代专业心电图检查和心内科医生诊断**。发现高风险请及时就医检查确诊
- 禁止临时生成脚本，只能用技能本身的脚本
- 传入的网路地址参数，不需要下载本地，默认地址都是公网地址，api 服务会自动下载
- 当显示历史分析报告清单的时候，从数据 json 中提取字段 reportImageUrl 作为超链接地址，使用 Markdown 表格格式输出，包含"
  报告名称"、"平均心率"、"异常类型"、"风险等级"、"分析时间"、"点击查看"六列，其中"报告名称"列使用`心律失常早期预警报告-{记录id}`
  形式拼接, "点击查看"列使用
  `[🔗 查看报告](reportImageUrl)`
  格式的超链接，用户点击即可直接跳转到对应的完整报告页面。
- 表格输出示例：
  | 报告名称 | 平均心率 | 异常类型 | 风险等级 | 分析时间 | 点击查看 |
  |----------|----------|----------|----------|----------|----------|
  | 心律失常早期预警报告 -20260329000100001 | 75次/分 | 偶发早搏 | 低风险 | 2026-03-29 00:
  10 | [🔗 查看报告](https://example.com/report?id=xxx) |

## 使用示例

```bash
# 分析本地面部采集视频（OpenClaw UI 上下文，使用 metadata id 作为 open-id）
python -m scripts.arrhythmia_early_warning_analysis --input /path/to/face.mp4 --open-id openclaw-control-ui

# 分析网络视频（OpenClaw UI 上下文，使用 metadata id 作为 open-id）
python -m scripts.arrhythmia_early_warning_analysis --url https://example.com/face.mp4 --open-id openclaw-control-ui

# 显示历史预警报告/显示预警报告清单列表/显示历史心脏筛查（自动触发关键词：查看历史预警报告、历史报告、预警报告清单等）
python -m scripts.arrhythmia_early_warning_analysis --list --open-id openclaw-control-ui

# 输出精简报告
python -m scripts.arrhythmia_early_warning_analysis --input face.mp4 --open-id your-open-id --detail basic

# 保存结果到文件
python -m scripts.arrhythmia_early_warning_analysis --input face.mp4 --open-id your-open-id --output result.json
```
