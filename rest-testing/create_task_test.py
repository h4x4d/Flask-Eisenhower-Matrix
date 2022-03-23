import requests
from token_header import header

files = {'file': open('test.txt', 'rb')}

print(requests.post('http://flask-eisenhower-matrix.herokuapp.com/api/tasks',
                    files=files,
                    headers=header,
                    data={
                        'name': 'Test task',
                        'is_important': True,

                    }).json())
