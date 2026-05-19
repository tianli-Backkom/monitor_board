#!/usr/bin/env python3
"""Generate history dashboard HTML from fetched data."""
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)


def generate_history_dashboard():
    """Generate history dashboard HTML."""
    # Load history data
    data_file = os.path.join(PROJECT_DIR, 'output', 'history_data.json')
    if not os.path.exists(data_file):
        print(f"Error: {data_file} not found. Run fetch_history.py first.")
        return None

    with open(data_file, 'r', encoding='utf-8') as f:
        repos_data = json.load(f)

    # Load template
    template_file = os.path.join(PROJECT_DIR, 'templates', 'history_dashboard.html')
    with open(template_file, 'r', encoding='utf-8') as f:
        template = f.read()

    # Inject data
    data_json = json.dumps(repos_data, ensure_ascii=False, indent=2)
    html = template.replace('__HISTORY_DATA__', data_json)

    # Write output
    output_file = os.path.join(PROJECT_DIR, 'output', 'history_dashboard.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"History dashboard generated: {output_file}")
    print(f"  Repos: {len(repos_data)}")
    total_prs = sum(len(comps) for comps in repos_data.values())
    print(f"  Total PRs: {total_prs}")

    # Summary per repo
    for repo, comps in repos_data.items():
        failed = len([c for c in comps if c['status'] == 'fail'])
        total_v = sum(c['violations'] for c in comps)
        print(f"  {repo}: {len(comps)} PRs, {failed} failed, {total_v:,} violations")

    return output_file


def main():
    generate_history_dashboard()


if __name__ == '__main__':
    main()
