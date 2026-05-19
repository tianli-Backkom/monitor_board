#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 GitHub Pages 首页 index.md"""
import json
import sys
from datetime import datetime

index_md_path = sys.argv[1] if len(sys.argv) > 1 else 'docs/index.md'
update_info_path = sys.argv[2] if len(sys.argv) > 2 else 'docs/update_info.json'

# 基础内容
content = '''---
title: Pre-Commit 静态检查看板
---

# 📊 Pre-Commit 静态检查看板

## 快速访问

- [📋 历史数据看板](history_dashboard.html)

## 最近更新

'''

# 添加更新信息
try:
    with open(update_info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)
    content += f'**最后更新**: {info["last_update"]}\n\n'
    content += f'- **监控仓库**: {info["total_repos"]} 个\n'
    content += f'- **总 PR 数**: {info["total_prs"]} 条\n'
    content += f'- **待修复 PR**: {info["failed_prs"]} 条\n'
    content += f'- **总违规数**: {info["total_violations"]:,} 处\n'
except Exception as e:
    content += '*暂无更新数据*\n'
    print(f'Warning: {e}')

# 添加关于部分
content += '''
## 关于

本看板由 GitHub Actions 每3小时自动更新，监控 openEuler UBSCore 各代码仓的 pre-commit 检查结果。

### 仓库列表

- ubs-engine
- ubs-comm
- ubs-io
- ubs-mem
- ubs-virt
- ubturbo
- ham
- OmniStateStore

---

*自动生成时间: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''*
'''

with open(index_md_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Generated: {index_md_path}')
