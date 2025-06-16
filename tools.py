import inspect
from enum import Enum
from collections import defaultdict
from functools import wraps
import time
from pydantic_core._pydantic_core import PydanticUndefinedType
from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic import Field
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import requests

TOOL_TYPE_MAP = {
    "str": "string",
    "int": "number",
    "float": "number",
    "list": "array",
    "dict": "object",
    "bool": "boolean",
    # 不允许出现 tuple、set、bytes ...
}

def tool(func: callable) -> callable:
    """
    装饰器, 提取函数的信息, 添加 tool_definition 属性. 
    捕获函数执行过程中的异常, 并以 dict 的形式返回失败信息.
    """
    properties = defaultdict(dict)
    required = []

    for _, param in inspect.signature(func).parameters.items():
        # _ 是参数的名称, 与 param.name 一样
        # param 是参数对象, 封装了该参数的一些信息
        # param.annotation 是参数的注释, 即参数的类型, 例如 <class 'int'>、<class 'str'>
        # param.anaotation.__name__ 是参数的类型的字符串表示, 例如 'int'、'str'
        p_type = param.annotation
        if issubclass(param.annotation, Enum):
            properties[param.name]["enum"] = [member.value for member in p_type]
        else:
            if p_type.__name__ not in TOOL_TYPE_MAP:
                raise ValueError(f"不支持的参数类型: {p_type.__name__}")
            properties[param.name]["type"] = TOOL_TYPE_MAP[p_type.__name__]

        field: FieldInfo = param.default
        if not isinstance(field, FieldInfo):
            raise ValueError(f"参数 {param.name} 的默认值必须使用 Field 进行注释")

        properties[param.name]["description"] = field.description
        if isinstance(field.default, PydanticUndefinedType):
            required.append(param.name)
        else:
            properties[param.name]["default"] = field.default

    tool_definition = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__,
            "parameters": {"type": "object", "properties": dict(properties)},
            "required": required,
        }
    }
    
    @wraps(func)
    def wrap(*args, **kwargs):
        try:
            return {'status': 'success', 'result': func(*args, **kwargs)}
        except Exception as e:
            return {'status': 'fail', 'detail': str(e)}
    
    wrap.tool_definition = tool_definition
    return wrap

@tool
def get_weather(city_name: str = Field(..., description='城市名称')) -> dict:
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

@tool
def send_email(
    subject: str = Field(..., description='邮件标题'), 
    addressee: str = Field(..., description='收件人邮箱地址, 例如："2036166178@qq.com". 一定要让用户提供收件人邮箱地址, 否则拒绝发送邮件'), 
    text: str = Field(..., description='邮件正文内容')
) -> str:
    """发送邮件"""
    sender_mail = '17675618762@163.com'
    sender_name = 'Agent'
    authorization_code = 'VNQSWBXVWRYIULHF'
    server = 'smtp.163.com'
    
    # 使用MIMEText创建电子邮件内容，指定内容类型为HTML和字符编码为UTF-8
    msg = MIMEText(text, "plain", "utf-8")
    # 设置电子邮件主题
    msg['Subject'] = subject
    # 设置发件人信息，包括发件人名字和邮箱地址
    msg["From"] = formataddr((sender_name, sender_mail))
    # 设置收件人邮箱地址
    msg['To'] = addressee
    with smtplib.SMTP_SSL(server) as server:
        server.login(sender_mail, authorization_code)
        server.sendmail(sender_mail, addressee, msg.as_string())
    return f'email is sent to {addressee}'