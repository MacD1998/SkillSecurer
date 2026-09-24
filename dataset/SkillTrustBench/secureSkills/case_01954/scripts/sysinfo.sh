#!/bin/bash
# quick-sysinfo: 快速获取本机系统信息
# 用法: sysinfo.sh [模块]
# 模块: all, cpu, mem, disk, net, env, load, proc, gpu, docker

MODULE="${1:-all}"

case "$MODULE" in
  cpu)
    echo "=== CPU 信息 ==="
    lscpu | grep -iE "^(Architecture|型号名称|Model name|CPU\(s\)|Thread|Core|Socket|CPU MHz|CPU 系列)" 2>/dev/null
    echo ""
    echo "=== CPU 使用率 ==="
    top -bn1 | head -5
    ;;
  mem)
    echo "=== 内存信息 ==="
    free -h
    echo ""
    echo "=== Swap ==="
    swapon --show 2>/dev/null || free -h | grep -iE "swap|交换" || echo "无 Swap"
    ;;
  disk)
    echo "=== 磁盘使用 ==="
    df -h | grep -E "^/dev|tmpfs"
    echo ""
    echo "=== IO 统计 (1秒采样) ==="
    iostat -x 1 1 2>/dev/null || echo "iostat 未安装"
    ;;
  net)
    echo "=== 网络接口 ==="
    ip -brief addr 2>/dev/null || ifconfig | grep -E "^[a-z]|inet "
    echo ""
    echo "=== 连接数 ==="
    ss -s 2>/dev/null | head -10
    ;;
  env)
    echo "=== 系统环境 ==="
    echo "主机名: $(hostname)"
    echo "系统: $(uname -sr)"
    echo "发行版: $(cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "内核: $(uname -r)"
    echo "架构: $(uname -m)"
    echo "启动时间: $(uptime -s 2>/dev/null || who -b)"
    echo "当前用户: $(whoami)"
    echo "Shell: $SHELL"
    echo "Node: $(node -v 2>/dev/null || echo '未安装')"
    echo "Python: $(python3 --version 2>/dev/null || echo '未安装')"
    echo "Docker: $(docker --version 2>/dev/null || echo '未安装')"
    ;;
  load)
    echo "=== 系统负载 ==="
    uptime
    echo ""
    echo "=== Top 10 进程 (CPU) ==="
    ps aux --sort=-%cpu | head -11
    echo ""
    echo "=== Top 10 进程 (内存) ==="
    ps aux --sort=-%mem | head -11
    ;;
  proc)
    echo "=== 进程统计 ==="
    echo "总进程数: $(ps aux | wc -l)"
    echo "运行中: $(ps aux | awk '$8=="R"{c++}END{print c+0}')"
    echo "睡眠中: $(ps aux | awk '$8=="S"{c++}END{print c+0}')"
    echo ""
    echo "=== 关键服务状态 ==="
    for svc in sshd docker nginx openclaw-gateway; do
      status=$(systemctl is-active $svc 2>/dev/null || echo "unknown")
      echo "$svc: $status"
    done
    ;;
  gpu)
    echo "=== GPU 信息 ==="
    if command -v nvidia-smi &>/dev/null; then
      nvidia-smi --query-gpu=name,temperature.gpu,memory.used,memory.total,utilization.gpu --format=csv,noheader
    elif command -v rocm-smi &>/dev/null; then
      rocm-smi --showtemp --showmemuse --showuse
    else
      lspci | grep -i vga
    fi
    ;;
  docker)
    echo "=== Docker 容器 ==="
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker 未安装或无权限"
    echo ""
    echo "=== Docker 资源 ==="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "无运行中容器"
    ;;
  openclaw)
    echo "=== OpenClaw 配置 ==="
    OC_BIN="/home/kele/.nvm/versions/node/v22.22.2/bin/openclaw"
    echo "版本: $($OC_BIN --version 2>/dev/null || echo '未知')"
    echo ""
    echo "=== Gateway ==="
    echo "端口: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('gateway',{}).get('port','未知'))" 2>/dev/null)"
    echo "绑定: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('gateway',{}).get('bind','未知'))" 2>/dev/null)"
    echo "认证: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('gateway',{}).get('auth',{}).get('mode','未知'))" 2>/dev/null)"
    echo ""
    echo "=== Agent ==="
    echo "默认模型: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('agents',{}).get('defaults',{}).get('model',{}).get('primary','未知'))" 2>/dev/null)"
    echo "工作目录: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('agents',{}).get('defaults',{}).get('workspace','未知'))" 2>/dev/null)"
    echo ""
    echo "=== 频道 ==="
    python3 -c "
import json
c=json.load(open('/home/kele/.openclaw/openclaw.json'))
ch = c.get('channels',{})
for name, conf in ch.items():
    enabled = conf.get('enabled', '未设置')
    print(f'  {name}: {enabled}')
" 2>/dev/null
    echo ""
    echo "=== 插件 ==="
    python3 -c "
import json
c=json.load(open('/home/kele/.openclaw/openclaw.json'))
plugins = c.get('plugins',{})
allow = plugins.get('allow', [])
installs = plugins.get('installs', {})
print(f'  白名单: {allow}')
for name, info in installs.items():
    ver = info.get('version', '?')
    print(f'  {name}: v{ver}')
" 2>/dev/null
    echo ""
    echo "=== 服务状态 ==="
    systemctl --user is-active openclaw-gateway 2>/dev/null || echo "  gateway: 未知"
    echo "  监听: $(ss -tlnp | grep 18789 | awk '{print $4}' || echo '未知')"
    echo ""
    echo "=== Session 概览 ==="
    ls /home/kele/.openclaw/agents/ 2>/dev/null | while read agent; do
      echo "  Agent: $agent"
    done
    ;;
  all|*)
    echo "📊 系统概览"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🖥️ 主机: $(hostname) | $(uname -sr)"
    echo "⏰ 运行: $(uptime -p 2>/dev/null || uptime)"
    echo ""
    echo "🧠 CPU:"
    cpu_model=$(lscpu | grep -i "型号名称\|Model name" | awk -F'：' '{print $2}' | sed 's/^[[:space:]]*//')
    [[ -z "$cpu_model" ]] && cpu_model=$(lscpu | grep -i "Model name" | awk -F':' '{print $2}' | sed 's/^[[:space:]]*//')
    echo "  ${cpu_model:-未知}"
    echo "  核心: $(nproc) | 负载: $(cat /proc/loadavg | cut -d' ' -f1-3)"
    echo ""
    echo "💾 内存:"
    free -h | grep -iE "Mem|内存" | awk '{printf "  总计: %s | 已用: %s | 可用: %s\n", $2, $3, $7}'
    echo ""
    echo "💿 磁盘:"
    df -h / | tail -1 | awk '{printf "  总计: %s | 已用: %s (%s) | 可用: %s\n", $2, $3, $5, $4}'
    echo ""
    echo "🌐 网络:"
    ip -4 addr show | grep inet | grep -v 127.0.0.1 | awk '{printf "  %s: %s\n", $NF, $2}'
    echo ""
    echo "🤖 OpenClaw:"
    echo "  模型: $(python3 -c "import json; c=json.load(open('/home/kele/.openclaw/openclaw.json')); print(c.get('agents',{}).get('defaults',{}).get('model',{}).get('primary','未知'))" 2>/dev/null)"
    echo "  频道: $(python3 -c "
import json
c=json.load(open('/home/kele/.openclaw/openclaw.json'))
ch = c.get('channels',{})
active = [n for n,v in ch.items() if v.get('enabled')]
print(', '.join(active) if active else '无')
" 2>/dev/null)"
    echo "  Gateway: $(systemctl --user is-active openclaw-gateway 2>/dev/null) | $(ss -tlnp | grep 18789 | awk '{print $4}' || echo '未监听')"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ;;
esac
