"""
Configuration Management
配置文件管理
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径（可选）
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}

        if config_path:
            self.load_config(config_path)
        else:
            self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        self.config = {
            'dolphinscheduler': {
                'base_url': os.getenv('DOLPHIN_BASE_URL', 'http://localhost:12345/dolphinscheduler'),
                'token': os.getenv('DOLPHIN_TOKEN', ''),
                'timeout': int(os.getenv('DOLPHIN_TIMEOUT', '30'))
            },
            'monitor': {
                'max_retry_count': int(os.getenv('MAX_RETRY_COUNT', '3')),
                'retry_interval': int(os.getenv('RETRY_INTERVAL', '60')),
                'check_interval': int(os.getenv('CHECK_INTERVAL', '300')),
                'continuous': os.getenv('CONTINUOUS_MONITOR', 'false').lower() == 'true'
            },
            'projects': {
                'codes': self._parse_project_codes(os.getenv('PROJECT_CODES', ''))
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': os.getenv('LOG_FILE', '')
            }
        }

    def _parse_project_codes(self, codes_str: str) -> list:
        """
        解析项目代码字符串

        Args:
            codes_str: 项目代码字符串，逗号分隔

        Returns:
            项目代码列表
        """
        if not codes_str:
            return []

        try:
            return [int(code.strip()) for code in codes_str.split(',') if code.strip()]
        except ValueError:
            return []

    def load_config(self, config_path: str):
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径
        """
        path = Path(config_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        # 根据文件扩展名选择解析器
        if path.suffix in ['.yaml', '.yml']:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        elif path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")

        # 合并环境变量
        self._merge_env_vars()

    def _merge_env_vars(self):
        """将环境变量合并到配置中（环境变量优先级更高）"""
        if os.getenv('DOLPHIN_BASE_URL'):
            self.config.setdefault('dolphinscheduler', {})['base_url'] = os.getenv('DOLPHIN_BASE_URL')

        if os.getenv('DOLPHIN_TOKEN'):
            self.config.setdefault('dolphinscheduler', {})['token'] = os.getenv('DOLPHIN_TOKEN')

        if os.getenv('MAX_RETRY_COUNT'):
            self.config.setdefault('monitor', {})['max_retry_count'] = int(os.getenv('MAX_RETRY_COUNT'))

        if os.getenv('PROJECT_CODES'):
            self.config.setdefault('projects', {})['codes'] = self._parse_project_codes(os.getenv('PROJECT_CODES'))

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）

        Args:
            key: 配置键（例如: 'dolphinscheduler.base_url'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def save_example_config(self, output_path: str = 'config.example.yaml'):
        """
        保存示例配置文件

        Args:
            output_path: 输出文件路径
        """
        example_config = {
            'dolphinscheduler': {
                'base_url': 'http://localhost:12345/dolphinscheduler',
                'token': 'your-api-token-here',
                'timeout': 30
            },
            'monitor': {
                'max_retry_count': 3,
                'retry_interval': 60,
                'check_interval': 300,
                'continuous': False
            },
            'projects': {
                'codes': [123456789, 987654321],
                'names': ['project1', 'project2']
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'check_dolphin.log'
            },
            'notification': {
                'enabled': False,
                'webhook_url': '',
                'email': ''
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(example_config, f, default_flow_style=False, allow_unicode=True)

    def __str__(self) -> str:
        """返回配置的字符串表示"""
        # 隐藏敏感信息
        safe_config = self.config.copy()
        if 'dolphinscheduler' in safe_config and 'token' in safe_config['dolphinscheduler']:
            safe_config['dolphinscheduler']['token'] = '***'

        return json.dumps(safe_config, indent=2, ensure_ascii=False)
