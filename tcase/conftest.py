import os
import requests
import pytest
import yaml
import time
from Common.config import Config


# @pytest.fixture()
# def lark_bot():
#     print("进行自动化测试...")
#     yield
#     time.sleep(10) # 等待生成Allure Result
#     path_dir = "Common/lark_utils.py"
#     os.system(f"python {path_dir}")





def write_yaml(token):
    '''
    写入yaml文件
    '''
    t_data = {
        "token": token
    }
    token_path = Config.get_root_dir() + "/ab.yml"
    if Config.get_project_info("token"):
        with open(token_path) as f:
            dict_temp = yaml.load(f, Loader=yaml.FullLoader)
            dict_temp["token"] = token
        with open(token_path, "w", encoding="utf-8") as f:
            yaml.dump(dict_temp, stream=f, allow_unicode=True)
            f.close()
    else:
        with open(token_path, "w", encoding="utf-8") as f:
            yaml.dump(data=t_data, stream=f, allow_unicode=True)
            f.close()

