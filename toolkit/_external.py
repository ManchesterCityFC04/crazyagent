from .core import agent_tool, Argument

import requests
import time

@agent_tool
def get_weather(city_name: str = Argument(description='城市名称', enum=['北京', '上海'])) -> dict:
    """获取天气"""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0'}
    session = requests.session()
    session.headers.update(headers)
    
    url = 'https://weather.cma.cn/api/autocomplete'
    params = {
        'q': city_name,
        'limit': 1,
        'timestamp': time.time()
    }
    data = session.get(url=url, params=params).json()
    if not data['data']:
        return {'status': 'fail', 'detail': 'city not found'}
    
    city_code = data['data'][0].split('|')[0]
    url = f'https://weather.cma.cn/api/now/{city_code}'
    data = session.get(url=url).json()
    return data