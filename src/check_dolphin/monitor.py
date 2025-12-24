"""
Workflow Monitor
监控工作流执行状态并处理失败任务
"""

import logging
import time
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta

from .api_client import DolphinSchedulerClient


logger = logging.getLogger(__name__)


class WorkflowMonitor:
    """工作流监控器"""

    # DolphinScheduler 工作流状态常量
    STATE_SUCCESS = 'SUCCESS'
    STATE_FAILURE = 'FAILURE'
    STATE_STOP = 'STOP'
    STATE_RUNNING_EXECUTION = 'RUNNING_EXECUTION'
    STATE_READY_PAUSE = 'READY_PAUSE'
    STATE_READY_STOP = 'READY_STOP'
    STATE_SUBMITTED_SUCCESS = 'SUBMITTED_SUCCESS'
    STATE_SERIAL_WAIT = 'SERIAL_WAIT'

    # 失败状态集合
    FAILED_STATES = {STATE_FAILURE, STATE_STOP}

    # 任务状态常量
    TASK_STATE_SUCCESS = 'SUCCESS'
    TASK_STATE_FAILURE = 'FAILURE'
    TASK_STATE_STOP = 'STOP'
    TASK_STATE_RUNNING = 'RUNNING_EXECUTION'
    TASK_STATE_KILL = 'KILL'

    # 任务失败状态集合
    TASK_FAILED_STATES = {TASK_STATE_FAILURE, TASK_STATE_STOP, TASK_STATE_KILL}

    def __init__(
        self,
        client: DolphinSchedulerClient,
        max_retry_count: int = 3,
        retry_interval: int = 60,
        check_interval: int = 300
    ):
        """
        初始化监控器

        Args:
            client: DolphinScheduler API 客户端
            max_retry_count: 最大重试次数
            retry_interval: 重试间隔（秒）
            check_interval: 检查间隔（秒）
        """
        self.client = client
        self.max_retry_count = max_retry_count
        self.retry_interval = retry_interval
        self.check_interval = check_interval

        # 记录已重试的实例及其重试次数
        self.retry_records: Dict[int, int] = {}

    def get_failed_workflows(
        self,
        project_code: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        获取失败的工作流实例

        Args:
            project_code: 项目代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            失败的工作流实例列表
        """
        failed_workflows = []

        # 获取所有失败状态的工作流
        for state in self.FAILED_STATES:
            workflows = self.client.get_workflow_instances(
                project_code=project_code,
                state_type=state,
                start_date=start_date,
                end_date=end_date,
                page_size=100
            )

            if workflows:
                failed_workflows.extend(workflows)

        logger.info(f"Found {len(failed_workflows)} failed workflows in project {project_code}")
        return failed_workflows

    def check_task_retry_exhausted(self, task: Dict) -> bool:
        """
        检查任务的重试次数是否已经用完

        Args:
            task: 任务实例信息

        Returns:
            是否重试次数已用完（True表示已用完）
        """
        # 任务的最大重试次数（任务配置中的重试次数）
        max_retry_times = task.get('maxRetryTimes', 0)
        # 任务已经重试的次数
        retry_times = task.get('retryTimes', 0)

        # 如果没有配置重试次数，认为重试已完成
        if max_retry_times == 0:
            return True

        # 检查是否已经达到最大重试次数
        return retry_times >= max_retry_times

    def validate_workflow_tasks(
        self,
        project_code: int,
        workflow_instance_id: int
    ) -> tuple[bool, str]:
        """
        验证工作流中的所有任务是否都已失败且重试次数用完

        Args:
            project_code: 项目代码
            workflow_instance_id: 工作流实例 ID

        Returns:
            (是否可以重试, 原因说明)
        """
        # 获取工作流的所有任务实例
        tasks = self.client.get_task_instances(
            project_code=project_code,
            process_instance_id=workflow_instance_id
        )

        if not tasks:
            logger.warning(f"No tasks found for workflow instance {workflow_instance_id}")
            return False, "No tasks found in workflow"

        # 统计任务状态
        total_tasks = len(tasks)
        failed_tasks = 0
        running_tasks = 0
        retry_not_exhausted_tasks = []

        for task in tasks:
            task_name = task.get('name', 'Unknown')
            task_state = task.get('state', '')
            task_id = task.get('id', 0)

            # 检查任务状态
            if task_state in self.TASK_FAILED_STATES:
                failed_tasks += 1

                # 检查任务的重试次数是否已用完
                if not self.check_task_retry_exhausted(task):
                    max_retry_times = task.get('maxRetryTimes', 0)
                    retry_times = task.get('retryTimes', 0)
                    retry_not_exhausted_tasks.append({
                        'name': task_name,
                        'id': task_id,
                        'retry_times': retry_times,
                        'max_retry_times': max_retry_times
                    })

            elif task_state == self.TASK_STATE_RUNNING:
                running_tasks += 1

        logger.info(
            f"Workflow {workflow_instance_id} task status: "
            f"total={total_tasks}, failed={failed_tasks}, running={running_tasks}"
        )

        # 如果有任务还在运行中，不能重试
        if running_tasks > 0:
            reason = f"Workflow has {running_tasks} tasks still running"
            logger.info(f"Cannot retry workflow {workflow_instance_id}: {reason}")
            return False, reason

        # 如果有任务重试次数未用完，不能重试
        if retry_not_exhausted_tasks:
            reason = (
                f"Some tasks have not exhausted their retry attempts: "
                f"{', '.join([f\"{t['name']}({t['retry_times']}/{t['max_retry_times']})\" for t in retry_not_exhausted_tasks])}"
            )
            logger.info(f"Cannot retry workflow {workflow_instance_id}: {reason}")
            return False, reason

        # 如果不是所有任务都失败了，不能重试
        if failed_tasks < total_tasks:
            reason = f"Not all tasks have failed (failed: {failed_tasks}/{total_tasks})"
            logger.info(f"Cannot retry workflow {workflow_instance_id}: {reason}")
            return False, reason

        # 所有检查通过，可以重试
        logger.info(
            f"Workflow {workflow_instance_id} validation passed: "
            f"all {total_tasks} tasks have failed and exhausted retries"
        )
        return True, "All tasks have failed and exhausted their retry attempts"

    def should_retry(self, instance_id: int) -> bool:
        """
        判断是否应该重试（基于监控器的重试次数限制）

        Args:
            instance_id: 工作流实例 ID

        Returns:
            是否应该重试
        """
        retry_count = self.retry_records.get(instance_id, 0)

        if retry_count >= self.max_retry_count:
            logger.warning(
                f"Workflow instance {instance_id} has reached max retry count "
                f"({self.max_retry_count}), skipping"
            )
            return False

        return True

    def retry_failed_workflow(
        self,
        project_code: int,
        workflow: Dict,
        validate_tasks: bool = True
    ) -> bool:
        """
        重试失败的工作流

        Args:
            project_code: 项目代码
            workflow: 工作流实例信息
            validate_tasks: 是否验证任务状态（默认为True）

        Returns:
            是否重试成功
        """
        instance_id = workflow.get('id')
        workflow_name = workflow.get('name', 'Unknown')
        state = workflow.get('state', 'Unknown')

        if not instance_id:
            logger.error("Workflow instance ID not found")
            return False

        # 检查监控器的重试次数限制
        if not self.should_retry(instance_id):
            return False

        # 验证任务状态（确保所有任务都失败且重试次数用完）
        if validate_tasks:
            can_retry, reason = self.validate_workflow_tasks(
                project_code=project_code,
                workflow_instance_id=instance_id
            )

            if not can_retry:
                logger.warning(
                    f"Skip retry for workflow {workflow_name} (ID: {instance_id}): {reason}"
                )
                return False

        logger.info(
            f"Retrying workflow: {workflow_name} (ID: {instance_id}, State: {state})"
        )

        # 执行重试
        success = self.client.retry_workflow_instance(
            project_code=project_code,
            instance_id=instance_id
        )

        if success:
            # 更新重试记录
            self.retry_records[instance_id] = self.retry_records.get(instance_id, 0) + 1
            logger.info(
                f"Successfully retried workflow {instance_id}, "
                f"retry count: {self.retry_records[instance_id]}"
            )
        else:
            logger.error(f"Failed to retry workflow {instance_id}")

        return success

    def monitor_and_retry(
        self,
        project_codes: List[int],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        continuous: bool = False
    ):
        """
        监控并重试失败的工作流

        Args:
            project_codes: 项目代码列表
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            continuous: 是否持续监控
        """
        logger.info(f"Starting workflow monitoring for projects: {project_codes}")

        while True:
            for project_code in project_codes:
                try:
                    # 获取失败的工作流
                    failed_workflows = self.get_failed_workflows(
                        project_code=project_code,
                        start_date=start_date,
                        end_date=end_date
                    )

                    # 重试失败的工作流
                    for workflow in failed_workflows:
                        try:
                            self.retry_failed_workflow(project_code, workflow)

                            # 重试之间添加间隔
                            if self.retry_interval > 0:
                                time.sleep(self.retry_interval)

                        except Exception as e:
                            logger.error(
                                f"Error retrying workflow {workflow.get('id')}: {str(e)}"
                            )

                except Exception as e:
                    logger.error(f"Error monitoring project {project_code}: {str(e)}")

            # 如果不是持续监控，退出循环
            if not continuous:
                break

            # 等待下一次检查
            logger.info(f"Waiting {self.check_interval} seconds before next check...")
            time.sleep(self.check_interval)

    def get_workflow_status_summary(self, project_code: int) -> Dict[str, int]:
        """
        获取工作流状态摘要

        Args:
            project_code: 项目代码

        Returns:
            状态摘要字典
        """
        summary = {
            'total': 0,
            'success': 0,
            'failure': 0,
            'running': 0,
            'other': 0
        }

        workflows = self.client.get_workflow_instances(
            project_code=project_code,
            page_size=100
        )

        if not workflows:
            return summary

        for workflow in workflows:
            state = workflow.get('state', '')
            summary['total'] += 1

            if state == self.STATE_SUCCESS:
                summary['success'] += 1
            elif state in self.FAILED_STATES:
                summary['failure'] += 1
            elif state == self.STATE_RUNNING_EXECUTION:
                summary['running'] += 1
            else:
                summary['other'] += 1

        return summary

    def get_retry_statistics(self) -> Dict:
        """
        获取重试统计信息

        Returns:
            重试统计字典
        """
        if not self.retry_records:
            return {
                'total_retried': 0,
                'max_retries': 0,
                'avg_retries': 0
            }

        total_retried = len(self.retry_records)
        max_retries = max(self.retry_records.values())
        avg_retries = sum(self.retry_records.values()) / total_retried

        return {
            'total_retried': total_retried,
            'max_retries': max_retries,
            'avg_retries': round(avg_retries, 2),
            'retry_details': self.retry_records
        }
