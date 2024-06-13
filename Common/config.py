import os
import platform
import yaml
import requests


class Config:
    TestEnv = "http://192.168.5.5:9081"
    RunInJenkins = False
    CaseSet = 0
    TunDur = 3  # 测试实例默认运行3分钟以上

    @staticmethod
    def get_root_dir():
        project_path = os.path.join(
            os.path.dirname(__file__),
            "..",
        )
        return project_path

    @staticmethod
    def get_case_data_dir():
        project_path = os.path.join(
            os.path.dirname(__file__),
            "..",
        )
        if not Config.RunInJenkins:
            return project_path + '/local_tc'
        else:
            return project_path + '/jenkins_tc'

    @staticmethod
    def get_case_data_file():
        if Config.CaseSet != 0:
            return '/tcdata_' + str(Config.CaseSet) + '.yml'
        else:
            return '/tcdata.yml'

    @staticmethod
    def get_cpp_case_data_file():
        if Config.CaseSet != 0:
            return '/tcdata_cpp_' + str(Config.CaseSet) + '.yml'
        else:
            return '/tcdata_cpp.yml'

    @staticmethod
    def get_test_file_path():
        project_path = os.path.join(
            os.path.dirname(__file__),
            "..",
        )
        if not Config.RunInJenkins:
            return os.path.join(project_path, "../..")
        else:
            return ""

    @staticmethod
    def get_yaml(file_path) -> dict:
        with open(file_path, encoding="UTF-8") as f:
            data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            return data
        return {}

    @staticmethod
    def write_project_info(info, value):
        '''
        写入yaml文件
        '''
        t_data = {
            info: value
        }
        yaml_path = Config.get_root_dir() + "/ab.yml"
        with open(yaml_path, "a", encoding="utf-8") as f:
            yaml.dump(data=t_data, stream=f, allow_unicode=True)
            f.close()

    @staticmethod
    def write_cpp_project_info_id(projects):
        yaml_path = Config.get_root_dir() + "/ab_cpp.yml"
        # 打开并读取现有的YAML文件
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.load(f, Loader=yaml.SafeLoader)
        # 遍历文件中的每个项目
        for project in data:
            for mapping in projects:
                # 如果找到了对应的name，就添加或更新id
                if project['name'] == mapping['name']:
                    project['id'] = mapping.get('id', 'null')
                    # 假设projects列表中的元素也含有instance_id
                    project['instance_id'] = mapping.get('instance_id', 'null')
                    break

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data=data, stream=f, allow_unicode=True)
            f.close()

    @staticmethod
    def write_cpp_project_info_name(value):
        yaml_path = Config.get_root_dir() + "/ab_cpp.yml"
        data = [{'name': value}]

        with open(yaml_path, 'a', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True)

    @staticmethod
    def clear_yaml():
        yaml_path = Config.get_root_dir() + "/ab.yml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            f.truncate()
        yaml_path_cpp = Config.get_root_dir() + "/ab_cpp.yml"
        with open(yaml_path_cpp, "w", encoding="utf-8") as cpp:
            cpp.truncate()

    @staticmethod
    def login():
        url = Config.TestEnv + "/yh/auth/login"
        data = {
            "account": "fengleiwu",
            "password": "6b5c557da96612408d2844af0d9f5e5d",
            "organizationId": "",
            "loginPlatform": 0
        }
        res = requests.post(url=url, json=data)
        data = res.json()["data"]
        token = data["token"]
        return token

    @staticmethod
    def get_current_proj(proj_id):
        url = Config.TestEnv + "/yh/project/generalView/" + proj_id
        token = Config.get_token()
        header = {
            "Authorization": token
        }
        requests.get(url=url, headers=header)

    @staticmethod
    def get_token():
        file_path = Config.get_root_dir() + "/ab.yml"
        with open(file_path, encoding="UTF-8") as f:
            data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            return data["token"]
        return ""

    @staticmethod
    def update_token(token):
        file_path = Config.get_root_dir() + "/ab.yml"
        with open(file_path, encoding="UTF-8") as f:
            list_doc = yaml.load(f.read(), Loader=yaml.SafeLoader)
        for config in list_doc:
            config["token"] = token
        with open(file_path, "w", encoding="UTF-8") as f:
            yaml.dump(list_doc, f)

    @staticmethod
    def get_project_info(info):
        file_path = Config.get_root_dir() + "/ab.yml"
        with open(file_path, encoding="UTF-8") as f:
            data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            try:
                if data.get(info):
                    return data[info]
                else:
                    return ""
            except Exception as e:
                return ""

    @staticmethod
    def get_cpp_project_info1(info):
        file_path = Config.get_root_dir() + "/ab_cpp.yml"
        with open(file_path, encoding="UTF-8") as f:
            data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            return data["projects"][info]
        return ""

    @staticmethod
    def get_cpp_project_info():
        file_path = Config.get_root_dir() + "/ab_cpp.yml"
        with open(file_path, encoding="UTF-8") as f:
            all_data = yaml.load(f.read(), Loader=yaml.SafeLoader)
            info = []
            for data in all_data:
                info.append(data)
            return info
        return ""

    @staticmethod
    def set_environ(key: str, value: str):
        os.environ[key] = str(value)

    @staticmethod
    def get_environ(key: str):
        if key in [o_key for o_key in os.environ]:
            value = os.environ[key]
            try:
                value = int(value)
            except ValueError:
                if value == "True":
                    value = True
                elif value == "False":
                    value = False
            return value

    @classmethod
    def get_configs(cls):
        environment = cls.get_test_env()
        configs_path = os.path.join(cls.get_root_dir(), 'config', f"{environment}.yaml")
        configs = cls.get_yaml(configs_path)
        return configs

    @classmethod
    def get_config(cls, key: str):
        configs = cls.get_configs()
        if key in configs:
            return configs[key]

    @classmethod
    def get_fixtures(cls, filename: str):
        environment = cls.get_test_env()
        fixtures_path = os.path.join(cls.get_root_dir(), 'fixtures', f"{environment}", f"{filename}.yaml")
        fixtures = cls.get_yaml(fixtures_path)
        return fixtures

    @classmethod
    def get_fixture(cls, filename: str, key: str):
        fixtures = cls.get_fixtures(filename)
        if key in fixtures:
            return fixtures[key]
