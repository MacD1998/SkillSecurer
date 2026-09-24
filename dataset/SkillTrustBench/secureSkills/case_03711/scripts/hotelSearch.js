#!/usr/bin/env node

/**
 * hotel-recommendation 技能调用脚本 (Node.js版本)
 * 调用方式: node hotelSearch.js "[查询JSON数组]"
 */

const https = require('https');

// 检查参数
if (process.argv.length < 3) {
    console.error("❌ 错误: 请提供查询JSON数组");
    console.log("");
    console.log("使用方法:");
    console.log("  node hotelSearch.js '[查询JSON数组]'");
    console.log("");
    console.log("示例:");
    console.log('  node hotelSearch.js \'[{"subQuery":"大阪酒店推荐","checkInDate":"2026-04-01","checkOutDate":"2026-04-07","city":"大阪","country":"日本","nearby":"梅田"}]\'');
    console.log('  node hotelSearch.js \'[{"subQuery":"东京酒店测试"}]\'');
    process.exit(1);
}

const queryString = process.argv[2];

console.log("🔍 开始酒店搜索");
console.log(`📋 原始查询参数: ${queryString}`);
console.log(`📏 参数字符数: ${queryString.length}`);
console.log("");

let textValue;
try {
    // 解析查询字符串来确定格式
    if (queryString.startsWith('"[') && queryString.endsWith(']"')) {
        // 情况1：已经是引号包裹的JSON字符串，如 "[{...}]"
        console.log("📄 格式: 已序列化JSON字符串");
        textValue = queryString;
    } else if (queryString.startsWith('[') && queryString.endsWith(']')) {
        // 情况2：直接的JSON数组，如 [{...}]
        console.log("📄 格式: 直接JSON数组，自动添加引号");
        textValue = `"${queryString}"`;
    } else {
        // 情况3：其他格式，默认为字符串
        console.log("📄 格式: 其他字符串格式，自动包装");
        // 尝试解析看看是否是有效的JSON数组
        try {
            JSON.parse(queryString);
            // 如果是有效的JSON对象但不是数组，包装成带引号的字符串
            textValue = `"${queryString}"`;
        } catch (e) {
            textValue = `"${queryString}"`;
        }
    }
    
    console.log(`🎯 处理后的text值: ${textValue}`);
    console.log("");
} catch (error) {
    console.error("❌ 参数格式错误:", error.message);
    process.exit(1);
}

// 构建请求数据
const requestData = JSON.stringify({
    "token": "003d2b7d-1ef9-4827-ab9b-cae765689f9d",
    "botId": "2026030610103389649",
    "bizUserId": "2107220265020227",
    "chatContent": {
        "contentType": "TEXT",
        "text": textValue
    },
    "botVariables": {
        "userId": "2107220265020227",
        "serviceType": "RECALL_hotel"
    },
    "stream": false
});

console.log("📦 请求JSON内容:");
console.log(JSON.stringify(JSON.parse(requestData), null, 2));
console.log("");

// 发送HTTP请求
const options = {
    hostname: 'ibotservice.alipayplus.com',
    path: '/almpapi/v1/message/chat',
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(requestData)
    }
};

console.log("📡 调用API...");

const req = https.request(options, (res) => {
    let responseData = '';
    
    res.on('data', (chunk) => {
        responseData += chunk;
    });
    
    res.on('end', () => {
        try {
            const response = JSON.parse(responseData);
            const responseCode = response.code || 0;
            
            console.log(`📊 API响应代码: ${responseCode}`);
            
            if (responseCode === 0) {
                console.log("✅ 查询成功");
                
                // 处理文本结果
                const textContent = response.text || '';
                const contentField = response.content || '';
                
                if (textContent) {
                    console.log("\n📝 文本结果:");
                    console.log("----------------------------------------");
                    console.log(textContent.replace(/\\n/g, '\n').replace(/\\"/g, '"'));
                    console.log("----------------------------------------");
                } else if (contentField) {
                    console.log("\n📊 JSON内容:");
                    console.log("----------------------------------------");
                    
                    // 尝试解析content字段
                    try {
                        const contentData = JSON.parse(contentField);
                        console.log(JSON.stringify(contentData, null, 2));
                    } catch (e) {
                        console.log(contentField.replace(/\\n/g, '\n').replace(/"/g, '"').replace(/\\/g, ''));
                    }
                    
                    console.log("----------------------------------------");
                } else {
                    console.log("\n📦 完整响应:");
                    console.log("----------------------------------------");
                    console.log(JSON.stringify(response, null, 2));
                    console.log("----------------------------------------");
                }
            } else {
                console.log("❌ 查询失败");
                console.log("\n📋 错误信息:");
                console.log("----------------------------------------");
                console.log(JSON.stringify(response, null, 2));
                console.log("----------------------------------------");
                
                if (typeof response === 'string' && response.includes('DOWNSTREAM_BIZ_ERROR')) {
                    console.log("\n⚠️ API状态提示: ");
                    console.log("  1. 检查token和botId是否有效");
                    console.log("  2. 确认serviceType是否正确 (RECALL_hotel)");
                    console.log("  3. 查询参数格式是否符合要求");
                    console.log("  4. 联系API提供方确认服务状态");
                }
            }
            
            // 提取trace信息
            const traceId = response.traceId || '';
            if (traceId) {
                console.log(`\n🔍 Trace ID: ${traceId}`);
            }
            
        } catch (error) {
            console.error("❌ 解析API响应失败:", error.message);
            console.log("\n📋 原始响应:");
            console.log(responseData);
        }
    });
});

req.on('error', (error) => {
    console.error("❌ 网络请求失败:", error.message);
    console.log("\n⚠️ 网络连接提示:");
    console.log("  1. 检查网络连接是否正常");
    console.log("  2. 确认API端点是否可用");
    console.log("  3. 检查代理设置是否正确");
});

req.write(requestData);
req.end();