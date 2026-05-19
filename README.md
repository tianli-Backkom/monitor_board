# Pre-Commit 静态检查看板系统

## 📋 功能概述

一套完整的 pre-commit 检查数据采集、可视化、定时更新和团队分享方案。

## 🚀 快速开始

### 首次部署

1. **右键以管理员身份运行** `scripts\setup_task.bat`
   - 执行首次数据更新
   - 创建 Windows 定时任务（每日 9:00 自动更新）
   - 生成 Web 服务器启动脚本

2. **启动 Web 服务器**
   - 双击运行 `start_server.bat`
   - 浏览器访问 http://localhost:8000

3. **分享给团队**
   - 查看启动时显示的 🌐 局域网访问地址（如 http://192.168.x.x:8000）
   - 将地址分享给团队成员

## 📂 项目结构

```
pre-commit-v2/
├── logs/                      # 日志目录
│   ├── ubs-engine/           # 各仓库 Jenkins 日志
│   ├── ubs-comm/
│   └── system/               # 系统运行日志
├── scripts/
│   ├── fetch_history.py      # 获取历史数据
│   ├── generate_history.py   # 生成看板
│   ├── daily_update.py       # 每日更新脚本
│   ├── web_server.py         # Web 服务器
│   ├── setup_task.bat        # 定时任务安装脚本
│   └── run_update.bat        # 被任务计划调用的脚本
├── templates/
│   └── history_dashboard.html # 看板模板
├── output/
│   ├── index.html            # 主页
│   ├── history_dashboard.html # 历史数据看板
│   ├── history_data.json     # 原始数据
│   └── update_info.json      # 更新状态
└── start_server.bat          # Web 服务器启动脚本（自动生成）
```

## 🔧 手动操作

### 手动更新数据

```bash
python scripts/daily_update.py
```

### 手动启动 Web 服务器

```bash
python scripts/web_server.py 8000
```

### 查看定时任务

- 打开 **控制面板** → **管理工具** → **任务计划程序**
- 在任务计划程序库中找到 `PreCommitDashboardUpdate`

### 删除定时任务

```bash
schtasks /delete /tn "PreCommitDashboardUpdate" /f
```

## 📊 看板功能

### 首页 (`/`)

- 当前更新状态
- 监控仓库数量
- 待修复 PR 数量
- 总违规数统计
- 快捷入口链接

### 历史看板 (`/history_dashboard.html`)

- **仓库切换 Tab**: 快速在 8 个代码仓间切换
- **状态告警**: 红色显示有问题的仓库
- **问题模块统计**: 按 P0/P1/P2 优先级展示
- **清理建议**: 具体的格式化命令和操作步骤
- **待修复 PR 列表**: 按违规数量排序，一键跳转 GitCode

## 🌐 网络分享

### 局域网访问

启动服务器后，分享显示的局域网 IP，如：
```
http://192.168.1.100:8000
```

### 公网访问（可选）

如果需要公网访问，可以：
1. 使用内网穿透工具（如 ngrok、frp）
2. 部署到公司内部服务器
3. 使用反向代理（如 Nginx）

## ⏰ 定时任务说明

- **触发时间**: 每日 9:00
- **执行内容**: 获取最近 20 条 PR 数据 → 生成看板
- **日志位置**: `logs/system/update_YYYYMMDD.log`

## 📝 自定义配置

### 修改定时任务时间

1. 打开 **任务计划程序**
2. 找到 `PreCommitDashboardUpdate` 任务
3. 右键 → 属性 → 触发器 → 编辑

### 添加新的代码仓

编辑 `scripts/fetch_history.py` 中的 `REPO_CONFIG` 配置。

### 修改端口

编辑 `start_server.bat` 中的端口号，或直接运行：
```bash
python scripts/web_server.py 8080
```

## 🔍 故障排查

### 数据更新失败

1. 检查网络连接，能否访问 `ci.openeuler.openatom.cn`
2. 查看 `logs/system/` 下的日志文件
3. 手动运行 `python scripts/daily_update.py` 查看输出

### 无法访问看板

1. 确认 `start_server.bat` 正在运行
2. 检查防火墙是否阻止了端口 8000
3. 尝试访问 http://127.0.0.1:8000 测试本地连通性

### 团队成员无法访问

1. 确认在同一局域网内
2. 检查本机防火墙入站规则
3. 使用正确的 IP 地址（不是 127.0.0.1）

## 📄 监控的代码仓

| 序号 | 仓库 | 检查类型 |
|------|------|---------|
| 1 | ubs-engine | OpenSourceCodeCheck |
| 2 | ubs-comm | OpenSourceCodeCheck |
| 3 | ubs-io | OpenSourceCodeCheck |
| 4 | ubs-mem | OpenSourceCodeCheck |
| 5 | ubs-virt | OpenSourceCodeCheck |
| 6 | ubturbo | OpenSourceCodeCheck |
| 7 | ham | OpenSourceCodeCheck |
| 8 | OmniStateStore | OpenSourceCodeCheck |
