import json
import time
import pytest
import allure
from Common.config import Config
from Common.core import HttpRequest
from Common.core import ReportStyle

http_client = HttpRequest()

test_cases = Config.get_yaml(Config.get_case_data_dir() + Config.get_case_data_file())
instance_id = None


@allure.feature("ABFerry测试")
class TestFuzzParallel:
    @allure.story("测试入口模块")
    @allure.severity("blocker")
    @allure.description("创建测试实例")
    @pytest.mark.parametrize("args", test_cases)
    # @pytest.mark.skip(reason="暂时不用")
    @allure.title("测试入口模块相关接口-选择内置源码-创建测试用例")
    def test_create_test_instance(self, args):
        '''创建测试实例'''
        print("选择内置源码-创建测试实例")
        print(args)
        projects = Config.get_cpp_project_info()
        proj_id = ""
        proj_name = ""
        name = ""
        for project in projects:
            proj_name = project["name"]
            name = proj_name[:-10]
            if args["program_alias"] == name:
                proj_id = project["id"]
                break
        # source_code_pkg_path = args['source_code_pkg_path']
        # data_path = source_code_pkg_path
        # print(data_path)

        crate_header = {
            "Content-Type": "application/json",
            # "Authorization": token
        }

        create_harness_url = Config.TestEnv + "/api/instance/createInstance"
        data = {
            "projectId": proj_id,
            "projectName": proj_name,
            "configMode": "3",
            "fileId": name,
            "taskName": name,
            "fileName": name,
            "buildPath": "build",
            "preCmd": "",
            "utConfig": [],
            "duration": 60,
            "version": "1.0",
            "cmakeConfig": "",
            "buildConfig": "",
            "buildShell": "",
            "variationConfig": []
        }
        ReportStyle.step("请求Url", create_harness_url)
        ReportStyle.step("请求数据：", data)

        with allure.step("step: 使用内置源码创建测试用例"):
            http_client.send_request(data_type="json", method="post", url=create_harness_url, header=crate_header, data=data)
            resp = http_client.response.json()
            harness_data = resp["message"]
            ReportStyle.step("请求结果: ", harness_data)
            print("---------------------------------------------------------------------------")
            print(harness_data)

        with allure.step("step: 断言测试用例创建成功"):
            code = resp["code"]
            # 断言创建用例的接口返回状态码是否为200
            assert code == 20000
            # 断言返回的data字段不为空
            instance_id = resp["data"]
            assert instance_id is not None

        with allure.step("step: 记录测试用例"):
            project_info = Config.get_cpp_project_info()
            project_id_list = [project['id'] for project in project_info]
            projects = []
            for project_id in project_id_list:
                if project_id == proj_id:
                    projects.append({
                                "name": proj_name,
                                "id": proj_id,
                                "instance_id": instance_id
                            })
            ReportStyle.step("测试用例: ", projects)
            Config.write_cpp_project_info_id(projects)

        with allure.step("step: 获取用例列表并轮询用例运行状态"):
            # 等用例从等待状态变成运行状态
            time.sleep(60)
            url = Config.TestEnv + "/api/instance/getInstanceList"
            params = {'projectId': proj_id}
            state = 1
            while state == 1:
                http_client.send_request(data_type="params", method="get", url=url, data=params)
                resp = http_client.response.json()
                code = resp["code"]
                # 断言查询用例的接口返回状态码是否为200
                assert code == 20000
                instances = resp.get('data')
                instance = next((item for item in instances if item["id"] == instance_id), None)
                # 断言用例是否存在
                assert instance is not None
                state = int(instance["state"])
                # 状态为1，表示正在运行
                if state == 1:
                    # 等待5秒后继续检查状态
                    time.sleep(30)
        with allure.step("step: 测试用例状态发生改变"):
            state_message = {
                0: "等待时间过长",
                2: "运行失败",
                9: "运行成功"
            }
            result = {"测试用例状态": state_message.get(state, "未知状态")}
            ReportStyle.step("测试用例状态: ", result)
            assert state == 9

