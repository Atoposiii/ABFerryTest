# -*- coding: utf-8 -*-
import requests
from datetime import datetime
import hashlib
import base64
import hmac
from Common.allure_utils import Allure_Results
from Common.config import Config

def gen_sign(timestamp, secret):
    # 拼接timestamp和secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
    # 对结果进行base64处理
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return sign


def push_report(web_hook, timestamp, sign, results):
    header = {
        "Content-Type": "application/json;charset=UTF-8"
    }
    message_body = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "interactive",
        "card": {
            "elements": [
                {
                    "fields": [
                        {
                            "text": {
                                "content": f'🔆 执行用例数量：{results["Total"]}\n',
                                "tag": "lark_md"
                            }
                        },
                        {
                            "text": {
                                "content": f'✅ 通过数量：{results["Passed"]}\n',
                                "tag": "lark_md"
                            }
                        },
                        {
                            "text": {
                                "content": f'❌ 失败数量：{results["Failed"]}\n',
                                "tag": "lark_md"
                            }
                        },
                        {
                            "text": {
                                "content": f'✴️ 中断数量：{results["Broken"]}\n',
                                "tag": "lark_md"
                            }
                        },
                        {
                            "text": {
                                "content": f'🤔 覆盖率低于阈值的数量：{results["Coverage"]}\n',
                                "tag": "lark_md"
                            }
                        },
                    ],
                    "tag": "div"
                },
                {
                    "tag": "div",
                    "text": {
                        "content": "[查看Allure测试报告](http://192.168.5.163:8080/job/abferry_allure/allure/)",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "div",
                    "text": {
                        "content": "<at id=all></at> ",
                        "tag": "lark_md"
                    },

                },
            ],
            "header": {
                "template": "blue",
                "title": {
                    "content": "ABFerry自动化测试",
                    "tag": "plain_text"
                }
            }
        }
    }

    resp = requests.post(url=web_hook, json=message_body, headers=header)

    opener = resp.json()
    if opener["StatusMessage"] == "success":
        print(u"%s 通知消息发送成功！" % opener)
    else:
        print(u"通知消息发送失败，原因：{}".format(opener))


if __name__ == '__main__':
    config = Config.get_yaml("local_tc/lark.yaml")

    timestamp = int(datetime.now().timestamp())
    sign = gen_sign(timestamp, config["WEBHOOK_SECRET"])

    results = Allure_Results.count_allure_results(config["ALLURE_RESULTS"])

    print(results)
    push_report(config["WEBHOOK"], timestamp, sign, results)
