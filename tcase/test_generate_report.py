import json
import os
from datetime import datetime
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
            "type": "instance"
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

        # with ((allure.step("step: 断言函数覆盖率是否正常"))):
        #     with assume:
        #         assert test_fuzzer_function_covered_rate >= base_fuzzer_function_covered_rate \
        #                or test_fuzzer_function_covered_rate > (base_fuzzer_function_covered_rate - 3)
        #
        # with allure.step("step: 断言行覆盖率是否正常"):
        #     with assume:
        #         assert test_fuzzer_line_covered_rate >= base_fuzzer_line_covered_rate \
        #                or test_fuzzer_line_covered_rate > (base_fuzzer_line_covered_rate - 3)

    def gather_bugs_info(self, args, report_data):
        instance_id = None
        name = None
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


        with allure.step("step: 统计BUG数量"):
            bug_count = len(bugs)
            bug_stats = {
                "bug总数": bug_count,
                "bug类型": 0,
                "用例bug数": 0,
                "源码bug数": 0,
            }
            test_bugs = []

            for item in bugs:
                level = item["level"]
                if level == "0":
                    bug_stats["用例bug数"] += 1
                elif level == "1":
                    bug_stats["源码bug数"] += 1
                    bug_name = item["bugName"]
                    source_line = item.get("sourceLine")
                    source_file_path = item.get("sourceFilePath").split('/')[-2:]
                    source_file_path = '/'.join(source_file_path[-2:])
                    info = f"{source_file_path}: {source_line}"
                    test_bugs.append(
                        {
                            "instance_name": name,
                            "bug_id": "",
                            "bug_name": bug_name,
                            "info": info
                        }
                    )
            report_data.update(bug_stats)
            report_data["bugs"] = test_bugs


    def gather_run_time(self, args, report_data):
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
        url = Config.TestEnv + "/api/instance/getInstanceList"
        params = {'projectId': proj_id}
        http_client.send_request(data_type="params", method="get", url=url, data=params)
        resp = http_client.response.json()
        # 定义时间格式
        time_format = "%Y-%m-%d %H:%M:%S"
        # 创建时间
        create_time_str = resp["data"][0]["createTime"]
        print(create_time_str)
        # 更新时间
        update_time_str = resp["data"][0]["updateTime"]
        print(update_time_str)
        # 将字符串转换为datetime对象
        create_time = datetime.strptime(create_time_str, time_format)
        update_time = datetime.strptime(update_time_str, time_format)
        # 计算时间差
        time_difference = update_time - create_time
        # 将时间差转换为秒
        run_duration_seconds = int(time_difference.total_seconds())
        # 将秒转换为分钟
        run_duration_minutes = run_duration_seconds / 60
        formatted_duration = f"{run_duration_minutes:.2f}"
        report_data["运行时长"] = formatted_duration
        print("运行时长为 {} 分钟".format(formatted_duration))

    def write_report(self, report_data):
        print(report_data)
        report = [report_data["用例名"], "", report_data["行覆盖提升率"], report_data["函数覆盖提升率"],
                  report_data["源码bug数"], report_data["运行时长"], report_data["代码行"], report_data["函数个数"],
                  report_data["gtest行覆盖"], report_data["gtest行覆盖率"], report_data["gtest函数覆盖"],
                  report_data["gtest函数覆盖率"], report_data["fuzzer行覆盖"], report_data["fuzzer行覆盖率"],
                  report_data["fuzzer函数覆盖"], report_data["fuzzer函数覆盖率"], report_data["bug总数"]
                  ]
        print(report)
        report_bugs = report_data['bugs']
        generate_report(report, report_bugs)
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
        self.gather_run_time(args, report_data)
        self.write_report(report_data)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
