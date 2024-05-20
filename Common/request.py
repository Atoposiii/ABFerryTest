import requests
import json
import logging
import traceback
import allure


class Request():
    def __init__(self, cookies: requests.cookies.RequestsCookieJar = None, user: dict = None):
        self.method = "POST"
        self.url = None
        self.host = None
        self.path = None
        self.headers = {
            "content-type": "application/json; charset=utf-8"
        }
        self.cookies = cookies if cookies or not user else self.__login_and_get_cookies(user) # cookies 优先
        self.params = {}
        self.data = {}
        self.response = None


    def request(self):
        @allure.step(f"请求 {self.path}")
        def __request_and_get_response(info:dict = self.__dict__) -> requests.models.Response: # 不需要传入参数，纯粹为了 allure 报告好看
            return s.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                params=self.params,
                data=json.dumps(self.data),
                cookies=self.cookies,
                verify=False
            )

        requests.packages.urllib3.disable_warnings()
        requests.adapters.DEFAULT_RETRIES = 5

        self.url = self.url if self.url else self.host + self.path

        s = requests.session()
        s.keep_alive = False
        self.response = __request_and_get_response()

        self.__log()
        self.is_success = True if self.response.json()["json"]["code"] == 200 else False

        return self.response

    @allure.step("断言")
    def assertion(self, expect_code = None, expect_message = None):
        if self.response is None:
            raise Exception("请先请求接口~")

        assert self.response.status_code == 200, f"HTTP CODE {self.response.status_code}"

        if expect_code is not None:
            assert expect_code == self.response.json()["json"]["code"], f"code 不一致"

        if expect_message  is not None:
            assert expect_message in self.response.json()["json"]["message"], f"message 不一致"
