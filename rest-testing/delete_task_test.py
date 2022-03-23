import requests
from token_header import header

print(
    requests.delete('http://flask-eisenhower-matrix.herokuapp.com/api/tasks/1',
                    headers=header).json())
