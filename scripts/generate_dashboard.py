#!/usr/bin/env python3
"""Parse UBSCore pre-commit check logs and generate multi-repo kanban dashboard HTML."""
import json
import os
import re
import sys
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def dir_desc(d):
    """Generate short descriptions for directory names."""
    last = d.split('/')[-1]
    m = {
        'brpc': 'RPC', 'ubsocket': '核心', 'transport': '传输',
        'common': '公共库', 'cli': 'CLI', 'node': '节点',
        'mem': '内存', 'controller': '控制器',
        'include': '头文件', 'config': '配置',
        'adapter': '适配', 'sdk': 'SDK', 'server': '服务端',
        'cache': '缓存', 'net': '网络', 'security': '安全',
        'util': '工具', 'test': '测试',
        'daemon': '守护进程', 'engine': '引擎',
        'sched': '调度', 'cluster': '集群', 'api': 'API',
        'parser': '解析', 'log': '日志',
        'core': '核心', 'shm': '共享内存',
        'umq': 'UMQ', 'zookeeper': 'ZK第三方',
        'hadoop': 'Hadoop第三方', 'agent': '代理',
        'virt': '虚拟化', 'stub': '桩', 'runtime': '运行时',
        'tuner': '调优', 'optimizer': '优化器',
        'lease': '租约', 'discovery': '服务发现',
    }
    return m.get(last, last)


def parse_log(filepath, repo_name):
    """Parse a single Jenkins CI pre-commit check log file."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    lines = content.split('\n')
    basename = os.path.splitext(os.path.basename(filepath))[0]

    EM = '-'

    comp = {
        'id': basename, 'name': basename, 'repo': repo_name,
        'branch': '', 'pr': '#' + EM, 'prAuthor': EM, 'prSource': EM,
        'trigger': EM, 'buildNumber': 0, 'jobTime': '',
        'status': 'skip', 'checkType': '未配置 pre-commit',
        'violations': 0, 'affectedFiles': 0,
        'srcViolations': 0, 'testViolations': 0,
        'conclusion': '', 'recommendation': '',
        'topDirs': [], 'topFiles': [], 'samples': [],
    }

    # Parse header metadata (first ~20 lines)
    for line in lines[:20]:
        # Build number
        m = re.search(r'build number (\d+)', line)
        if m:
            comp['buildNumber'] = int(m.group(1))

        # PR info (handle HTML escaped chars like -&gt; for ->)
        m = re.search(
            r'PR\s+#?(\d+)\s+\[([^:]+):([^\]]+?)\s*(-&gt;|->)\s*([^\]]+)\]'
            r'\s+trigger\s+by\s+(\S+)',
            line,
        )
        if m:
            comp['pr'] = '#' + m.group(1)
            comp['prAuthor'] = m.group(2).strip()
            comp['prSource'] = m.group(3).strip()
            comp['trigger'] = m.group(6).strip()

        # Branch
        m = re.search(r'git clone\s+-b\s+(\S+)', line)
        if m:
            comp['branch'] = m.group(1)

    # Check if pre-commit / clang-format ran
    has_precommit_run = re.search(r'pre-commit run', content)
    has_clang_format = re.search(r'clang-format', content)

    if has_precommit_run and has_clang_format:
        comp['checkType'] = 'clang-format'
        comp['status'] = 'pass'  # Default to pass if ran without violation

        # Check for failure
        failed = re.search(
            r'Run clang-format check[\s\S]{0,200}?Failed',
            content, re.DOTALL,
        )

        if failed:
            comp['status'] = 'fail'

            # Count violations per file (different format in actual log)
            vpat = re.compile(
                r'^(\S+?\.\w+):(\d+):(\d+):\s*error:\s*'
                r'code should be clang-formatted',
                re.MULTILINE,
            )

            file_counts = defaultdict(int)
            samples_seen = set()
            samples = []

            for m in vpat.finditer(content):
                fpath = m.group(1)
                file_counts[fpath] += 1

                if len(samples) < 5:
                    sl = '{}:{}:{}: code should be clang-formatted'.format(
                        fpath, m.group(2), m.group(3),
                    )
                    if sl not in samples_seen:
                        samples_seen.add(sl)
                        samples.append(sl)

            if file_counts:
                total = sum(file_counts.values())
                comp['violations'] = total
                comp['affectedFiles'] = len(file_counts)

                # src vs test breakdown
                src_v = sum(v for f, v in file_counts.items()
                            if not f.startswith('test/'))
                test_v = sum(v for f, v in file_counts.items()
                             if f.startswith('test/'))
                comp['srcViolations'] = src_v
                comp['testViolations'] = test_v
                comp['samples'] = samples

                # Directory-level aggregation
                dir_counts = defaultdict(int)
                for fpath, count in file_counts.items():
                    parts = fpath.split('/')
                    for i in range(1, len(parts)):
                        d = '/'.join(parts[:i])
                        dir_counts[d] += count

                dirs_sorted = sorted(
                    [(d, c) for d, c in dir_counts.items() if len(d) > 2],
                    key=lambda x: -x[1],
                )[:10]
                comp['topDirs'] = [[d, c, dir_desc(d)]
                                   for d, c in dirs_sorted]

                # Top files
                files_sorted = sorted(
                    file_counts.items(), key=lambda x: -x[1],
                )[:10]
                comp['topFiles'] = [[f, c] for f, c in files_sorted]

                # Auto-generate conclusion
                if dirs_sorted:
                    wd = dirs_sorted[0]
                    concl = 'clang-format 检查失败，'
                    if test_v > src_v:
                        pct = round(test_v / total * 100)
                        concl += '测试目录占 {}% 违规'.format(pct)
                    else:
                        concl += '{} 模块违规较多'.format(wd[0])
                    comp['conclusion'] = concl

                    # Recommendation
                    top3 = dirs_sorted[:3]
                    rec_parts = ['{} ({}处)'.format(d, c) for d, c in top3]
                    comp['recommendation'] = (
                        '重点关注 '
                        + '、'.join(rec_parts)
                        + '，建议统一运行 '
                        'clang-format -i 批量修复'
                    )
            else:
                comp['conclusion'] = 'clang-format 检查通过'
                comp['recommendation'] = '代码格式符合规范'

    # Skip status reasons
    if comp['status'] == 'skip':
        has_config = re.search(r'\.pre-commit-config\.yaml', content)
        has_clang_tools = re.search(r'clang-tools-extra|clang-format', content)
        branch = comp.get('branch', '')

        if has_config and has_clang_tools and not has_precommit_run:
            comp['checkType'] = 'pre-commit 已安装未运行'
            comp['conclusion'] = (
                '已安装 clang-tools 和 pre-commit '
                '但日志中未执行 pre-commit run'
            )
            comp['recommendation'] = (
                '仓库已有 .pre-commit-config.yaml'
                '（clang-format + clang-tidy），'
                '修复 Jenkinsfile 即可启用'
            )
        elif has_config:
            comp['checkType'] = '未配置 pre-commit'
            comp['conclusion'] = (
                '仓库未配置 pre-commit '
                '检查，仅执行了 Git '
                '合并操作'
            )
            comp['recommendation'] = (
                '建议在仓库根目录添加 '
                '.pre-commit-config.yaml，启用 clang-format '
                '和 clang-tidy'
            )
        else:
            comp['checkType'] = '未配置 pre-commit'
            comp['conclusion'] = (
                '仓库未配置 pre-commit 检查'
            )
            if branch and branch != 'master':
                comp['recommendation'] = (
                    '该 PR 目标分支为 {}'
                    '，建议在 master 配置 '
                    'pre-commit 并在 CI 支持多分支'
                ).format(branch)
            else:
                comp['recommendation'] = (
                    '建议在仓库根目录添加 '
                    '.pre-commit-config.yaml，启用 clang-format '
                    '和 clang-tidy'
                )

    return comp


def parse_all_logs(logs_dir):
    """Parse all logs from subdirectories (each subdir is a repo)."""
    repos = {}

    for repo_name in os.listdir(logs_dir):
        repo_dir = os.path.join(logs_dir, repo_name)
        if not os.path.isdir(repo_dir):
            continue

        txt_files = sorted([
            f for f in os.listdir(repo_dir) if f.endswith('.txt')
        ])

        if not txt_files:
            continue

        components = []
        for fname in txt_files:
            fpath = os.path.join(repo_dir, fname)
            print(f'  Parsing {repo_name}/{fname}...', end=' ', flush=True)
            try:
                comp = parse_log(fpath, repo_name)
                components.append(comp)
                print(f'[{comp["status"]}] {comp["violations"]} violations')
            except Exception as e:
                print(f'ERROR: {e}')

        if components:
            repos[repo_name] = components

    return repos


def generate_html(repos_data, template_path, output_path):
    """Inject parsed data into the HTML template."""
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    data_json = json.dumps(repos_data, ensure_ascii=False, indent=2)
    html = template.replace('__REPOS_DATA__', data_json)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Dashboard generated: {output_path}')
    total_components = sum(len(comps) for comps in repos_data.values())
    print(f'  Total repos: {len(repos_data)}')
    print(f'  Total components: {total_components}')

    # Aggregate stats
    all_comps = []
    for comps in repos_data.values():
        all_comps.extend(comps)
    statuses = [c['status'] for c in all_comps]
    print(f'  Failed: {statuses.count("fail")}, '
          f'Passed: {statuses.count("pass")}, '
          f'Skipped: {statuses.count("skip")}')

    total_v = sum(c['violations'] for c in all_comps)
    print(f'  Total violations: {total_v:,}')


def main():
    logs_dir = os.path.join(PROJECT_DIR, 'logs')
    template_path = os.path.join(PROJECT_DIR, 'templates', 'dashboard.html')
    output_path = os.path.join(PROJECT_DIR, 'output', 'dashboard.html')

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print('Parsing logs from:', logs_dir)
    repos_data = parse_all_logs(logs_dir)

    if not repos_data:
        print('ERROR: No log files found')
        sys.exit(1)

    # Locate template
    if not os.path.exists(template_path):
        template_path = os.path.join(PROJECT_DIR, 'templates', 'template.html')
    if not os.path.exists(template_path):
        print(f'ERROR: Template file not found at {template_path}')
        sys.exit(1)

    generate_html(repos_data, template_path, output_path)


if __name__ == '__main__':
    main()
