#!/usr/bin/env python3
"""
简单的 Web 服务器，用于分享 pre-commit 看板。
用法: python scripts/web_server.py [端口]
"""
import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
from datetime import datetime

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


class DashboardHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)

    def do_GET(self):
        """处理 GET 请求"""
        # 根路径重定向到历史看板
        if self.path == '/' or self.path == '':
            self.path = '/history_dashboard.html'

        # 处理 API 请求
        if self.path == '/api/status':
            self.send_json_response(self.get_status())
            return

        if self.path == '/api/update':
            # 触发更新（简单实现，实际使用建议加认证）
            self.run_update()
            return

        return super().do_GET()

    def get_status(self):
        """获取当前状态"""
        info_file = os.path.join(OUTPUT_DIR, 'update_info.json')
        if os.path.exists(info_file):
            with open(info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'last_update': '未知', 'status': '未初始化'}

    def run_update(self):
        """手动触发更新"""
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, os.path.join(PROJECT_DIR, 'scripts', 'daily_update.py')],
                capture_output=True,
                text=True,
                timeout=300
            )
            self.send_json_response({
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def send_json_response(self, data):
        """发送 JSON 响应"""
        response = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f'[{timestamp}] {self.address_string()} - {format % args}')

    def end_headers(self):
        """添加 CORS 头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()


def get_local_ip():
    """获取本机 IP 地址"""
    try:
        # 连接到外部服务器来获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 创建主页索引
    index_path = os.path.join(OUTPUT_DIR, 'index.html')
    if not os.path.exists(index_path):
        create_index_html(index_path, port)

    local_ip = get_local_ip()

    print('=' * 70)
    print('[OK] Pre-Commit 看板 Web 服务器已启动')
    print('=' * 70)
    print(f'[路径] 看板目录: {OUTPUT_DIR}')
    print(f'[本地] 本地访问: http://localhost:{port}')
    print(f'[网络] 局域网访问: http://{local_ip}:{port}')
    print(f'[看板] 历史看板: http://{local_ip}:{port}/history_dashboard.html')
    print('=' * 70)
    print('[提示]')
    print('   - 分享上面的 局域网链接 给团队其他成员')
    print('   - 按 Ctrl+C 停止服务器')
    print('=' * 70)

    try:
        server = HTTPServer(('0.0.0.0', port), DashboardHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n\n👋 服务器已停止')
        server.server_close()


def create_index_html(path, port):
    """创建主页索引"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pre-Commit 静态检查看板</title>
<style>
  :root {{
    --bg: #f5f7fa;
    --card-bg: #ffffff;
    --text: #1a2332;
    --text-dim: #6b7a8f;
    --border: #dce2eb;
    --accent: #3182ce;
    --accent-dim: #ebf4ff;
    --green: #38a169;
    --red: #e53e3e;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
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
    <h2>📊 当前状态</h2>
    <div id="statusContent">
      <div class="status-row"><span class="status-label">最后更新</span><span class="status-value">加载中...</span></div>
    </div>
  </div>

  <div class="links">
    <a href="history_dashboard.html" class="link-card">
      <h3>📋 历史数据看板</h3>
      <p>查看所有代码仓的 pre-commit 检查结果、问题模块统计和修复建议</p>
    </a>
  </div>

  <div class="info">
    <strong>💡 使用说明</strong><br>
    • 看板数据每日 9:00 自动刷新<br>
    • 点击上面的卡片查看详细检查结果<br>
    • 如需手动刷新，执行: <code>python scripts/daily_update.py</code>
  </div>
</div>

<script>
fetch('/api/status')
  .then(r => r.json())
  .then(data => {{
    document.getElementById('statusContent').innerHTML = `
      <div class="status-row"><span class="status-label">最后更新</span><span class="status-value">${{data.last_update || '未知'}}</span></div>
      <div class="status-row"><span class="status-label">监控仓库</span><span class="status-value">${{data.total_repos || 0}} 个</span></div>
      <div class="status-row"><span class="status-label">总 PR 数</span><span class="status-value">${{data.total_prs || 0}} 条</span></div>
      <div class="status-row"><span class="status-label">待修复 PR</span><span class="status-value" style="${{data.failed_prs > 0 ? 'color:var(--red)' : 'color:var(--green)'}}">${{data.failed_prs || 0}} 条</span></div>
      <div class="status-row"><span class="status-label">总违规数</span><span class="status-value" style="${{data.total_violations > 0 ? 'color:var(--red)' : 'color:var(--green)'}}">${{(data.total_violations || 0).toLocaleString()}} 处</span></div>
    `;
  }})
  .catch(e => {{
    console.error(e);
  }});
</script>
</body>
</html>"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    main()
