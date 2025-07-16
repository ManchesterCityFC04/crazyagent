from .core import crazy_tool, Argument
from crazyagent.utils import is_valid_email

from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib

# ----------------------------------------------------

_email_config = None

def configure_email_service(sender_mail: str, authorization_code: str, server: str):
    """Configure email service settings.

    Args:
        sender_mail: Sender's email address.
        authorization_code: Email authorization code.
        server: Email server address.
    """
    global _email_config
    _email_config = {
        'sender_mail': sender_mail,
        'authorization_code': authorization_code,
        'server': server
    }

@crazy_tool
def send_email(
    subject: str = Argument(description='Email subject'), 
    sender_name: str = Argument(description='Sender name, e.g., "Crazy Agent".'),
    addressee: str = Argument(description='Recipient email address, e.g., "example@qq.com". If not specified, the email will not be sent.'), 
    text: str = Argument(description='Email body content')
) -> str:
    """
    Send an email.

    Returns:
        str: A message indicating whether the email is sent successfully.
    """
    if _email_config is None:
        raise ValueError('Please configure the email service first using configure_email_service function')

    if not is_valid_email(addressee):
        raise ValueError(f'Email address {addressee} is invalid')

    sender_mail = _email_config['sender_mail']
    authorization_code = _email_config['authorization_code']
    server = _email_config['server']
    # Create SMTP object
    smtp = smtplib.SMTP_SSL(server)
    # Login to email account
    smtp.login(sender_mail, authorization_code)

    # Create email content using MIMEText, specify content type as plain text and encoding as UTF-8
    msg = MIMEText(text, "plain", "utf-8")
    # Set email subject
    msg['Subject'] = subject
    # Set sender information, including sender name and email address
    msg["From"] = formataddr((sender_name, sender_mail))
    # Set recipient email address
    msg['To'] = addressee
    with smtplib.SMTP_SSL(server) as server:
        server.login(sender_mail, authorization_code)
        server.sendmail(sender_mail, addressee, msg.as_string())
    return f'email is sent to {addressee}'