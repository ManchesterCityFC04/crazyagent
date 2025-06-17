from . import agent_tool, Argument

import requests
import time

@agent_tool
def get_weather(city_name: str = Argument(description='城市名称', enum=['北京', '上海', '广州', '深圳'])) -> dict:
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

from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib

@agent_tool
def send_email(
    subject: str = Argument(description='邮件标题'), 
    sender_name: str = Argument(description='发件人名称'),
    addressee: str = Argument(description='收件人邮箱地址, 例如: "2036166178@qq.com"'), 
    text: str = Argument(description='邮件正文内容')
) -> str:
    """发送邮件"""
    sender_mail = '17675618762@163.com'
    authorization_code = 'VNQSWBXVWRYIULHF'
    server = 'smtp.163.com'
    # 创建SMTP对象
    smtp = smtplib.SMTP_SSL(server)
    # 登录邮箱
    smtp.login(sender_mail, authorization_code)

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