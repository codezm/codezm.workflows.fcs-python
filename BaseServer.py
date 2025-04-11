import os
import json
import base64

class BaseServer:
    serverDataFile = ""

    def __init__(self, serverDataFile):
        self.serverDataFile = serverDataFile

    def setJsonDataByFile(self, data):
        with open(self.serverDataFile, 'w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def getJsonDataByFile(self):
        if os.path.exists(self.serverDataFile):
            with open(self.serverDataFile, 'r') as file:
                data = json.load(file)
                return data
        else:
            os.makedirs(os.path.dirname(self.serverDataFile), exist_ok=True)
            with open(self.serverDataFile, "w") as file:
                json.dump([], file, indent=4, ensure_ascii=False)
                return []

    def toBase64Str(self, dataStr):
        return base64.b64encode(dataStr.encode('utf-8')).decode('utf-8')

