# GitHub Actions 自动化部署说明

## 📋 方案概述

使用 GitHub Actions + GitHub Pages 实现：
1. ✅ 每日 9:00 自动获取最新 pre-commit 数据
2. ✅ 自动生成看板 HTML
3. ✅ 自动部署到 GitHub Pages
4. ✅ 公开链接可分享给任何人

---

## 🚀 部署步骤

### 第一步：准备仓库

1. 在 GitHub 创建一个新仓库（或使用现有仓库）
2. 将本项目的代码推送到 GitHub

```bash
cd pre-commit-v2
git init
git add .
git commit -m "Initial commit: Pre-commit dashboard system"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

### 第二步：启用 GitHub Pages

1. 进入仓库的 **Settings** → **Pages**
2. 在 **Source** 中选择：
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. 点击 **Save**

> 💡 首次运行 Actions 后才会有 `gh-pages` 分支

### 第三步：首次手动触发（可选）

1. 进入仓库的 **Actions** 标签
2. 在左侧选择 "Daily Pre-Commit Dashboard Update"
3. 点击 **Run workflow** → 选择 main 分支 → 点击 **Run workflow**

---

## ⚙️ 工作流说明

### 定时触发

```yaml
cron: '0 1 * * *'  # UTC 1:00 = 北京时间 9:00
```

### 工作流步骤

| 步骤 | 说明 |
|------|------|
| Checkout code | 检出代码 |
| Set up Python | 配置 Python 环境 |
| Install dependencies | 安装依赖（requests） |
| Fetch pre-commit data | 从 Jenkins 获取最近 20 条 PR 数据 |
| Generate dashboard HTML | 生成看板 HTML 文件 |
| Deploy to GitHub Pages | 部署到 gh-pages 分支 |

---

## 🔗 访问地址

部署成功后，访问地址格式：

```
https://你的用户名.github.io/仓库名/
```

例如：
```
https://yourname.github.io/pre-commit-v2/
```

访问时会显示：
- **首页**: 状态汇总和快捷入口
- **历史看板**: 各仓库详细检查结果

---

## 📁 目录结构（gh-pages 分支）

```
/
├── index.md              # GitHub Pages 首页
├── index.html            # Web 服务器首页（可选）
├── history_dashboard.html # 主看板
├── history_data.json     # 原始数据
└── update_info.json      # 更新状态
```

---

## 🔧 自定义配置

### 修改更新时间

编辑 `.github/workflows/daily-update.yml` 中的 cron 表达式：

```yaml
schedule:
  - cron: '0 1 * * *'  # UTC 时间，北京时间 = UTC + 8
```

常用 cron 示例：
```
0 1 * * *    # 每天 9:00
0 2 * * *    # 每天 10:00
0 */6 * * *  # 每 6 小时
```

### 修改获取的 PR 数量

修改 `-n` 参数：

```yaml
python scripts/fetch_history.py -n 30  # 获取最近 30 条
```

### 添加自定义仓库

编辑 `scripts/fetch_history.py` 中的 `REPO_CONFIG`：

```python
REPO_CONFIG = {
    '你的新仓库': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/...',
        'gitcode_url': 'https://gitcode.com/openeuler/你的新仓库',
    },
    # ... 更多仓库
}
```

---

## 🔍 查看运行日志

1. 进入仓库的 **Actions** 标签页
2. 点击最近的工作流运行记录
3. 点击 **update-dashboard** 任务
4. 展开各个步骤查看详细日志

### 常见问题

**问题 1**: 工作流运行失败，提示网络错误

> Jenkins 可能有限制，检查 GitHub Actions 服务器是否能访问 ci.openeuler.openatom.cn

**问题 2**: GitHub Pages 没有更新

> 检查 gh-pages 分支是否有新提交，Pages 部署通常有 1-3 分钟延迟

**问题 3**: 看板页面显示 404

> 确认 gh-pages 分支存在，且 Pages 设置中源分支正确

---

## 📱 分享看板

部署成功后，你可以分享以下链接：

| 页面 | 链接 |
|------|------|
| 首页 | `https://你的用户名.github.io/仓库名/` |
| 历史看板 | `https://你的用户名.github.io/仓库名/history_dashboard.html` |

**分享示例**：
> 📊 Pre-Commit 检查看板已上线！
> 地址：https://yourname.github.io/pre-commit-v2/
> 每天 9:00 自动更新，欢迎订阅关注~

---

## 💡 高级功能

### 1. 添加通知（可选）

在工作流末尾添加通知步骤，如：

```yaml
- name: Send notification
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: Pre-commit 看板已更新！
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

支持 Slack、飞书、企业微信等。

### 2. 生成问题报告（可选）

在生成看板后，可以自动生成 Issue 报告问题：

```yaml
- name: Create issue for critical issues
  if: failure()
  run: |
    # 检查违规数量，创建 Issue
    # ...
```

### 3. 徽章（可选）

在 README 中添加状态徽章：

```markdown
![Daily Update](https://github.com/你的用户名/仓库名/actions/workflows/daily-update.yml/badge.svg)
```

---

## 📊 与本地方案对比

| 特性 | 本地方案 | GitHub Actions 方案 |
|------|---------|-------------------|
| 定时更新 | ✅ 需要电脑一直开机 | ✅ 云端 24/7 运行 |
| 外部访问 | ❌ 需要内网穿透 | ✅ GitHub Pages 公网访问 |
| 运行成本 | ❌ 需要占用本地资源 | ✅ 开源仓库免费 |
| 稳定性 | ⚠️ 依赖网络和电脑状态 | ✅ 高可用 |
| 历史记录 | ⚠️ 本地日志 | ✅ Actions 完整历史记录 |
| 分享便捷 | ❌ 需要配置网络 | ✅ 直接分享链接 |

---

## 📝 注意事项

1. **API 限制**: Jenkins 如有访问频率限制，请注意调整
2. **数据大小**: 日志文件较多时，注意仓库大小
3. **网络连通性**: 确保 GitHub Actions 可以访问 Jenkins 服务器
4. **权限配置**: 确保 Actions 有写入仓库的权限

---

## 🔗 参考文档

- [GitHub Actions 文档](https://docs.github.com/cn/actions)
- [GitHub Pages 文档](https://docs.github.com/cn/pages)
- [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages)
