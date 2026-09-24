# 小红书 API 文档

> 本文档汇总了小红书 Web/移动端常用的数据接口信息，供 crawler.py 和 xhs_client.py 参考。

## 目录

1. [接口基础](#接口基础)
2. [搜索接口](#搜索接口)
3. [笔记接口](#笔记接口)
4. [用户接口](#用户接口)
5. [评论接口](#评论接口)
6. [发布接口](#发布接口)
7. [趋势接口](#趋势接口)
8. [注意事项](#注意事项)

---

## 接口基础

### 基础 URL

| 环境 | URL |
|------|-----|
| Web API | `https://edith.xiaohongshu.com` |
| Web 页面 | `https://www.xiaohongshu.com` |
| 移动 API | `https://edith.xiaohongshu.com` |

### 认证方式

小红书 API 需要 Cookie 认证，核心字段：

```
Cookie: a1=xxx; web_session=xxx; webId=xxx
```

- `a1`：设备指纹，首次访问时服务端下发
- `web_session`：登录态凭证
- `webId`：Web 端唯一标识

### 请求头

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
Accept: application/json, text/plain, */*
Accept-Language: zh-CN,zh;q=0.9
Content-Type: application/json;charset=UTF-8
Origin: https://www.xiaohongshu.com
Referer: https://www.xiaohongshu.com/
X-s: [签名参数]
X-t: [时间戳]
```

### 签名机制（X-s）

小红书使用 X-s 签名防止接口被直接调用。签名算法较为复杂，通常通过以下方式绕过：

1. **浏览器环境**：使用 Playwright/Puppeteer 在真实浏览器中执行请求
2. **逆向工程**：逆向 JS 中的签名生成逻辑
3. **MCP 协议**：通过浏览器自动化 MCP 工具执行

---

## 搜索接口

### 搜索笔记

```
GET /api/sns/web/v1/search/notes
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | ✅ | 搜索关键词 |
| sort | string | ❌ | 排序：general=综合, popularity=最热, latest=最新, correlation=相关 |
| limit | int | ❌ | 每页数量，默认 20，最大 20 |
| offset | int | ❌ | 偏移量 |
| note_type | string | ❌ | 笔记类型过滤：normal=图文, video=视频 |

**响应示例：**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "note_model": {
          "note_id": "xxx",
          "display_title": "标题",
          "desc": "正文内容",
          "type": "normal",
          "time": 1700000000000,
          "interact_info": {
            "liked_count": "1000",
            "collected_count": "500",
            "comment_count": "100",
            "share_count": "50"
          },
          "user": {
            "user_id": "xxx",
            "nickname": "用户名",
            "avatar": "https://..."
          },
          "image_list": [
            {"url_default": "https://..."}
          ],
          "tag_list": [
            {"name": "美妆"}
          ],
          "ip_location": "上海"
        }
      ]
  }
}
```

### 搜索用户

```
GET /api/sns/web/v1/search/users
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | ✅ | 搜索关键词 |
| limit | int | ❌ | 数量，默认 20 |

---

## 笔记接口

### 笔记详情

```
GET /api/sns/web/v1/feed
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| note_id | string | ✅ | 笔记 ID |

### 用户笔记列表

```
GET /api/sns/web/v1/user_posted
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | ✅ | 用户 ID |
| limit | int | ❌ | 数量，默认 30 |
| cursor | string | ❌ | 分页游标 |

---

## 用户接口

### 用户资料

```
GET /api/sns/web/v1/user/otherinfo
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | string | ✅ | 用户 ID |

**响应关键字段：**

```json
{
  "success": true,
  "data": {
    "user": {
      "user_id": "xxx",
      "nickname": "昵称",
      "image": "头像URL",
      "desc": "简介",
      "gender": 0,
      "ip_location": "北京",
      "fans": 10000,
      "follows": 500,
      "interaction": 2000,
      "notes": 100
    }
  }
}
```

### 自己的资料

```
GET /api/sns/web/v1/user/selfinfo
```

---

## 评论接口

### 笔记评论列表

```
GET /api/sns/web/v2/comment/page
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| note_id | string | ✅ | 笔记 ID |
| limit | int | ❌ | 数量，默认 20 |
| cursor | string | ❌ | 分页游标 |

### 发表评论

```
POST /api/sns/web/v1/comment/post
```

**请求体：**

```json
{
  "note_id": "xxx",
  "content": "评论内容",
  "target_comment_id": ""
}
```

### 评论子评论

```
GET /api/sns/web/v2/comment/sub/page
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| note_id | string | ✅ | 笔记 ID |
| root_comment_id | string | ✅ | 父评论 ID |
| limit | int | ❌ | 数量 |

---

## 发布接口

### 创建笔记（图文）

```
POST /api/sns/web/v1/note/create
```

**请求体：**

```json
{
  "title": "笔记标题",
  "desc": "笔记正文",
  "type": "normal",
  "image_ids": ["id1", "id2"],
  "post_time": 1700000000000,
  "is_draft": false
}
```

### 创建笔记（视频）

```json
{
  "title": "笔记标题",
  "desc": "笔记正文",
  "type": "video",
  "video_id": "video_id",
  "cover_id": "cover_id"
}
```

### 上传图片

```
POST /api/sns/web/v1/upload/image
```

Content-Type: `multipart/form-data`

### 上传视频

```
POST /api/sns/web/v1/upload/video
```

支持分片上传。

---

## 趋势接口

### 热搜榜

```
GET /api/sns/web/v1/search/trending
```

### 关键词联想

```
GET /api/sns/web/v1/search/sug
```

**参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| keyword | string | ✅ | 输入关键词 |
| limit | int | ❌ | 联想数量 |

---

## 注意事项

### 频率限制

- 搜索接口：约每分钟 10-20 次
- 笔记接口：约每分钟 30 次
- 评论接口：约每分钟 20 次
- 发布接口：约每分钟 5 次

### 反爬策略

1. **请求间隔**：每次请求间隔 1.5-3 秒
2. **User-Agent 轮换**：准备多个 UA
3. **Cookie 轮换**：多账号轮换使用
4. **IP 管理**：避免单 IP 高频请求
5. **随机延迟**：在固定间隔基础上加入随机延迟

### 数据限制

- 搜索结果最多翻约 20 页（400 条）
- 用户笔记列表最多翻约 100 页
- 评论最多获取约 1000 条
- 部分私密笔记无法获取

### 合规说明

- 请遵守小红书平台规则和robots.txt
- 不要用于商业爬取或数据倒卖
- 不要恶意大量请求影响平台正常运营
- 数据仅用于个人运营分析和优化
