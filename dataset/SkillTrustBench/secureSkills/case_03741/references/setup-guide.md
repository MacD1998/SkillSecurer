# 环境配置指南

## 步骤 1：检查 mcporter 是否安装

```bash
mcporter --version
```

**如未安装**，按以下流程安装：

```bash
# 1. 通过 npm 全局安装
npm install -g mcporter

# 2. 验证安装
mcporter --version
```

## 步骤 2：检查 MCP 服务配置

```bash
# 列出所有已配置的 MCP 服务
mcporter list
```

**预期输出**（必须包含以下两个服务）：
- jy-financedata-tool
- jy-financedata-api

**如服务未配置**，需要获取 JY_API_KEY 并配置。

### 2.1 获取 JY_API_KEY

向恒生聚源官方邮箱发送邮件申请签发 数据地图 JY_API_KEY，用于接口鉴权。

**申请邮箱**：datamap@gildata.com

**邮件标题**：数据地图 KEY 申请-XX 公司 - 申请人姓名

**正文模板**：
```
• 姓名：
• 手机号：
• 公司/单位全称：
• 所属部门：
• 岗位：
• MCP_KEY 申请用途：
• Skill 申请列表：
• 是否需要 Skill 安装包：（是，邮件提供/否，自行下载）
• 其他补充说明（可选）：
```

申请通过后，恒生聚源将默认发送【工具版和接口版】KEY。

另外，【Skill】包可通过 https://clawhub.ai/ 自行选择下载，若需要我们通过邮件提供【Skill】，亦可在邮件中注明。

### 2.2 配置 MCP 服务

```bash
# 配置 jy-financedata-tool 服务
mcporter config add jy-financedata-tool --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-tool?token=你的 JY_API_KEY"

# 配置 jy-financedata-api 服务
mcporter config add jy-financedata-api --url "https://api.gildata.com/mcp-servers/aidata-assistant-srv-api?token=你的 JY_API_KEY"
```

### 2.3 验证配置

```bash
mcporter list
```

确认输出中包含 `jy-financedata-tool` 和 `jy-financedata-api` 两个服务。

### 2.4 使用方式

```bash
# 基础键值对传参
mcporter call 服务名称。工具 参数=值

# 示例，注意：所有服务工具的入参均为 query
mcporter call jy-financedata-api.StockBelongIndustry query="电子行业 代表性上市公司 龙头股"
```

## 步骤 3：在 OpenClaw 中启用 mcporter（如未配置）

### 配置文件路径

**mcporter 配置文件路径**：
- Windows: `C:\Users\你的用户名\config\mcporter.json`
- Linux/MacOS: `/root/config/mcporter.json`

**OpenClaw 配置文件路径**：
- Windows: `C:\Users\你的用户名\.openclaw\openclaw.json`
- Linux/MacOS: `~/.openclaw/openclaw.json`

### 编辑 openclaw.json

在 skills 部分添加 mcporter 配置：

```json
{
  "skills": {
    "entries": {
      "mcporter": {
        "enabled": true,
        "env": {
          "MCPORTER_CONFIG": "C:\\Users\\你的用户名\\config\\mcporter.json"
        }
      }
    }
  }
}
```

### 重启 OpenClaw

```bash
openclaw gateway restart
```

## 快速验证

完成配置后，运行以下命令验证：

```bash
# 1. 验证 mcporter
mcporter --version

# 2. 验证服务配置
mcporter list

# 3. 测试调用（替换为实际产品代码）
mcporter call jy-financedata-tool.ProductBasicInfoList query="PR202401001"
```

如测试调用返回数据，说明配置成功。
