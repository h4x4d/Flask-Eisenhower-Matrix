import requests

files = {'file': open('test.txt', 'rb')}

print(requests.post('http://192.168.1.44:5000/api/tasks',
                    files=files,
                    headers={'token': '123'},
                    data={
                        'name': 'pupa',
                        'is_important': True,

                    }).text)
