#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GitHub Pages 首页 index.html"""
import json
import sys
from datetime import datetime

html_path = sys.argv[1] if len(sys.argv) > 1 else 'docs/index.html'
update_info_path = sys.argv[2] if len(sys.argv) > 2 else 'docs/update_info.json'

# 读取更新信息
info = {}
try:
    with open(update_info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
except Exception as e:
    print(f'Warning: {e}')

last_update = info.get('last_update', '暂无')
total_repos = info.get('total_repos', 0)
total_prs = info.get('total_prs', 0)
failed_prs = info.get('failed_prs', 0)
total_violations = info.get('total_violations', 0)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pre-Commit 静态检查看板</title>
<style>
  :root {{
    --bg: #f5f7fa; --card-bg: #ffffff; --text: #1a2332; --text-dim: #6b7a8f;
    --border: #dce2eb; --accent: #3182ce; --accent-dim: #ebf4ff;
    --green: #38a169; --red: #e53e3e;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg); color: var(--text); min-height: 100vh;
  }}
  .container {{ max-width: 800px; margin: 0 auto; padding: 60px 24px; }}
  .header {{ text-align: center; margin-bottom: 48px; }}
  .header h1 {{ font-size: 36px; font-weight: 800; margin-bottom: 8px; }}
  .header h1 span {{ color: var(--accent); }}
  .header .sub {{ color: var(--text-dim); font-size: 16px; }}
  .status-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px;
    padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }}
  .status-card h2 {{ font-size: 20px; margin-bottom: 16px; }}
  .status-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--border); }}
  .status-row:last-child {{ border-bottom: none; }}
  .status-label {{ color: var(--text-dim); }}
  .status-value {{ font-weight: 600; }}
  .status-value.ok {{ color: var(--green); }}
  .links {{ display: grid; gap: 16px; }}
  .link-card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 20px; text-decoration: none; color: var(--text);
    transition: all .2s; display: block;
  }}
  .link-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: var(--accent); }}
  .link-card h3 {{ font-size: 18px; margin-bottom: 8px; color: var(--accent); }}
  .link-card p {{ color: var(--text-dim); font-size: 14px; }}
  .info {{
    background: var(--accent-dim); border-radius: 12px; padding: 20px;
    margin-top: 32px; font-size: 14px; line-height: 1.8; color: #2b6cb0;
  }}
  .info code {{ background: white; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Pre-Commit <span>静态检查看板</span></h1>
    <div class="sub">openEuler UBSCore 代码格式检查监控平台</div>
  </div>

  <div class="status-card">
    <h2>当前状态</h2>
    <div class="status-row"><span class="status-label">最后更新</span><span class="status-value">{last_update}</span></div>
    <div class="status-row"><span class="status-label">监控仓库</span><span class="status-value">{total_repos} 个</span></div>
    <div class="status-row"><span class="status-label">开启中 PR</span><span class="status-value">{total_prs} 条</span></div>
    <div class="status-row"><span class="status-label">待修复 PR</span><span class="status-value" style="color: {'var(--red)' if failed_prs > 0 else 'var(--green)'}">{failed_prs} 条</span></div>
    <div class="status-row"><span class="status-label">总违规数</span><span class="status-value" style="color: {'var(--red)' if total_violations > 0 else 'var(--green)'}">{total_violations:,} 处</span></div>
  </div>

  <div class="links">
    <a href="history_dashboard.html" class="link-card">
      <h3>历史数据看板</h3>
      <p>查看所有代码仓的 pre-commit 检查结果、问题统计和修复建议</p>
    </a>
  </div>

  <div class="info">
    <strong>使用说明</strong><br>
    &bull; 看板数据每3小时自动刷新<br>
    &bull; 点击上面的卡片查看详细检查结果<br>
    &bull; 监控仓库: ubs-engine, ubs-comm, ubs-io, ubs-mem, ubs-virt, ubturbo, ham, OmniStateStore
  </div>
</div>
</body>
</html>"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated: {html_path}')
