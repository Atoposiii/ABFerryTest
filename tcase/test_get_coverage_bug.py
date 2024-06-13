import json
import time
import pytest
import allure
from pytest_assume.plugin import assume
from Common.config import Config
from Common.core import HttpRequest
from Common.core import ReportStyle

http_client = HttpRequest()

test_cases = Config.get_yaml(Config.get_case_data_dir() + Config.get_case_data_file())


@allure.feature("ABFerry测试")
class TestFuzzResultInfo:
    @allure.story("测试入口模块")
    @allure.severity("blocker")
    @allure.description("获取覆盖率")
    @pytest.mark.parametrize("args", test_cases)
    # @pytest.mark.skip(reason="暂时不用")
    @allure.title("测试入口模块相关接口-获取测试用例覆盖率")
    def test_instance_coverages(self, args):
        instance_id = None
        with allure.step("step: 读取yaml文件，获取测试用例id"):
            project_info = Config.get_cpp_project_info()
            for project in project_info:
                name = project["name"][:-10]
                if name == args["program_alias"]:
                    instance_id = project["instance_id"]
                    ReportStyle.step("测试用例id: ", instance_id)
                    break

        url = Config.TestEnv + "/api/structure/instanceCoverages"
        params = {
            "instanceId": instance_id,
            "type": "project"
        }
        http_client.send_request(data_type="params", method="get", url=url, data=params)
        resp = http_client.response.json()

        with allure.step("step:获取用例覆盖率接口的返回状态码"):
            code = resp["code"]
            assert code == 20000
        with allure.step("step: 断言获取用例覆盖率接口的返回data不为空"):
            coverages = resp["data"]
            assert coverages is not None
        with allure.step("step: 统计覆盖率"):
            stats = {}
            for coverage in coverages:
                # 多ut使用
                # unit_name = coverage["unitName"]
                # if unit_name not in stats:
                if coverage["projectId"] != "":
                    # stats[unit_name]
                    stats = {
                        "gtest行覆盖Total": coverage["gtestLineTotal"],
                        "gtest行覆盖": coverage["gtestLineCovered"],
                        "gtest函数覆盖Total": coverage["gtestFunctionTotal"],
                        "gtest函数覆盖": coverage["gtestFunctionCovered"],
                        "fuzzer行覆盖Total": coverage["fuzzerLineTotal"],
                        "fuzzer行覆盖": coverage["fuzzerLineCovered"],
                        "fuzzer函数覆盖Total": coverage["fuzzerFunctionTotal"],
                        "fuzzer函数覆盖": coverage["fuzzerFunctionCovered"],
                        "gtest行覆盖率": "{:.2f}%".format(
                            coverage["gtestLineCovered"] / coverage["gtestLineTotal"] * 100),
                        "gtest函数覆盖率": "{:.2f}%".format(
                            coverage["gtestFunctionCovered"] / coverage["gtestFunctionTotal"] * 100),
                        "fuzzer行覆盖率": "{:.2f}%".format(
                            coverage["fuzzerLineCovered"] / coverage["fuzzerLineTotal"] * 100),
                        "fuzzer函数覆盖率": "{:.2f}%".format(
                            coverage["fuzzerFunctionCovered"] / coverage["fuzzerFunctionTotal"] * 100),
                    }
            ReportStyle.step("覆盖率: ", stats)
        test_fuzzer_line_covered_rate = float(stats["fuzzer行覆盖率"].split("%")[0])
        test_fuzzer_function_covered_rate = float(stats["fuzzer函数覆盖率"].split("%")[0])
        base_fuzzer_line_covered_rate = float(args.get("fuzzer_line_covered_rate").split("%")[0])
        base_fuzzer_function_covered_rate = float(args.get("fuzzer_function_covered_rate").split("%")[0])
        with ((allure.step("step: 断言函数覆盖率是否正常"))):
            with assume:
                #
                assert test_fuzzer_function_covered_rate >= base_fuzzer_function_covered_rate \
                or test_fuzzer_function_covered_rate > (base_fuzzer_function_covered_rate - 3)

        with allure.step("step: 断言行覆盖率是否正常"):
            with assume:
                #
                assert test_fuzzer_line_covered_rate >= base_fuzzer_line_covered_rate \
                or test_fuzzer_line_covered_rate > (base_fuzzer_line_covered_rate - 3)


    @allure.story("测试入口模块")
    @allure.severity("blocker")
    @allure.description("获取bug数")
    @pytest.mark.parametrize("args", test_cases)
    # @pytest.mark.skip(reason="暂时不用")
    @allure.title("测试入口模块相关接口-获取测试用例bug数")
    def test_instance_bugs(self, args):
        instance_id = None
        with allure.step("step: 读取yaml文件，获取测试用例id"):
            project_info = Config.get_cpp_project_info()
            for project in project_info:
                name = project["name"][:-10]
                if name == args["program_alias"]:
                    instance_id = project["instance_id"]
                    break

        url = Config.TestEnv + "/api/bugs/instanceBugs"
        params = {'instanceId': instance_id}
        http_client.send_request(data_type="params", method="get", url=url, data=params)
        resp = http_client.response.json()
        with allure.step("step: 获取用例bug数接口的返回状态码"):
            code = resp["code"]
            assert code == 20000
        with allure.step("step: 断言获取用例bug数接口的返回data不为空"):
            bugs = resp["data"]
            assert bugs is not None
        with allure.step("step: 统计BUG详情"):
            stats = {}
            for bug in bugs:
                id = bug["id"].split("-")[0]
                stats[id] = {
                    "类型": bug["bugName"],
                    "测试名称": bug["unitName"],
                    "驱动名称": bug["driverName"],
                    "中断来源": bug["bugType"],
                    "bug来源": "用例" if bug["level"] == 0 else "源码"
                }
            ReportStyle.step("BUG列表: ", stats)

        test_bugs = []
        with allure.step("step: 统计BUG数量"):
            bug_count = len(bugs)
            # 初始化字典来存储结果
            bug_stats = {
                "bug总数": bug_count,
                "bug类型": 0,
                "用例bug数": 0,
                "源码bug数": 0,
            }

            # 初始化一个集合来存储不同的bug类型，以便计算bug的类型数
            bug_types = set()

            for item in bugs:
                bug_name = item["bugName"]
                source_line = item["sourceLine"]

                level = item["level"]
                # 更新bug类型的集合
                bug_types.add(bug_name)

                # 根据level来更新用例的数量或源码的数量
                if level == "0":
                    bug_stats["用例bug数"] += 1
                elif level == "1":
                    bug_stats["源码bug数"] += 1
                    test_bugs.append(
                        {
                            "name": bug_name,
                            "location": source_line
                        }
                    )

            # 更新bug的类型数
            bug_stats["bug类型"] = len(bug_types)

            ReportStyle.step("BUG数据总览: ", bug_stats)
        with allure.step("step: 断言bug的类型与定位是否一致"):
            base_bugs = args["bugs"]
            with assume:
                test_bugs = None if not test_bugs else test_bugs
                if base_bugs is not None and test_bugs is not None:
                    assert sorted(base_bugs) == sorted(test_bugs)
                    ReportStyle.step("bug的类型与定位", test_bugs)
                else:
                    assert base_bugs == test_bugs
                    ReportStyle.step("bug的类型与定位", None)

