import json
import re
import sys
import os
from BaseServer import BaseServer
import subprocess

# 环境变量
os.environ["PATH"] = "/usr/local/bin:/opt/homebrew/bin:" + os.environ.get("PATH", "")
separator = os.environ.get("separator", " | ")
sshDataFileName = os.environ.get("SSH_DATA_FILE_PATH", "data/ssh-data.json")
TMUX_SESSION_NAME = os.environ.get("TMUX_SESSION_NAME", "")

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

    def has_tab_with_session_name(self, name_fragment):
        """检查是否有标签页的会话名称包含指定字符串"""
        
        applescript = f'''
tell application "iTerm"
    if (count of windows) = 0 then
        return false
    end if
    
    repeat with w in windows
        tell w
            repeat with aTab in tabs
                try
                    if (name of current session of aTab) contains "{name_fragment}" then
                        return true
                    end if
                on error
                    -- 忽略错误
                end try
            end repeat
        end tell
    end repeat
    
    return false
end tell
'''
        
        try:
            result = subprocess.run(['osascript', '-e', applescript],
                                capture_output=True, text=True, timeout=5)
            output = result.stdout.strip().lower()
            return output == "true"
        except Exception as e:
            return False

    def run(self, methodName, *args, **kwargs):
        method = getattr(self, methodName, None)
        if method and callable(method):
            name, result = method(*args, **kwargs)
            if TMUX_SESSION_NAME and (methodName == "getByIndex" or methodName == "add"):
                name = name.replace(".", "_")
                # check tmux session exist
                session_check = subprocess.run(["tmux", "has-session", "-t", TMUX_SESSION_NAME], capture_output=True)
                if session_check.returncode != 0:
                    # create tmux session
                    subprocess.run(["tmux", "new-session", "-d", "-s", TMUX_SESSION_NAME])
                # check tmux window exist
                window_check = subprocess.run(["tmux", "list-windows", "-t", TMUX_SESSION_NAME, "-F", "#{window_name}"], capture_output=True, text=True)
                if name not in window_check.stdout.splitlines():
                    if self.has_tab_with_session_name(TMUX_SESSION_NAME):
                        print(f"tmux new-window -t {TMUX_SESSION_NAME} -n \"{name}\" && tmux send-keys -t {TMUX_SESSION_NAME}:{name} \"{result}\" Enter && osascript -e 'tell application \"iTerm\" to tell current window to tell current tab to close' && osascript -e 'tell application \"iTerm\"' -e 'tell current window' -e 'repeat with aTab in tabs' -e 'tell aTab' -e 'if (name of current session) contains \"{TMUX_SESSION_NAME}\" then' -e 'select aTab' -e 'exit repeat' -e 'end if' -e 'end tell' -e 'end repeat' -e 'end tell' -e 'end tell'", end='')
                    else:
                        print(f"tmux new-window -t {TMUX_SESSION_NAME} -n \"{name}\" && tmux send-keys -t {TMUX_SESSION_NAME}:{name} \"{result}\" Enter && tmux attach -t {TMUX_SESSION_NAME}", end='')
                else:
                    print(result, end='')
            else:
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

            return "", "\n".join(output)
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

            return "", "\n".join(output)
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

        return item['name'], " ".join(self.args)

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
        return "", json.dumps({ 'items': queryList })

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

            return item['name'], " ".join(self.args)
        except IndexError:
            return 'Execute Failed! Server may be remove!'

# 获取命令行参数
args = sys.argv

if args[1] == "add" and "add" not in args[2]:
    args[1] = 'getByIndex'

sshServer(sshDataFileName).run(args[1],  args[2])
exit()
