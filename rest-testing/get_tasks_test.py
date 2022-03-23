import requests
from token_header import header

print(requests.get('http://flask-eisenhower-matrix.herokuapp.com/api/tasks',
                   headers=header).json())