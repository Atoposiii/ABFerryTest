import lark_oapi as lark
import requests
import json
from lark_oapi.api.sheets.v3 import *
from datetime import datetime
from Common.config import Config

# SDK 使用说明: https://github.com/larksuite/oapi-sdk-python#readme

def generate_report(report_data):
    config = Config.get_yaml("local_tc/lark.yaml")
    # 应用ID和密钥
    app_id = config["APP_ID"]
    app_secret = config["APP_SECRET"]
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 获取应用访问令牌
    app_access_token = get_app_access_token(app_id, app_secret)
    # 用户访问令牌
    user_access_token = "u-fR5Zg.ILxcsqLAPYLa5mVyhkkcYl4kDxg0w0klE00CtF"
    # 创建电子表格
    # create_sheet(app_id, app_secret)
    # 获取创建的表格token
    # spreadsheet_token = response.data.spreadsheet.spreadsheet_token
    # 获取工作表
    sheet_info = get_sheet(client=client)
    titles = [sheet['title'] for sheet in sheet_info]
    title = datetime.today().strftime('%Y-%m-%d')
    spreadsheet_token = config["SPREADSHEET_TOKEN"]
    # 如果sheet未创建，首先要创建
    sheet_id = None
    if title not in titles:
        sheet_id = sheets_update(spreadsheet_token, app_access_token, title)
    else:
        sheet_id = find_sheet_id_by_title(sheet_info, title)
    # 获取sheetId
    # sheet_id = get_sheet_id(spreadsheet_token, app_access_token)
    if not sheet_id:
        lark.logger.error("获取sheetId失败")
        return
    # 添加表头信息
    add_values_to_sheet(spreadsheet_token, app_access_token, f"{sheet_id}!A1:Q1",
                        [["用例名", "代码行", "函数个数", "gtest行覆盖",
                          "gtest函数覆盖", "fuzzer行覆盖", "fuzzer函数覆盖",
                          "gtest行覆盖率", "gtest函数覆盖率", "fuzzer行覆盖率", "fuzzer函数覆盖率",
                          "行覆盖提升率", "函数覆盖提升率", "bug总数", "bug类型", "用例bug数",
                          "源码bug数"]])
    # 添加数据信息
    append_to_sheet(spreadsheet_token, app_access_token, f"{sheet_id}!A1:Q1",
                    [report_data])

def find_sheet_id_by_title(sheets, title_to_find):
    # 遍历sheets列表
    for sheet in sheets:
        # 检查当前sheet的title是否与要查询的title匹配
        if sheet['title'] == title_to_find:
            # 如果匹配，返回对应的sheet_id
            return sheet['sheet_id']
    return None

def get_sheet(client):
    # 构造请求对象
    request: QuerySpreadsheetSheetRequest = QuerySpreadsheetSheetRequest.builder() \
        .spreadsheet_token("GCoLsuawvhPxfdtypTNcATEqnKd") \
        .build()

    # 发起请求
    response: QuerySpreadsheetSheetResponse = client.sheets.v3.spreadsheet_sheet.query(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.sheets.v3.spreadsheet_sheet.query failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    # lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    sheet_info = []
    for sheet in response.data.sheets:
        sheet_info.append(
            {
                "sheet_id": sheet.sheet_id,
                "title": sheet.title
            }
        )
    return sheet_info


def sheets_update(sheet_token, access_token, title):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{sheet_token}/sheets_batch_update"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": title,
                    }
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()['data']['replies'][0]['addSheet']['properties']['sheetId']


def create_sheet(app_id, app_secret, user_access_token):
    # 创建client
    client = lark.Client.builder() \
        .app_id(app_id) \
        .app_secret(app_secret) \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()
    # 构造请求对象，创建新的电子表格
    request = CreateSpreadsheetRequest.builder() \
        .request_body(Spreadsheet.builder()
                      .title("ABFerry Test Report")
                      .build()) \
        .build()
    option = lark.RequestOption.builder().user_access_token(user_access_token).build()
    response = client.sheets.v3.spreadsheet.create(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.sheets.v3.spreadsheet.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return


def get_sheet_id(spreadsheet_token, user_access_token):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo"
    headers = {
        "Authorization": f"Bearer {user_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200 or response.json().get("code") != 0:
        lark.logger.error(
            f"get_sheet_id failed, code: {response.json().get('code')}, msg: {response.json().get('msg')}")
        return None
    info = response.json()["data"]
    print(info)
    sheet_id = response.json()['data']['sheets'][0]['sheetId']
    lark.logger.info(f"获取的sheetId: {sheet_id}")
    return sheet_id


def add_values_to_sheet(spreadsheet_token, access_token, range_address, values):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "valueRange": {
            "range": range_address,
            "values": values
        }
    }
    response = requests.put(url, headers=headers, json=body)

    if response.status_code != 200 or response.json().get("code") != 0:
        lark.logger.error(
            f"add_values_to_sheet failed, code: {response.json().get('code')}, msg: {response.json().get('msg')}")
    else:
        lark.logger.info("表头创建成功")


def append_to_sheet(spreadsheet_token, access_token, range_address, values):
    url = f"https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/values_append"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "valueRange": {
            "range": range_address,
            "values": values
        }
    }
    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200 or response.json().get("code") != 0:
        lark.logger.error(
            f"add_values_to_sheet failed, code: {response.json().get('code')}, msg: {response.json().get('msg')}")
    else:
        lark.logger.info("数据添加成功")


def get_app_access_token(app_id, app_secret):
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "app_id": app_id,
        "app_secret": app_secret
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()['app_access_token']


def print_http_request_details(response):
    print("Status Code:", response.status_code)
    print("Headers:", json.dumps(dict(response.headers), indent=4))
    print("Response Body:", response.text)


if __name__ == "__main__":
    report_data = ['mini', 113, 10, 52, 6, 96, 9, '46.02%', '60.00%', '84.96%', '90.00%', '84.62%', '50.00%', 2,
                   'FPE, heap-use-after-free', 0, 2]

    generate_report(report_data)
