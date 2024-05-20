import json
import os


class Allure_Results:
    # 设置Allure结果数据的目录
    # allure_results_directory = 'allure_results'
    @staticmethod
    def count_allure_results(allure_results_directory=None):
        # 初始化统计变量
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        broken_tests = 0
        coverage = 0

        # 遍历Allure结果目录中的所有文件
        for filename in os.listdir(allure_results_directory):
            if filename.endswith('-result.json'):
                filepath = os.path.join(allure_results_directory, filename)
                with open(filepath, 'r') as file:
                    data = json.load(file)
                    if data["description"] == "创建测试实例":
                        # 状态可以是'passed', 'failed', 'skipped'等
                        status = data['status']
                        if status == 'passed':
                            passed_tests += 1
                        elif status == 'failed':
                            failed_tests += 1
                        elif status == 'skipped':
                            skipped_tests += 1
                        elif status == 'broken':
                            broken_tests += 1
                        total_tests += 1
                    elif data["description"] == "获取覆盖率":
                        # 状态可以是'passed', 'failed'
                        status = data['status']
                        if status == 'failed':
                            coverage += 1

        return {
            "Total": total_tests,
            "Passed": passed_tests,
            "Failed": failed_tests,
            "Skipped": skipped_tests,
            "Broken": broken_tests,
            "Coverage": coverage,
        }
