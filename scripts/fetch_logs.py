#!/usr/bin/env python3
"""Fetch Jenkins CI pre-commit check console logs."""
import os
import sys
import requests

# Jenkins base URLs for each repo
REPO_CONFIG = {
    'ubs-engine': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ubs-engine',
        'console_suffix': 'consoleText',
    },
    'ubs-comm': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/DT/job/ubs-comm',
        'console_suffix': 'consoleText',
    },
    'ubs-io': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ubs-io',
        'console_suffix': 'consoleText',
    },
    'ubs-mem': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ubs-mem',
        'console_suffix': 'consoleText',
    },
    'ubs-virt': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ubs-virt',
        'console_suffix': 'consoleText',
    },
    'ubturbo': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ubturbo',
        'console_suffix': 'consoleText',
    },
    'ham': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/ham',
        'console_suffix': 'consoleText',
    },
    'OmniStateStore': {
        'base_url': 'https://ci.openeuler.openatom.cn/job/multiarch/job/manual-jobs/job/openeuler/job/UBSCore/job/OpenSourceCodeCheck/job/OmniStateStore',
        'console_suffix': 'consoleText',
    },
}

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')


def fetch_single_log(repo_name, build_number, output_dir=None):
    """Fetch a single build's console log from Jenkins."""
    if repo_name not in REPO_CONFIG:
        raise ValueError(f'Unknown repo: {repo_name}. Available: {list(REPO_CONFIG.keys())}')

    config = REPO_CONFIG[repo_name]
    url = f"{config['base_url']}/{build_number}/{config['console_suffix']}"

    print(f'Fetching {repo_name} build #{build_number}...')
    print(f'  URL: {url}')

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f'  ERROR: Failed to fetch log: {e}')
        return None

    if output_dir is None:
        output_dir = os.path.join(LOGS_DIR, repo_name)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{repo_name}-{build_number}.txt')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(response.text)

    size_kb = len(response.text) / 1024
    print(f'  Saved: {output_path} ({size_kb:.1f} KB)')
    return output_path


def fetch_latest_build(repo_name, output_dir=None):
    """Fetch the latest build number and its log."""
    config = REPO_CONFIG[repo_name]
    # Get last successful build number via Jenkins API
    api_url = f"{config['base_url']}/lastBuild/api/json"

    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        build_info = response.json()
        build_number = build_info['number']
        print(f'Latest build for {repo_name}: #{build_number}')
        return fetch_single_log(repo_name, build_number, output_dir)
    except requests.RequestException as e:
        print(f'ERROR: Failed to get latest build: {e}')
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fetch Jenkins CI pre-commit logs')
    parser.add_argument('repo', nargs='?', help='Repository name (ubs-engine or ubs-comm)')
    parser.add_argument('--build', type=int, help='Build number to fetch')
    parser.add_argument('--latest', action='store_true', help='Fetch latest build')
    parser.add_argument('--all', action='store_true', help='Fetch latest for all repos')
    parser.add_argument('--output', '-o', help='Output directory')

    args = parser.parse_args()

    if args.all:
        for repo in REPO_CONFIG.keys():
            fetch_latest_build(repo, args.output)
        return

    if not args.repo:
        parser.print_help()
        print('\nExamples:')
        print('  python fetch_logs.py ubs-engine --build 1766')
        print('  python fetch_logs.py ubs-engine --latest')
        print('  python fetch_logs.py --all')
        sys.exit(1)

    if args.build:
        fetch_single_log(args.repo, args.build, args.output)
    elif args.latest:
        fetch_latest_build(args.repo, args.output)
    else:
        print('Please specify --build <number> or --latest')
        sys.exit(1)


if __name__ == '__main__':
    main()
