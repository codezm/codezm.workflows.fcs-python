import json
import re
import sys
import os
from BaseServer import BaseServer

# 环境变量
separator = os.environ.get("separator", " | ")
sshDataFileName = os.environ.get("SSH_DATA_FILE_NAME", "data/ssh-data.json")

class sshServer(BaseServer):
    data = []
    workFlowPath = os.getcwd().replace(" ", "\\ ")
    args = []
    subtitle = {
        'operate': 'Tips: input <Enter> to use | <Shift> to delete | <Cmd> to copy!',
        'addTip': 'Please add data by this format: ssh add server-name ip-addr uname pwd [root-pwd]'
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

    def delete(self, keywordIndex):
        keywordIndex = int(keywordIndex)
        try:
            item = self.data[keywordIndex]
            del self.data[keywordIndex]

            # sort
            self.data = sorted(self.data, key=lambda x: x['name'])
            # save
            self.setJsonDataByFile(self.data)

            output = [
                item['name'],
                item['host'],
            ]
            if 'username' in item:
                output.append(item['username'])
                if 'userpwd' in item:
                    output.append(item['userpwd'])
                if 'rootpwd' in item:
                    output.append(item['rootpwd'])

            return "\n".join(output)
        except IndexError:
            return 'Delete Failed! Server may be remove!'

    def copy(self, keywordIndex):
        keywordIndex = int(keywordIndex)
        try:
            item = self.data[keywordIndex]
            output = [
                item['name'],
                item['host'],
            ]
            if 'username' in item:
                output.append(item['username'])
                if 'userpwd' in item:
                    output.append(item['userpwd'])
                if 'rootpwd' in item:
                    output.append(item['rootpwd'])

            return "\n".join(output)
        except IndexError:
            return 'Copy Failed! Server may be remove!'

    def add(self, info, addLabel="add"):
        info = info.split(addLabel)[1]
        serviceArr = info.strip().split(" ")
        item = {}
        if len(serviceArr) < 2:
            return False

        if "ssh" in info:
            item = {
                "name": serviceArr.pop(0),
            }

            item['host'] = " ".join(serviceArr)

        elif len(serviceArr) > 3:
            item = {
                "name": serviceArr[0],
                "host": serviceArr[1],
                "username": serviceArr[2],
                "userpwd": serviceArr[3],
            }
            if len(serviceArr) > 4:
                item['rootpwd'] = serviceArr[4]
        elif len(serviceArr) == 3:
            item = {
                "name": serviceArr[0],
                "host": serviceArr[1],
                "username": "root",
                "userpwd": serviceArr[2],
            }
        else:
            item = {
                "name": serviceArr[0],
                "host": serviceArr[1],
            }
        self.data.append(item)

        # sort
        self.data = sorted(self.data, key=lambda x: x['name'])
        # save
        self.setJsonDataByFile(self.data)

        if 'username' in item:
            self.args.append(f"'ssh {item['username']}@{item['host']} -o ServerAliveInterval=30'")
            if 'userpwd' in item:
                item['userpwd'] = self.toBase64Str(item['userpwd'])
                self.args.append(item['userpwd'])
            if 'rootpwd' in item:
                item['rootpwd'] = self.toBase64Str(item['rootpwd'])
                self.args.append(item['rootpwd'])
        else:
            self.args.append(f"'{item['host']}'")

        return " ".join(self.args)

    def get(self, keyword):
        queryList = []
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
                    'valid' : True,
                    'icon' : {
                        'path': 'icon.png'
                    },
                })

        if len(queryList) == 0:
            item = {
                'uid': 'codezm',
                'arg': keyword,
                'title': 'Auto login by ssh - Tips: You haven\'t added any thing.',
                'subtitle': self.subtitle['addTip'],
                'valid': False,
            }
            if "add" in keyword:
                item['title'] = 'Input <enter> to save.'
                item['valid'] = True
            queryList.append(item)
        return json.dumps({ 'items': queryList })

    def getByIndex(self, keywordIndex):
        keywordIndex = int(keywordIndex)
        try:
            item = self.data[keywordIndex]
            if 'username' in item:
                self.args.append(f"'ssh {item['username']}@{item['host']} -o ServerAliveInterval=30'")
                if 'userpwd' in item:
                    item['userpwd'] = self.toBase64Str(item['userpwd'])
                    self.args.append(item['userpwd'])
                if 'rootpwd' in item:
                    item['rootpwd'] = self.toBase64Str(item['rootpwd'])
                    self.args.append(item['rootpwd'])
            else:
                self.args.append(f"'{item['host']}'")

            return " ".join(self.args)
        except IndexError:
            return 'Execute Failed! Server may be remove!'

# 获取命令行参数
args = sys.argv

if args[1] == "add" and "add" not in args[2]:
    args[1] = 'getByIndex'

sshServer(sshDataFileName).run(args[1],  args[2])
exit()
