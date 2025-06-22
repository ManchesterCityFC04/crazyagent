from .core import crazy_tool, Argument
from crazyagent.utils import is_valid_email, HEADERS

import os
import uuid

from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import aiosmtplib

import requests

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

@crazy_tool(is_async=False)
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

@crazy_tool(is_async=True)
async def async_send_email(
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
    
    # Create email content using MIMEText, specify content type as plain text and encoding as UTF-8
    msg = MIMEText(text, "plain", "utf-8")
    # Set email subject
    msg['Subject'] = subject
    # Set sender information, including sender name and email address
    msg["From"] = formataddr((sender_name, sender_mail))
    # Set recipient email address
    msg['To'] = addressee
    
    # Use aiosmtplib for async email sending
    smtp = aiosmtplib.SMTP(hostname=server, use_tls=True)
    await smtp.connect()
    await smtp.login(sender_mail, authorization_code)
    await smtp.send_message(msg)
    await smtp.quit()
    
    return f'email is sent to {addressee}'

# ----------------------------------------------------

_save_dir = None

def configure_save_dir(save_dir: str):
    """Configure the directory where files will be saved.

    Args:
        save_dir: Directory where files will be saved.

    Raises:
        ValueError: If the path is not absolute or does not exist.
    """
    global _save_dir
    if not os.path.isabs(save_dir):
        raise ValueError("The save_dir must be an absolute path.")
    if not os.path.isdir(save_dir):
        raise ValueError(f"The directory '{save_dir}' does not exist.")
    _save_dir = save_dir

@crazy_tool(is_async=False)
def fetch_and_save(
    url_file_pairs: list = Argument(description="""\
A list of URL and filename pairs, where each pair is a list containing two elements: the URL and the filename.
Example:
```python
    [
        ['http://example.com/image.jpg', 'image1.jpg'],
        ['http://example.com/image2.jpg', 'image2.jpg'],
        ['http://example.com/image3.jpg', 'image3.jpg']
    ]
```
""")
) -> str:
    """
    Fetch and save files from a list of URL and filename pairs.

    Returns:
        A message indicating the location of the saved files.
    """
    if _save_dir is None:
        raise ValueError('Please configure the save_dir first using configure_save_dir function')

    temp_dir = os.path.join(_save_dir, str(uuid.uuid4().hex))
    os.makedirs(temp_dir, exist_ok=True)
    os.startfile(temp_dir)

    for url, filename in url_file_pairs:
        response = requests.get(url, headers=HEADERS)
        with open(os.path.join(temp_dir, filename), 'wb') as f:
            f.write(response.content)

    return f'Files are saved to {temp_dir}'