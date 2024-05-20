"""插件类"""
import json
import os
import re
from copy import deepcopy
from string import Template
from zipfile import ZipFile
from zipfile import ZIP_DEFLATED
from datetime import datetime
from typing import Optional
from typing import Dict
from typing import Any
from typing import Union
from decimal import Decimal

import allure
import yaml
from jsonpath import jsonpath
from loguru import logger
from requests import Session
from requests import Response


class ReportStyle:
    """allure 报告样式"""

    @staticmethod
    def step(step: str, var: Optional[Union[str, Dict[str, Any]]] = None):
        with allure.step(step):
            allure.attach(
                json.dumps(var, ensure_ascii=False, indent=4),
                "附件内容",
                allure.attachment_type.JSON,
            )

    @staticmethod
    def title(title: str):
        allure.dynamic.title(title)


class HttpRequest(Session):
    """请求类实现"""

    data_type_list = ["params", "data", "json"]

    def __init__(self):
        self._last_response = None
        super().__init__()

    @property
    def response(self) -> Response:
        return self._last_response

    @response.setter
    def response(self, value):
        self._last_response = value

    def send_request(
        self, data_type: str, method, url, header=None, data=None, file=None, **kwargs
    ):
        if data_type.lower() in HttpRequest.data_type_list:
            extra_args = {data_type: data}
        else:
            raise ValueError("可选关键字为params, json, data")
        self.response = self.request(
            method=method, url=url, files=file, headers=header, **extra_args, **kwargs
        )
        req_info = {
            "请求地址": url,
            "请求方法": method,
            "请求头": header,
            "请求数据": data,
            "上传文件": str(file),
        }
        ReportStyle.step("Request Info", req_info)
        logger.info(req_info)
        rep_info = {
            "响应耗时(ms)": self.response.elapsed.total_seconds() * 1000,
            "状态码": self.response.status_code,
            "响应数据": self.response.json(),
        }
        logger.info(rep_info)
        ReportStyle.step("Response Info", rep_info)
