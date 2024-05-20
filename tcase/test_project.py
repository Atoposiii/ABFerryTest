import os
import pytest
import allure
from Common.config import Config
from loguru import logger
from datetime import datetime
from Common.core import HttpRequest
from Common.core import ReportStyle

http_client = HttpRequest()

test_cases = Config.get_yaml(Config.get_case_data_dir() + Config.get_case_data_file())


@allure.feature("ABFerry测试")
class TestFuzzSequence:
    @classmethod
    def setup_class(cls):
        # 清空YAML文件内容
        Config.clear_yaml()

    @allure.story("项目相关接口")
    @allure.issue("http://bug.html")
    @allure.severity("blocker")
    @allure.description("调用接口创建新项目")
    @allure.title("项目相关接口-新建项目")
    @allure.testcase(
        "https://rrtq2022032510560773.pingcode.com/testhub/cases/6614b4fa68119cffbd481b7c?#DMX-1  从前端新建一个测试项目")
    @pytest.mark.parametrize("args", test_cases)
    # @pytest.mark.skip(reason="暂时不用")
    def test_create_project(self, args):
        print("测试新建项目接口")
        url = Config.TestEnv + "/api/project/create"
        suffix = datetime.now().strftime('%Y%m%d%H%M%S')
        data = {
            "name": args['program_alias'] + suffix[4:],
            "describe": 'ABFerry',
            "type": 'c/c++'
        }

        with allure.step("step:新增项目"):
            http_client.send_request(data_type="json", method="post", url=url, data=data)
            res = http_client.response
            code = res.json()["code"]
        with allure.step("step:断言新增项目是否成功并记录 project_name"):
            assert code == 20000
            Config.write_cpp_project_info_name(args['program_alias'] + suffix[4:], )

    @allure.story("项目相关接口")
    @allure.severity("blocker")
    @allure.description("测试获取项目列表接口")
    @allure.title("项目相关接口-项目列表")
    @pytest.mark.dependency(depends=["test_create_project"])
    # @pytest.mark.skip(reason="暂时不用")
    def test_get_project_id(self):
        print("测试获取项目projectid")

        url = Config.TestEnv + "/api/project/list"
        with allure.step("step:获取所有项目列表"):
            http_client.send_request(data_type="params", method="get", url=url)
            res = http_client.response
            json_dict = res.json()["data"]

        with allure.step("step:查询新建项目"):
            project_info = Config.get_cpp_project_info()
            project_names_list = [project['name'] for project in project_info]
            projects = []
            for project in json_dict:
                if project['name'] in project_names_list:
                    project_id = project['id']
                    print(project_id)
                    projects.append({
                        "name": project['name'],
                        "id": project['id']
                    })
            ReportStyle.step("新建的project", projects)
            Config.write_cpp_project_info_id(projects)


