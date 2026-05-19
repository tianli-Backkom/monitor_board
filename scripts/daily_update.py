#!/usr/bin/env python3
"""
每日定时更新 pre-commit 看板数据。
用法: python scripts/daily_update.py
"""
import os
import sys
import subprocess
import logging
from datetime import datetime
import json

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_DIR, 'logs', 'system')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')

# 确保目录存在
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'update_{datetime.now().strftime("%Y%m%d")}.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """执行命令并记录日志"""
    logger.info(f'开始: {description}')
    logger.info(f'执行命令: {cmd}')

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.stdout:
            logger.info(f'输出:\n{result.stdout}')
        if result.stderr:
            logger.warning(f'错误输出:\n{result.stderr}')

        if result.returncode == 0:
            logger.info(f'完成: {description}')
            return True
        else:
            logger.error(f'失败: {description}, 返回码: {result.returncode}')
            return False

    except Exception as e:
        logger.error(f'执行异常: {description}, 错误: {e}', exc_info=True)
        return False


def update_data():
    """更新所有数据"""
    logger.info('=' * 60)
    logger.info('开始每日 pre-commit 看板数据更新')
    logger.info(f'更新时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    logger.info('=' * 60)

    # 1. 获取历史数据
    success = run_command(
        f'{sys.executable} scripts/fetch_history.py -n 10',
        '获取最新10条开启中PR的pre-commit检查数据'
    )

    if not success:
        logger.error('数据获取失败，终止更新')
        return False

    # 2. 生成历史看板
    success = run_command(
        f'{sys.executable} scripts/generate_history.py',
        '生成历史数据看板'
    )

    if not success:
        logger.error('看板生成失败')
        return False

    # 3. 生成更新摘要
    try:
        history_file = os.path.join(OUTPUT_DIR, 'history_data.json')
        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            total_repos = len(data)
            total_prs = sum(len(comps) for comps in data.values())
            total_failed = sum(len([c for c in comps if c['status'] == 'fail']) for comps in data.values())
            total_violations = sum(sum(c['violations'] for c in comps) for comps in data.values())

            logger.info('=' * 60)
            logger.info('📊 更新摘要')
            logger.info(f'  仓库总数: {total_repos}')
            logger.info(f'  总 PR 数: {total_prs}')
            logger.info(f'  失败 PR: {total_failed}')
            logger.info(f'  总违规数: {total_violations:,}')
            logger.info('=' * 60)

            # 保存最新更新信息
            update_info = {
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_repos': total_repos,
                'total_prs': total_prs,
                'failed_prs': total_failed,
                'total_violations': total_violations,
            }
            with open(os.path.join(OUTPUT_DIR, 'update_info.json'), 'w', encoding='utf-8') as f:
                json.dump(update_info, f, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.warning(f'生成更新摘要失败: {e}')

    logger.info('🎉 每日数据更新完成！')
    return True


if __name__ == '__main__':
    success = update_data()
    sys.exit(0 if success else 1)
