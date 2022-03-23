import requests

header = {
    'token': 'wdhpw2b1b3bwhvdk0ncsege5eugq00'
}

print(requests.get('http://192.168.1.44:5000/api/tasks', headers=header).text)