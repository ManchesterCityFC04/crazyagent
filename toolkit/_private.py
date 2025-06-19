from .core import agent_tool, Argument
from crazy_agent.utils import is_valid_email

from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib

_email_config = {
    'sender_mail': '',
    'authorization_code': '',
    'server': ''
}

def configure_email_service(sender_mail: str, authorization_code: str, server: str):
    """设置邮箱配置
    Args:
        sender_mail : 发件人邮箱
        authorization_code : 邮箱授权码
        server : 邮箱服务器
    """
    _email_config['sender_mail'] = sender_mail
    _email_config['authorization_code'] = authorization_code
    _email_config['server'] = server

@agent_tool
def send_email(
    subject: str = Argument(description='邮件标题'), 
    sender_name: str = Argument(description='发件人名称'),
    addressee: str = Argument(description='收件人邮箱地址, 例如: "example@qq.com", 一定要让用户指定收件人邮箱地址, 否则就拒绝发送邮件'), 
    text: str = Argument(description='邮件正文内容')
) -> str:
    """发送邮件"""
    if not is_valid_email(addressee):
        raise ValueError(f'邮箱地址 {addressee} 格式不正确')

    sender_mail = _email_config['sender_mail']
    authorization_code = _email_config['authorization_code']
    server = _email_config['server']
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