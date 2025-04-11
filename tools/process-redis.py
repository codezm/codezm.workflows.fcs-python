import json
import re
import sys
import os

with open('../data/redis.json', 'r') as file:
    data = json.load(file)

serviceJson = []
for item in data:
    if "redis-cli " in item:
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
                "port": serviceArr[1],
                "db": serviceArr[2],
                "auth": serviceArr[3],
            })
with open('../data/redis-data.json', 'w') as file:
    serviceJson = sorted(serviceJson, key=lambda x: x['name'])
    json.dump(serviceJson, file, indent=4, ensure_ascii=False)
