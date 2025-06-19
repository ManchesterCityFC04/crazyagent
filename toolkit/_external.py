from .core import crazy_tool, Argument, default_argument
from crazy_agent.utils import HEADERS

import requests
import time

@crazy_tool
def get_weather(city_name: str = Argument('City name, e.g., "Guangzhou". If city name is not specified, refuse to provide weather information.')) -> dict | str:
    """
    Get weather information for a given city.
    Data source: China Meteorological Administration (https://weather.cma.cn/).

    Args:
        city_name: City name, e.g., "Guangzhou". If city name is not specified, refuse to provide weather information.

    Returns:
        Weather information dictionary if city is found, otherwise a string indicating city not found.
    """
    session = requests.session()
    session.headers.update(HEADERS)
    
    url = 'https://weather.cma.cn/api/autocomplete'
    params = {
        'q': city_name,
        'limit': 1,
        'timestamp': time.time()
    }
    data = session.get(url=url, params=params).json()
    if not data['data']:
        return 'city not found'
    
    city_code = data['data'][0].split('|')[0]
    url = f'https://weather.cma.cn/api/now/{city_code}'
    data = session.get(url=url).json()
    return data

@crazy_tool
def search_image(query: str = Argument('Search keyword'), page: int = Argument('Page number', default=1)) -> list[str]:
    """
    Search for images based on the provided query.    
    Data source: https://www.duitang.com/
    
    Args:
        query: Search keyword
        page: Page number (default: 1)
        
    Returns:
        List of image URLs
    """
    default_argument(page)

    url = 'https://www.duitang.com/napi/blogv2/list/by_search/'
    params = {
        'kw': query,
        'after_id': 24 * page,
        'type': 'feed',
        '_': (time.time() * 1000)
    }
    data = requests.get(url=url, params=params, headers=HEADERS).json()
    url_list = []
    for i in data['data']['object_list']:
        url = i['photo']['path']
        url_list.append(url)
    return url_list
