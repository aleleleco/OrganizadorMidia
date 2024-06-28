import json

'C:\projetos_python\modelo.json'

with open('C:\projetos_python\modelo.json') as file:
    data = json.load(file)

print(data)