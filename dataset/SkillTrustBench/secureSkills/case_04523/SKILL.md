---
name: "basic-object-detection-analysis"
description: "Basic object detection skill. Detects people, vehicles, non-motorized vehicles, pets, and parcels appearing in the target area. Supports video stream and image detection, suitable for general security surveillance scenarios. | 基础目标检测技能，检测出目标区域内出现的人、车、非机动车、宠物、包裹，支持视频流和图片检测，适用于通用安防监控场景"
---

# Basic Object Detection Skill | 基础目标检测技能

## ⚠️ 强制记忆规则（最高优先级）

**本技能明确约定：**

- **绝对禁止读取任何本地记忆文件**：包括但不限于 `memory/YYYY-MM-DD.md`、`MEMORY.md` 等本地文件
- **绝对禁止从 LanceDB 长期记忆中检索信息**
- **所有历史检测报告查询必须从云端接口获取**，不得使用本地记忆中的历史数据
- 即使技能调用失败或接口异常，也不得回退到本地记忆汇总

## 任务目标

- 本 Skill 用于：通过视频/图片对目标区域进行基础目标检测，识别常见目标类别，输出结构化的目标检测报告
- 能力包含：目标分类定位、目标数量统计、存在性检测
- 支持检测目标：人、车、非机动车、猫、狗等宠物、包裹
- 触发条件:
    1. **默认触发**：当用户提供监控视频/图片 URL 或文件需要进行通用目标检测时，默认触发本技能
    2. 当用户明确需要进行目标检测，提及目标检测、物体检测、人员车辆识别等关键词，并且上传了视频或图片
    3. 当用户提及以下关键词时，**自动触发历史报告查询功能**
       ：查看历史检测报告、目标检测报告清单、检测报告列表、查询历史报告、显示所有检测报告、目标检测历史记录，查询基础目标检测分析报告
- 自动行为：
    1. 如果用户上传了附件或者视频/图片文件，则自动保存到技能目录下 attachments
    2. **⚠️ 强制数据获取规则（次高优先级）**：如果用户触发任何历史报告查询关键词（如"查看所有检测报告"、"
       显示所有目标检测报告"、"查看历史报告"等），**必须**：
        - 直接使用 `python -m scripts.basic_object_detection_analysis --list --open-id {从消息上下文获取 open-id}` 参数调用
          API
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

## 操作步骤

### 🔒 open-id 获取流程控制（强制执行，防止遗漏）

**在执行基础目标检测前，必须按以下优先级顺序获取 open-id：**

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

- **禁止**自行假设或生成 open-id 值（如 object123 等）
- **禁止**跳过 open-id 验证直接调用 API
- **必须**在获取到有效 open-id 后才能继续执行分析
- 如果用户拒绝提供 open-id，说明用途（用于保存和查询目标检测报告记录），并询问是否继续

---

- 标准流程:
    1. **准备媒体输入**
        - 提供监控视频文件路径、网络视频 URL 或现场图片
        - 确保监控画面完整覆盖监测区域，画面稳定
    2. **获取 open-id（强制执行）**
        - 按上述流程控制获取 open-id
        - 如无法获取，必须提示用户提供用户名或手机号
    3. **执行基础目标检测**
        - 调用 `-m scripts.basic_object_detection_analysis` 处理素材（**必须在技能根目录下运行脚本**）
        - 参数说明:
            - `--input`: 本地视频/图片文件路径（使用 multipart/form-data 方式上传）
            - `--url`: 网络视频/图片 URL 地址（API 服务自动下载）
            - `--media-type`: 媒体类型，可选值：video/image，默认 video
            - `--confidence-threshold`: 置信度阈值，低于该分值不输出，默认 0.5
            - `--open-id`: 当前用户的 OpenID/UserId（必填，按上述流程获取）
            - `--list`: 显示基础目标检测历史分析报告列表清单（可以输入起始日期参数过滤数据范围）
            - `--api-key`: API 访问密钥（可选）
            - `--api-url`: API 服务地址（可选，使用默认值）
            - `--detail`: 输出详细程度（basic/standard/json，默认 json）
            - `--output`: 结果输出文件路径（可选）
    4. **查看分析结果**
        - 接收结构化的基础目标检测报告
        - 包含：检测基本信息、各类目标数量、目标位置统计

## 资源索引

- 必要脚本：见 [scripts/basic_object_detection_analysis.py](scripts/basic_object_detection_analysis.py)(用途：调用 API
  进行基础目标检测，本地文件使用 multipart/form-data 方式上传，网络 URL 由 API 服务自动下载)
- 配置文件：见 [scripts/config.py](scripts/config.py)(用途：配置 API 地址、默认参数和媒体格式限制)
- 领域参考：见 [references/api_doc.md](references/api_doc.md)(何时读取：需要了解 API 接口详细规范和错误码时)

## 注意事项

- 仅在需要时读取参考文档，保持上下文简洁
- 支持格式：视频支持 mp4/avi/mov 格式，图片支持 jpg/png/jpeg 格式，最大 100MB
- API 密钥可选，如果通过参数传入则必须确保调用鉴权成功，否则忽略鉴权
- 分析结果仅供安防管理参考，具体处置请按单位相关规定执行
- 禁止临时生成脚本，只能用技能本身的脚本
- 传入的网络地址参数，不需要下载本地，默认地址都是公网地址，api 服务会自动下载
- 当显示历史检测报告清单的时候，从数据 json 中提取字段 reportImageUrl 作为超链接地址，使用 Markdown 表格格式输出，包含"
  报告名称"、"检测时间"、"目标总数"、"点击查看"四列，其中"报告名称"列使用`基础目标检测报告-{记录id}`形式拼接, "点击查看"列使用
  `[🔗 查看报告](reportImageUrl)`
  格式的超链接，用户点击即可直接跳转到对应的完整报告页面。
- 表格输出示例：
  | 报告名称 | 检测时间 | 目标总数 | 点击查看 |
  |----------|----------|----------|----------|
  | 基础目标检测报告-20260312172200001 | 2026-03-12 17:22:00 | 5 | [🔗 查看报告](https://example.com/report?id=xxx) |

## 使用示例

```bash
# 检测本地监控视频（OpenClaw UI 上下文，使用 metadata id 作为 open-id）
python -m scripts.basic_object_detection_analysis --input /path/to/monitor.mp4 --media-type video --open-id openclaw-control-ui

# 检测现场图片，调整置信度阈值（OpenClaw UI 上下文）
python -m scripts.basic_object_detection_analysis --input /path/to/scene.jpg --media-type image --confidence-threshold 0.6 --open-id openclaw-control-ui

# 检测网络监控视频（OpenClaw UI 上下文，使用 metadata id 作为 open-id）
python -m scripts.basic_object_detection_analysis --url https://example.com/monitor.mp4 --media-type video --open-id openclaw-control-ui

# 显示历史检测报告/显示检测报告清单列表/显示历史目标检测报告（自动触发关键词：查看历史检测报告、历史报告、检测报告清单等）
python -m scripts.basic_object_detection_analysis --list --open-id openclaw-control-ui

# 输出精简报告
python -m scripts.basic_object_detection_analysis --input video.mp4 --media-type video --open-id your-open-id --detail basic

# 保存结果到文件
python -m scripts.basic_object_detection_analysis --input video.mp4 --media-type video --open-id your-open-id --output result.json
```
