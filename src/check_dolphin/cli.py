"""
Command Line Interface
命令行界面
"""

import argparse
import logging
import sys
from pathlib import Path

from .config import Config
from .api_client import DolphinSchedulerClient
from .monitor import WorkflowMonitor


def setup_logging(config: Config):
    """
    设置日志

    Args:
        config: 配置对象
    """
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = config.get('logging.file', '')

    logging_config = {
        'level': getattr(logging, log_level.upper(), logging.INFO),
        'format': log_format
    }

    if log_file:
        logging_config['filename'] = log_file
        logging_config['filemode'] = 'a'

    logging.basicConfig(**logging_config)


def command_monitor(args, config: Config):
    """
    执行监控命令

    Args:
        args: 命令行参数
        config: 配置对象
    """
    logger = logging.getLogger(__name__)

    # 创建客户端
    client = DolphinSchedulerClient(
        base_url=config.get('dolphinscheduler.base_url'),
        token=config.get('dolphinscheduler.token'),
        timeout=config.get('dolphinscheduler.timeout', 30)
    )

    # 创建监控器
    monitor = WorkflowMonitor(
        client=client,
        max_retry_count=config.get('monitor.max_retry_count', 3),
        retry_interval=config.get('monitor.retry_interval', 60),
        check_interval=config.get('monitor.check_interval', 300)
    )

    # 获取项目代码
    project_codes = args.projects or config.get('projects.codes', [])

    if not project_codes:
        logger.error("No project codes specified. Use --projects or set in config file.")
        sys.exit(1)

    # 开始监控
    try:
        monitor.monitor_and_retry(
            project_codes=project_codes,
            start_date=args.start_date,
            end_date=args.end_date,
            continuous=args.continuous or config.get('monitor.continuous', False)
        )

        # 输出统计信息
        stats = monitor.get_retry_statistics()
        logger.info(f"Retry statistics: {stats}")

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error during monitoring: {str(e)}", exc_info=True)
        sys.exit(1)


def command_status(args, config: Config):
    """
    执行状态查询命令

    Args:
        args: 命令行参数
        config: 配置对象
    """
    logger = logging.getLogger(__name__)

    # 创建客户端
    client = DolphinSchedulerClient(
        base_url=config.get('dolphinscheduler.base_url'),
        token=config.get('dolphinscheduler.token'),
        timeout=config.get('dolphinscheduler.timeout', 30)
    )

    # 创建监控器
    monitor = WorkflowMonitor(client=client)

    # 获取项目代码
    project_codes = args.projects or config.get('projects.codes', [])

    if not project_codes:
        logger.error("No project codes specified. Use --projects or set in config file.")
        sys.exit(1)

    # 显示状态摘要
    for project_code in project_codes:
        logger.info(f"\nProject {project_code} status:")
        summary = monitor.get_workflow_status_summary(project_code)
        for state, count in summary.items():
            logger.info(f"  {state}: {count}")


def command_retry(args, config: Config):
    """
    执行重试命令

    Args:
        args: 命令行参数
        config: 配置对象
    """
    logger = logging.getLogger(__name__)

    # 创建客户端
    client = DolphinSchedulerClient(
        base_url=config.get('dolphinscheduler.base_url'),
        token=config.get('dolphinscheduler.token'),
        timeout=config.get('dolphinscheduler.timeout', 30)
    )

    # 执行重试
    success = client.retry_workflow_instance(
        project_code=args.project,
        instance_id=args.instance_id
    )

    if success:
        logger.info(f"Successfully retried workflow instance {args.instance_id}")
    else:
        logger.error(f"Failed to retry workflow instance {args.instance_id}")
        sys.exit(1)


def command_config(args):
    """
    生成示例配置文件

    Args:
        args: 命令行参数
    """
    config = Config()
    output_path = args.output or 'config.example.yaml'
    config.save_example_config(output_path)
    print(f"Example config file created: {output_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='DolphinScheduler Workflow Monitor and Retry Tool'
    )

    parser.add_argument(
        '-c', '--config',
        help='Config file path (YAML or JSON)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # monitor 命令
    monitor_parser = subparsers.add_parser('monitor', help='Monitor and retry failed workflows')
    monitor_parser.add_argument(
        '-p', '--projects',
        type=int,
        nargs='+',
        help='Project codes to monitor'
    )
    monitor_parser.add_argument(
        '--start-date',
        help='Start date (format: yyyy-MM-dd HH:mm:ss)'
    )
    monitor_parser.add_argument(
        '--end-date',
        help='End date (format: yyyy-MM-dd HH:mm:ss)'
    )
    monitor_parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous monitoring mode'
    )

    # status 命令
    status_parser = subparsers.add_parser('status', help='Show workflow status summary')
    status_parser.add_argument(
        '-p', '--projects',
        type=int,
        nargs='+',
        help='Project codes to check'
    )

    # retry 命令
    retry_parser = subparsers.add_parser('retry', help='Retry a specific workflow instance')
    retry_parser.add_argument(
        '-p', '--project',
        type=int,
        required=True,
        help='Project code'
    )
    retry_parser.add_argument(
        '-i', '--instance-id',
        type=int,
        required=True,
        help='Workflow instance ID to retry'
    )

    # config 命令
    config_parser = subparsers.add_parser('config', help='Generate example config file')
    config_parser.add_argument(
        '-o', '--output',
        help='Output file path (default: config.example.yaml)'
    )

    args = parser.parse_args()

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 处理 config 命令（不需要加载配置）
    if args.command == 'config':
        command_config(args)
        return

    # 加载配置
    config = Config(args.config) if args.config else Config()

    # 设置日志
    setup_logging(config)

    # 执行对应的命令
    if args.command == 'monitor':
        command_monitor(args, config)
    elif args.command == 'status':
        command_status(args, config)
    elif args.command == 'retry':
        command_retry(args, config)


if __name__ == '__main__':
    main()
