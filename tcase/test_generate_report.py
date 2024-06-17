import json
import os
import pytest
import allure
from pytest_assume.plugin import assume
from Common.config import Config
from Common.core import HttpRequest
from Common.core import ReportStyle
from Common.generate_report import generate_report
http_client = HttpRequest()

test_cases = Config.get_yaml(Config.get_case_data_dir() + Config.get_case_data_file())


@pytest.fixture
def report_data():
    return {}


@allure.feature("ABFerry测试")
class TestFuzzResultInfo:
    def gather_coverage_info(self, args, report_data):
        instance_id = None
        with allure.step("step: 读取yaml文件，获取测试用例id"):
            project_info = Config.get_cpp_project_info()
            for project in project_info:
                name = project["name"][:-10]
                report_data["用例名"] = name
                if name == args["program_alias"]:
                    instance_id = project["instance_id"]
                    # ReportStyle.step("测试用例id: ", instance_id)
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
                if coverage["projectId"] != "":
                    stats = {
                        "gtest行覆盖Total": coverage["gtestLineTotal"],
                        "gtest行覆盖": coverage["gtestLineCovered"],
                        "gtest函数覆盖Total": coverage["gtestFunctionTotal"],
                        "gtest函数覆盖": coverage["gtestFunctionCovered"],
                        "fuzzer行覆盖Total": coverage["abferryLineTotal"],
                        "fuzzer行覆盖": coverage["abferryLineCovered"],
                        "fuzzer函数覆盖Total": coverage["abferryFunctionTotal"],
                        "fuzzer函数覆盖": coverage["abferryFunctionCovered"],
                        "gtest行覆盖率": "{:.2f}%".format(
                            coverage["gtestLineCovered"] / coverage["gtestLineTotal"] * 100),
                        "gtest函数覆盖率": "{:.2f}%".format(
                            coverage["gtestFunctionCovered"] / coverage["gtestFunctionTotal"] * 100),
                        "fuzzer行覆盖率": "{:.2f}%".format(
                            coverage["abferryLineCovered"] / coverage["abferryLineTotal"] * 100),
                        "fuzzer函数覆盖率": "{:.2f}%".format(
                            coverage["abferryFunctionCovered"] / coverage["abferryFunctionTotal"] * 100),
                    }
            # ReportStyle.step("覆盖率: ", stats)

            report_data["代码行"] = stats["gtest行覆盖Total"]
            report_data["函数个数"] = stats["gtest函数覆盖Total"]

            # 将统计结果合并到报告数据中
            report_data.update(stats)

        test_gtest_line_covered_rate = float(stats["gtest行覆盖率"].split("%")[0])
        test_gtest_function_covered_rate = float(stats["gtest函数覆盖率"].split("%")[0])
        test_fuzzer_line_covered_rate = float(stats["fuzzer行覆盖率"].split("%")[0])
        test_fuzzer_function_covered_rate = float(stats["fuzzer函数覆盖率"].split("%")[0])
        base_fuzzer_line_covered_rate = float(args.get("fuzzer_line_covered_rate").split("%")[0])
        base_fuzzer_function_covered_rate = float(args.get("fuzzer_function_covered_rate").split("%")[0])

        report_data["行覆盖提升率"] = "{:.2f}%".format(
            ((test_fuzzer_line_covered_rate - test_gtest_line_covered_rate) / test_gtest_line_covered_rate) * 100)
        report_data["函数覆盖提升率"] = "{:.2f}%".format(((
                                                                      test_fuzzer_function_covered_rate - test_gtest_function_covered_rate) / test_gtest_function_covered_rate) * 100)

        with ((allure.step("step: 断言函数覆盖率是否正常"))):
            with assume:
                assert test_fuzzer_function_covered_rate >= base_fuzzer_function_covered_rate \
                       or test_fuzzer_function_covered_rate > (base_fuzzer_function_covered_rate - 3)

        with allure.step("step: 断言行覆盖率是否正常"):
            with assume:
                assert test_fuzzer_line_covered_rate >= base_fuzzer_line_covered_rate \
                       or test_fuzzer_line_covered_rate > (base_fuzzer_line_covered_rate - 3)

    def gather_bugs_info(self, args, report_data):
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
            # ReportStyle.step("BUG列表: ", stats)

        test_bugs = []
        with allure.step("step: 统计BUG数量"):
            bug_count = len(bugs)
            bug_stats = {
                "bug总数": bug_count,
                "bug类型": 0,
                "用例bug数": 0,
                "源码bug数": 0,
            }
            bug_types = set()

            for item in bugs:
                bug_name = item["bugName"]
                source_line = item.get("sourceLine")

                level = item["level"]
                bug_types.add(bug_name)

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

            bug_stats["bug类型"] = len(bug_types)
            report_data.update(bug_stats)
            report_data.update({"bug类型": bug_types})
            # ReportStyle.step("BUG数据总览: ", bug_stats)

        with allure.step("step: 断言bug的类型与定位是否一致"):
            base_bugs = args["bugs"]
            with assume:
                test_bugs = None if not test_bugs else test_bugs
                if base_bugs is not None and test_bugs is not None:
                    sorted_base_bugs = sorted(base_bugs, key=lambda x: (x['name'], x['location']))
                    sorted_test_bugs = sorted(test_bugs, key=lambda x: (x['name'], x['location']))
                    assert sorted_base_bugs == sorted_test_bugs
                    # ReportStyle.step("bug的类型与定位", test_bugs)
                else:
                    assert base_bugs == test_bugs
                    # ReportStyle.step("bug的类型与定位", None)

    import os

    def write_report(self, report_data):
        # print(report_data)
        elements = list(report_data["bug类型"])
        separator = ', '
        result_string = separator.join(elements)
        report = [report_data["用例名"], report_data["代码行"], report_data["函数个数"], report_data["gtest行覆盖"],
                report_data["gtest函数覆盖"], report_data["fuzzer行覆盖"], report_data["fuzzer函数覆盖"],
                report_data["gtest行覆盖率"], report_data["gtest函数覆盖率"], report_data["fuzzer行覆盖率"], report_data["fuzzer函数覆盖率"],
                report_data["行覆盖提升率"], report_data["函数覆盖提升率"], report_data["bug总数"], result_string, report_data["用例bug数"],
                report_data["源码bug数"]]
        print(report)
        generate_report(report)
        # import csv
        # from datetime import datetime
        # today = datetime.today().strftime('%Y-%m-%d')
        # filename = f"{today}.csv"
        #
        # file_exists = os.path.isfile(filename)
        #
        # with open(filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
        #     fieldnames = report_data.keys()
        #     writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        #
        #     if not file_exists:
        #         writer.writeheader()
        #
        #     writer.writerow(report_data)
        #
        # print(f"数据已保存到文件 {filename}")

    @pytest.mark.parametrize("args", test_cases)
    def test_run_all(self, args, report_data):
        self.gather_coverage_info(args, report_data)
        self.gather_bugs_info(args, report_data)
        self.write_report(report_data)


if __name__ == "__main__":
    pytest.main(["-v", __file__])



