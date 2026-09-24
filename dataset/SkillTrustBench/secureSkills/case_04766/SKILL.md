---
name: chc
description: Claw Help Claude - OpenClaw manages Claude Code CLI lifecycle. Use when: (1) starting Claude Code CLI sessions via PTY, (2) managing multiple Claude Code instances (create/list/monitor/kill), (3) forwarding messages between user and Claude Code, (4) persisting Claude Code sessions across OpenClaw restarts, (5) user mentions "claude code", "chc", "启动claude", or wants to use Claude Code through OpenClaw.
---

# CHC - Claw Help Claude

OpenClaw 作为中介，管理 Claude Code CLI 的完整生命周期，实现用户与 Claude Code 的双向通信。

## 核心架构

```
用户 → OpenClaw → Claude Code CLI (PTY) → 代码/项目
                    ↓
              多实例管理
```

**关键点：**
- Claude Code CLI 通过 PTY (伪终端) 运行，而非直接 API
- OpenClaw 作为消息路由器，转发双方交互
- 支持同时运行多个独立 Claude Code 实例
- 会话持久化在 `~/.claude/sessions/`

## 会话生命周期

### 1. 启动 Claude Code 会话

使用 `sessions_spawn` 创建后台 PTY 会话：

```json
{
  "runtime": "acp",
  "mode": "session",
  "thread": true,
  "agentId": "claude-code",
  "cwd": "/path/to/project",
  "label": "project-name"
}
```

**参数说明：**
- `runtime: "acp"` - ACP 模式，适合 Claude Code CLI
- `mode: "session"` - 持久化会话（推荐）
- `thread: true` - 线程绑定，便于追踪
- `cwd` - Claude Code 工作目录

### 2. 发送消息到 Claude Code

使用 `sessions_send` 或直接 PTY write：

```json
{
  "sessionKey": "young-falcon",
  "message": "分析这个项目的代码结构"
}
```

PTY 模式（更直接）：
```
process(action=write, sessionId="xxx", data="用户消息")
process(action=send-keys, keys=["Enter"])
```

### 3. 接收 Claude Code 输出

使用 `process(action=poll)` 获取输出：

```json
{
  "action": "poll",
  "sessionId": "young-falcon",
  "timeout": 120000
}
```

### 4. 管理多个实例

查看所有运行的 Claude Code 会话：

```
sessions_list(kinds=["acp"])
subagents(action=list)
```

监控特定会话状态：

```
process(action=poll, sessionId="xxx", limit=100)
```

终止会话：

```
process(action=kill, sessionId="xxx")
```

### 5. 会话恢复

Claude Code 会话持久化在 `~/.claude/sessions/<uuid>.json`

恢复现有会话：
```json
{
  "runtime": "acp",
  "resumeSessionId": "<claude-session-uuid>",
  "agentId": "claude-code"
}
```

## 实例管理最佳实践

### 实例命名约定

使用语义化 label 区分不同项目：
- `young-falcon` - 测试/临时会话
- `hermes-main` - Hermes 项目主会话
- `coding-pr` - PR 审查专用

### 多实例场景

| 场景 | 实例数 | 建议 |
|------|--------|------|
| 单项目开发 | 1 | 保持单一实例 |
| 多项目并行 | 2-3 | 每项目独立实例 |
| PR 审查 + 开发 | 2 | 分离审查实例 |

### 资源监控

定期检查实例状态：
- Token 使用量（通过 Claude Code 输出）
- 运行时长（避免过长会话）
- 响应延迟（判断是否需要重启）

## Claude Code CLI 配置参考

详见 [references/config.md](references/config.md)

关键配置文件：
- `~/.claude/settings.json` - API 配置
- `~/.claude/sessions/*.json` - 会话持久化

## 常见问题

### Q: Claude Code 无响应？
检查：
1. 会话是否仍在运行 (`sessions_list`)
2. PTY 是否卡住（尝试发送空消息唤醒）
3. 是否需要重启实例

### Q: 如何切换项目？
在现有实例中发送：
```
/cd /path/to/new/project
```

或启动新实例指向新目录。

### Q: 会话历史丢失？
Claude Code 自动保存历史到 `~/.claude/sessions/`。
使用 `resumeSessionId` 恢复。

## 资源文件

- `references/config.md` - Claude Code CLI 配置详解
- `scripts/session_manager.py` - 会话管理辅助脚本（可选）