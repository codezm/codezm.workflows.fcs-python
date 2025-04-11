import json
import re
import sys
import os
from BaseServer import BaseServer

# 环境变量
separator = os.environ.get("separator", " | ")
dataFileName = os.environ.get("SSH_DATA_FILE_NAME", "data/ssh-data.json")

class Server(BaseServer):
    data = []
    workFlowPath = os.getcwd().replace(" ", "\\ ")
    args = []
    subtitle = {
        'operate': 'Tips: <Enter> to use!',
        'addTip': 'Download or Upload file by server'
    }
    queryList = []

    def __init__(self, serverDataFile):
        super().__init__(serverDataFile)
        self.data = self.getJsonDataByFile()
        self.args = [
            f"/usr/bin/expect {self.workFlowPath}/login.expect",
        ]

    def run(self, methodName, *args, **kwargs):
        method = getattr(self, methodName, None)
        if method and callable(method):
            result = method(*args, **kwargs)
            print(result, end='')
        else:
            raise AttributeError(f"Method {methodName} not found")

    def execute(self, keyword):
        commands = keyword.split(">>>")
        paths = commands[2].split(" ")
        localPath = paths.pop()
        remotePath = " ".join(paths)
        servers = [i for i in self.data if i['name'] == commands[0]]

        # Get the first item
        item = servers[0]
        if 'ssh' in item['host']:
            pattern = r"""
                ^ssh\s+                              # 起始部分
                (?:-i\s+(?P<keyfile>"[^"]+"|\S+)\s+)?  # 可选的密钥文件路径
                (?:                                  # 用户名和主机部分（整体可选）
                    (?P<user>[^@\s]+)@               # 用户名（捕获组）
                    (?P<host>[^\s:]+)                # 主机地址
                    |                                # 或
                    (?P<host_only>[^\s:]+)           # 仅主机地址（无用户名）
                )
                (?::(?P<port>\d+))?                  # 可选的端口号
                \s*$                                 # 忽略末尾空格
            """
            regex = re.compile(pattern, re.VERBOSE)
            match = regex.search(item['host'].strip())  # 去除首尾空格
            host = match.group("host") or match.group("host_only")

            if match.group("user"):
                host = match.group("user") + "@" + host
            if match.group("keyfile"):
                host = f"-i {match.group('keyfile')} {host}"
            if match.group("port"):
                host = f"-P {match.group('port')} {host}"
            if commands[1] == "Download":
                self.args.append(f"'scp {host}:{remotePath} {localPath}'")
            elif commands[1] == "Upload":
                self.args.append(f"'scp {localPath} {host}:{remotePath}'")
        else:
            if commands[1] == "Download":
                self.args.append(f"'scp {item['username']}@{item['host']}:{remotePath} {localPath}'")
            elif commands[1] == "Upload":
                self.args.append(f"'scp {localPath} {item['username']}@{item['host']}:{remotePath}'")
            self.args.append(self.toBase64Str(item['userpwd']))

        return " ".join(self.args)

    def get(self, keyword):
        queryList = []
        if ">>>" in keyword:
            if "Download>>>" in keyword:
                args = []
                queryList.append({
                    'uid' : 1,
                    'arg' : keyword,
                    'title' : 'Input server file path and local download path',
                    'subtitle' : 'Example: /etc/passwd Downloads (Default mapped to /Users/codezm/Downloads/)',
                    'valid' : True,
                    'autocomplete' : ''
                })
            elif "Upload>>>" in keyword:
                args = []
                queryList.append({
                    'uid' : 1,
                    'arg' : keyword,
                    'title' : 'Input server saves the directory and local upload file path',
                    'subtitle' : 'Example: /tmp notes.txt',
                    'valid' : True,
                    'autocomplete' : ''
                })
            else:
                queryList = queryList + [
                    {
                        'uid': 0,
                        'title': 'Download',
                        'subtitle': 'Download server file to local',
                        'valid': False,
                        'autocomplete': keyword + 'Download>>>',
                        'icon' : {
                            'path': 'icon.png'
                        }
                    },
                    {
                        'uid': 1,
                        'title': 'Upload',
                        'subtitle': 'Upload local file to server',
                        'valid': False,
                        'autocomplete': keyword + 'Upload>>>',
                        'icon' : {
                            'path': 'icon.png'
                        }
                    },
                ]
        else:
            for (key, item) in enumerate(self.data):
                if 'name' not in item:
                    continue
                if keyword in item['name'] or keyword in item['host'] or ('username' in item and keyword in item['username']):
                    title = [item['name']]
                    if 'username' in item:
                        title.append(f"{item['username']}@{item['host']}")
                    else:
                        title.append(f"{item['host']}")

                    queryList.append({
                        'uid': key,
                        'arg': key,
                        'title' : separator.join(title),
                        'subtitle' : self.subtitle['operate'],
                        'valid' : False,
                        'autocomplete': item['name'] + '>>>',
                        'icon' : {
                            'path': 'icon.png'
                        },
                    })

        if len(queryList) == 0:
            item = {
                'uid': 'codezm',
                'arg': keyword,
                'title': 'Download or Upload by scp!',
                'subtitle': self.subtitle['addTip'],
                'valid': False,
            }
            queryList.append(item)
        return json.dumps({ 'items': queryList })

# 获取命令行参数
args = sys.argv

Server(dataFileName).run(args[1], args[2])
exit()
