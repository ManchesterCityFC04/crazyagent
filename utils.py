import re 
from colorama import Fore, Style

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0',}

class CS:

    @staticmethod
    def red(string: str) -> str:
        return Fore.RED + string + Style.RESET_ALL
    
    @staticmethod
    def green(string: str) -> str:
        return Fore.GREEN + string + Style.RESET_ALL
    
    @staticmethod
    def purple(string: str) -> str:
        return Fore.MAGENTA + string + Style.RESET_ALL
    
    @staticmethod
    def yellow(string: str) -> str:
        return Fore.YELLOW + string + Style.RESET_ALL

    @staticmethod
    def blue(string: str) -> str:
        return Fore.LIGHTBLUE_EX + string + Style.RESET_ALL
    
def is_valid_email(email: str) -> bool:
    """
    验证邮箱地址是否有效
    
    参数:
        email: 需要验证的邮箱地址
        
    返回:
        bool: 邮箱有效返回 True，否则返回 False
    """
    if not isinstance(email, str):
        return False
        
    # 邮箱正则表达式模式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # 使用正则表达式匹配
    return bool(re.match(pattern, email))