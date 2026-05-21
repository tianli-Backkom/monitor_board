#!/usr/bin/env python3
"""Fetch pre-commit check history for latest N open PRs."""
import os
import sys
import re
import json
import requests
from collections import defaultdict

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
LOGS_DIR = os.path.join(PROJECT_DIR, 'logs')

# Jenkins config for each repo
REPO_CONFIG = {
    'ubs-engine': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-engine',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-engine',
    },
    'ubs-comm': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-comm',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-comm',
    },
    'ubs-io': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-io',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-io',
    },
    'ubs-mem': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-mem',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-mem',
    },
    'ubs-virt': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-virt',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-virt',
    },
    'ubturbo': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubturbo',
        'gitcode_url': 'https://gitcode.com/openeuler/ubturbo',
    },
    'ham': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ham',
        'gitcode_url': 'https://gitcode.com/openeuler/ham',
    },
    'OmniStateStore': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/OmniStateStore',
        'gitcode_url': 'https://gitcode.com/openeuler/OmniStateStore',
    },
    'ubs-atomic': {
        'jenkins_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/pre-commit/job/ubs-atomic',
        'gitcode_url': 'https://gitcode.com/openeuler/ubs-atomic',
    },
}

# Session for requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})


def get_jenkins_builds(repo_name, count=20):
    """Get recent Jenkins builds via API or scraping."""
    config = REPO_CONFIG[repo_name]
    url = f"{config['jenkins_url']}/api/json"

    try:
        print(f"  Fetching builds from Jenkins...")
        r = session.get(url, params={
            'tree': 'builds[number,id,result,timestamp,actions[parameters[name,value]]]',
            'per_page': count
        }, timeout=30)
        r.raise_for_status()
        data = r.json()

        builds = data.get('builds', [])
        print(f"    Got {len(builds)} builds")

        # Extract PR numbers from build
        result = []
        for b in builds[:count]:
            build_num = b.get('number')
            result.append(build_num)

        return sorted(result, reverse=True)[:count]

    except Exception as e:
        print(f"    Error: {e}")
        # Fallback: try to get from console page scraping
        return scrape_jenkins_builds(config['jenkins_url'], count)


def scrape_jenkins_builds(base_url, count=20):
    """Scrape build numbers from Jenkins page."""
    try:
        r = session.get(base_url, timeout=30)
        # Find build numbers from page
        pattern = r'job/[^/]+/(\d+)/'
        matches = re.findall(pattern, r.text)
        builds = sorted(set([int(m) for m in matches]), reverse=True)[:count]
        print(f"    Scraped {len(builds)} build numbers")
        return builds
    except Exception as e:
        print(f"    Scrape error: {e}")
        # Return some recent build numbers as fallback
        return list(range(1760, 1770))


def fetch_build_log(repo_name, build_number):
    """Fetch and parse a single build log."""
    config = REPO_CONFIG[repo_name]
    url = f"{config['jenkins_url']}/{build_number}/consoleText"

    output_dir = os.path.join(LOGS_DIR, repo_name)
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f'{repo_name}-{build_number}.txt')

    # Skip if already exists
    if os.path.exists(output_file):
        print(f"    Already cached: {build_number}")
        return output_file

    try:
        print(f"    Downloading build #{build_number}...", end=' ', flush=True)
        r = session.get(url, timeout=60)
        if r.status_code != 200:
            print(f"HTTP {r.status_code}")
            return None

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(r.text)

        size_kb = len(r.text) / 1024
        print(f"{size_kb:.1f} KB")
        return output_file

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_open_pr_numbers(repo_name, count=10):
    """Get PR numbers and info of the latest open PRs from GitCode API."""
    token = os.environ.get('GITCODE_TOKEN', '')
    if not token:
        print(f"  GITCODE_TOKEN not set, skipping open PR filter")
        return []

    owner = 'openeuler'
    repo = repo_name
    url = f"https://gitcode.com/api/v5/repos/{owner}/{repo}/pulls"
    try:
        print(f"  Fetching open PRs from GitCode...")
        headers = {'private-token': token}
        r = session.get(url, params={
            'state': 'open',
            'sort': 'updated',
            'direction': 'desc',
            'page': 1,
            'per_page': count,
        }, headers=headers, timeout=30)
        r.raise_for_status()
        prs = r.json()
        pr_info = []
        for pr in prs:
            if 'number' in pr:
                pr_info.append({
                    'number': int(pr['number']),
                    'author': pr.get('author', {}).get('username', pr.get('user', {}).get('login', '-')),
                    'title': pr.get('title', ''),
                    'updated_at': pr.get('updated_at', ''),
                })
        print(f"    Got {len(pr_info)} open PRs")
        return pr_info[:count]
    except Exception as e:
        print(f"    GitCode API error: {e}")
        return []


def parse_pr_number_from_log(filepath):
    """Extract PR number from log content."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Pattern: PR #XXX [... trigger by
        m = re.search(r'PR\s+#?(\d+)\s+\[', content)
        if m:
            return int(m.group(1))
        return None
    except:
        return None


def has_precommit_check(filepath):
    """Check if a log file contains pre-commit check execution."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return bool(re.search(r'pre-commit run', content))
    except:
        return False


def fetch_repo_history(repo_name, count=10):
    """Fetch and parse history for a repo, filtered by open PRs.

    Returns a list of (log_file_or_None, pr_info) tuples in GitCode open PR order.
    If a PR has no Jenkins check data, log_file is None.
    """
    print(f"\n=== Fetching history for {repo_name} ===")

    # Get open PR info from GitCode
    open_pr_info = get_open_pr_numbers(repo_name, count)
    open_pr_numbers = [p['number'] for p in open_pr_info]
    open_pr_set = set(open_pr_numbers)

    if not open_pr_set:
        print(f"  No open PRs found, falling back to recent builds")
        build_numbers = get_jenkins_builds(repo_name, count + 5)
        log_files = []
        for build_num in build_numbers[:count + 5]:
            log_file = fetch_build_log(repo_name, build_num)
            if log_file:
                log_files.append(log_file)
        pr_to_build = {}
        for log_file in log_files:
            pr_num = parse_pr_number_from_log(log_file)
            if pr_num and pr_num not in pr_to_build:
                pr_to_build[pr_num] = log_file
                if len(pr_to_build) >= count:
                    break
        print(f"  Found {len(pr_to_build)} unique PRs (fallback)")
        return [(lf, None) for lf in list(pr_to_build.values())[:count]]

    # Get recent build numbers - scan enough builds to find all open PRs
    # Use a larger range: scan up to 100 recent builds
    build_numbers = get_jenkins_builds(repo_name, 100)

    # Fetch logs
    log_files = []
    for build_num in build_numbers:
        log_file = fetch_build_log(repo_name, build_num)
        if log_file:
            log_files.append(log_file)

    # Map open PR number -> best log file (prefer builds with pre-commit check results)
    pr_to_build = {}
    for log_file in log_files:
        pr_num = parse_pr_number_from_log(log_file)
        if pr_num and pr_num in open_pr_set:
            existing = pr_to_build.get(pr_num)
            if existing is None:
                pr_to_build[pr_num] = log_file
            else:
                # Prefer log with pre-commit check results over one without
                if has_precommit_check(log_file) and not has_precommit_check(existing):
                    pr_to_build[pr_num] = log_file

    # Build result in GitCode's open PR order
    result = []
    pr_info_map = {p['number']: p for p in open_pr_info}
    for pr_num in open_pr_numbers:
        log_file = pr_to_build.get(pr_num)
        result.append((log_file, pr_info_map[pr_num]))
        if len(result) >= count:
            break

    matched = sum(1 for lf, _ in result if lf is not None)
    print(f"  Found {matched}/{len(result)} open PRs with check data")
    return result


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

    comp = {
        'id': basename, 'name': basename, 'repo': repo_name,
        'branch': '', 'pr': '#-', 'prAuthor': '-', 'prSource': '-',
        'trigger': '-', 'buildNumber': 0,
        'status': 'skip', 'checkType': '未配置 pre-commit',
        'violations': 0, 'affectedFiles': 0,
        'srcViolations': 0, 'testViolations': 0,
        'conclusion': '', 'recommendation': '',
        'topDirs': [], 'topFiles': [], 'samples': [],
        'merged_at': '',
    }

    # Parse header metadata
    for line in lines[:30]:
        m = re.search(r'build number (\d+)', line)
        if m:
            comp['buildNumber'] = int(m.group(1))

        # PR info: PR 551 [wangxh-07:master_ut -&gt; master] trigger by merge_request
        m = re.search(r'PR\s+#?(\d+)\s+\[([^:]+):([^\]]+?)\s*(-&gt;|->)\s*([^\]]+)\]\s+trigger\s+by\s+(\S+)', line)
        if m:
            comp['pr'] = '#' + m.group(1)
            comp['prAuthor'] = m.group(2).strip()
            comp['prSource'] = m.group(3).strip()
            comp['trigger'] = m.group(6).strip()

        m = re.search(r'git clone\s+-b\s+(\S+)', line)
        if m:
            comp['branch'] = m.group(1)

    # Check if pre-commit ran
    has_precommit_run = re.search(r'pre-commit run', content)
    has_clang_format = re.search(r'clang-format', content)

    if has_precommit_run and has_clang_format:
        comp['checkType'] = 'clang-format'
        comp['status'] = 'pass'

        failed = re.search(r'Run clang-format check[\s\S]{0,200}?Failed', content, re.DOTALL)

        if failed:
            comp['status'] = 'fail'

            vpat = re.compile(r'^(\S+?\.\w+):(\d+):(\d+):\s*error:\s*code should be clang-formatted', re.MULTILINE)
            file_counts = defaultdict(int)
            samples_seen = set()
            samples = []

            for m in vpat.finditer(content):
                fpath = m.group(1)
                file_counts[fpath] += 1

                if len(samples) < 5:
                    sl = '{}:{}:{}: code should be clang-formatted'.format(fpath, m.group(2), m.group(3))
                    if sl not in samples_seen:
                        samples_seen.add(sl)
                        samples.append(sl)

            if file_counts:
                total = sum(file_counts.values())
                comp['violations'] = total
                comp['affectedFiles'] = len(file_counts)

                src_v = sum(v for f, v in file_counts.items() if not f.startswith('test/'))
                test_v = sum(v for f, v in file_counts.items() if f.startswith('test/'))
                comp['srcViolations'] = src_v
                comp['testViolations'] = test_v
                comp['samples'] = samples

                # Directory aggregation - only first-level directories (root modules)
                dir_counts = defaultdict(int)
                for fpath, count in file_counts.items():
                    parts = fpath.split('/')
                    # Only count the first level (root module directory)
                    if len(parts) > 1:
                        d = parts[0]
                        dir_counts[d] += count

                dirs_sorted = sorted([(d, c) for d, c in dir_counts.items()], key=lambda x: -x[1])
                comp['topDirs'] = [[d, c, dir_desc(d)] for d, c in dirs_sorted]

                files_sorted = sorted(file_counts.items(), key=lambda x: -x[1])
                comp['topFiles'] = [[f, c] for f, c in files_sorted]

                if dirs_sorted:
                    wd = dirs_sorted[0]
                    concl = 'clang-format 检查失败，'
                    if test_v > src_v:
                        pct = round(test_v / total * 100)
                        concl += '测试目录占 {}% 违规'.format(pct)
                    else:
                        concl += '{} 模块违规较多'.format(wd[0])
                    comp['conclusion'] = concl

                    top3 = dirs_sorted[:3]
                    rec_parts = ['{} ({}处)'.format(d, c) for d, c in top3]
                    comp['recommendation'] = '重点关注 ' + '、'.join(rec_parts) + '，建议统一运行 clang-format -i 批量修复'
            else:
                comp['conclusion'] = 'clang-format 检查通过'
                comp['recommendation'] = '代码格式符合规范'

    if comp['status'] == 'skip':
        has_config = re.search(r'\.pre-commit-config\.yaml', content)
        if has_config:
            comp['checkType'] = '已配置pre-commit但未运行'
            comp['conclusion'] = '已配置pre-commit但日志中未执行检查'
        else:
            comp['checkType'] = '未配置 pre-commit'
            comp['conclusion'] = '仓库未配置 pre-commit 检查'

    return comp


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fetch pre-commit history for latest N open PRs')
    parser.add_argument('--count', '-n', type=int, default=10, help='Number of open PRs to fetch')
    parser.add_argument('--repo', '-r', help='Specific repo (ubs-engine/ubs-comm)')

    args = parser.parse_args()

    repos = [args.repo] if args.repo else list(REPO_CONFIG.keys())

    all_data = {}
    for repo in repos:
        results = fetch_repo_history(repo, args.count)
        components = []
        for log_file, pr_info in results:
            if log_file:
                print(f"  Parsing {os.path.basename(log_file)}...")
                comp = parse_log(log_file, repo)
            else:
                # No Jenkins check data for this open PR
                pr_num = pr_info['number'] if pr_info else 0
                comp = {
                    'id': f'{repo}-no-build-{pr_num}',
                    'name': f'{repo}-no-build-{pr_num}',
                    'repo': repo,
                    'branch': '',
                    'pr': f'#{pr_num}',
                    'prAuthor': pr_info.get('author', '-') if pr_info else '-',
                    'prSource': '-',
                    'trigger': '-',
                    'buildNumber': 0,
                    'status': 'skip',
                    'checkType': '无检查记录',
                    'violations': 0,
                    'affectedFiles': 0,
                    'srcViolations': 0,
                    'testViolations': 0,
                    'conclusion': '该 PR 尚无 Jenkins pre-commit 检查记录',
                    'recommendation': '等待 Jenkins pre-commit 任务执行检查',
                    'topDirs': [],
                    'topFiles': [],
                    'samples': [],
                    'merged_at': '',
                }
            components.append(comp)
        all_data[repo] = components

    # Save summary data
    summary_file = os.path.join(PROJECT_DIR, 'output', 'history_data.json')
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== Summary ===")
    for repo, comps in all_data.items():
        fail = len([c for c in comps if c['status'] == 'fail'])
        skip = len([c for c in comps if c['status'] == 'skip'])
        total_v = sum(c['violations'] for c in comps)
        print(f"  {repo}: {len(comps)} PRs, {fail} failed, {skip} skipped, {total_v:,} total violations")

    return all_data


if __name__ == '__main__':
    main()
