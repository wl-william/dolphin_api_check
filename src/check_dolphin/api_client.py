"""
DolphinScheduler API Client
用于与 DolphinScheduler REST API 交互
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class DolphinSchedulerClient:
    """DolphinScheduler API 客户端"""

    def __init__(self, base_url: str, token: str, timeout: int = 30):
        """
        初始化 DolphinScheduler 客户端

        Args:
            base_url: DolphinScheduler API 基础 URL (例如: http://localhost:12345/dolphinscheduler)
            token: API 访问令牌
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'token': token
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法 (GET, POST, etc.)
            endpoint: API 端点
            **kwargs: 其他请求参数

        Returns:
            响应数据字典，如果请求失败返回 None
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()

            data = response.json()

            if not data.get('success', False):
                logger.error(f"API request failed: {data.get('msg', 'Unknown error')}")
                return None

            return data.get('data')

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return None

    def get_projects(self, page_no: int = 1, page_size: int = 100) -> Optional[List[Dict]]:
        """
        获取项目列表

        Args:
            page_no: 页码
            page_size: 每页大小

        Returns:
            项目列表
        """
        params = {
            'pageNo': page_no,
            'pageSize': page_size
        }

        result = self._make_request('GET', '/projects', params=params)

        if result and 'totalList' in result:
            return result['totalList']

        return []

    def get_workflow_instances(
        self,
        project_code: int,
        page_no: int = 1,
        page_size: int = 100,
        workflow_name: Optional[str] = None,
        state_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        获取工作流实例列表

        Args:
            project_code: 项目代码
            page_no: 页码
            page_size: 每页大小
            workflow_name: 工作流名称（可选）
            state_type: 状态类型（可选，例如: FAILURE, SUCCESS）
            start_date: 开始日期（可选，格式: yyyy-MM-dd HH:mm:ss）
            end_date: 结束日期（可选，格式: yyyy-MM-dd HH:mm:ss）

        Returns:
            工作流实例列表
        """
        params = {
            'pageNo': page_no,
            'pageSize': page_size
        }

        if workflow_name:
            params['searchVal'] = workflow_name
        if state_type:
            params['stateType'] = state_type
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date

        endpoint = f'/projects/{project_code}/process-instances'
        result = self._make_request('GET', endpoint, params=params)

        if result and 'totalList' in result:
            return result['totalList']

        return []

    def get_workflow_instance(self, project_code: int, instance_id: int) -> Optional[Dict]:
        """
        获取单个工作流实例详情

        Args:
            project_code: 项目代码
            instance_id: 实例 ID

        Returns:
            工作流实例详情
        """
        endpoint = f'/projects/{project_code}/process-instances/{instance_id}'
        return self._make_request('GET', endpoint)

    def retry_workflow_instance(
        self,
        project_code: int,
        instance_id: int
    ) -> bool:
        """
        重试失败的工作流实例

        Args:
            project_code: 项目代码
            instance_id: 实例 ID

        Returns:
            是否重试成功
        """
        endpoint = f'/projects/{project_code}/executors/execute'

        data = {
            'processInstanceId': instance_id,
            'executeType': 'REPEAT_RUNNING'
        }

        result = self._make_request('POST', endpoint, json=data)

        if result:
            logger.info(f"Successfully retried workflow instance {instance_id}")
            return True
        else:
            logger.error(f"Failed to retry workflow instance {instance_id}")
            return False

    def get_task_instances(
        self,
        project_code: int,
        process_instance_id: int
    ) -> Optional[List[Dict]]:
        """
        获取工作流实例的任务实例列表

        Args:
            project_code: 项目代码
            process_instance_id: 工作流实例 ID

        Returns:
            任务实例列表
        """
        endpoint = f'/projects/{project_code}/process-instances/{process_instance_id}/tasks'
        result = self._make_request('GET', endpoint)

        if isinstance(result, list):
            return result

        return []
