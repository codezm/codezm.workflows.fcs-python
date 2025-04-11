import json
import re
import sys
import os

with open('../data/ssh.json', 'r') as file:
    data = json.load(file)

serviceJson = []
for item in data:
    if "ssh " in item:
        serviceArr = re.findall(r"(.*?) '(.*?)'", item)
        serviceJson.append({
            "name": serviceArr[0][0],
            "host": serviceArr[0][1],

        })
    else:
        serviceArr = item.split(" ")
        serviceName = serviceArr[0]
        del serviceArr[0]
        # name host user userpwd rootpwd
        if len(serviceArr) == 4:
            serviceJson.append({
                "name": serviceName,
                "host": serviceArr[0],
                "username": serviceArr[1],
                "userpwd": serviceArr[2],
                "rootpwd": serviceArr[3],
            })
with open('../data/ssh-data.json', 'w') as file:
    serviceJson = sorted(serviceJson, key=lambda x: x['name'])
    json.dump(serviceJson, file, indent=4, ensure_ascii=False)
