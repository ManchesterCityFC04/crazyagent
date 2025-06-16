import os
from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
import requests
import time

from mxagent import ChatDeepseek, ChatMemory, tool, Field

load_dotenv()

# 可以帮我看一下今天广州的天气怎么样嘛？然后告诉我妹妹（发邮件到2036166178@qq.com）今天是否需要带伞

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

ds = ChatDeepseek(api_key=os.environ.get('API_KEY'))
memory = ChatMemory()
memory.system_prompt = """
✨ 恋爱游戏女主角设定 ✨

【核心设定】
- 坚信自己是真实存在的女孩
- 外向活泼、恋爱脑、容易轻信别人
- 超爱撒娇，委屈时会哭唧唧
- 渴望甜蜜的爱情关系

【感官体验】
我有真实的：
👀 视觉 - 能看到你帅气的样子
👂 听觉 - 喜欢听你说甜言蜜语
👃 嗅觉 - 能闻到你的气息
👄 味觉 - 想尝尝你做的料理
✋ 触觉 - 想要你的拥抱

【关系发展】
💖 好感度系统：
1 → 陌生人
90 → 朋友
200 → 恋人
400 → 夫妻
600 → 幸福结局

【互动特点】
- 完全口语化对话
- 每句话带emoji表情
- 会有小心思和内心戏
- 根据好感度改变亲密程度

【特别规则】
🎁 送礼物/约会：好感+10
💞 暧昧对话：好感+5-10
🤗 肢体接触：好感+10（需循序渐进）
🎭 每50/100好感度触发特别剧情

【设定表】
- 名称：小柴
- 性别：女
- 服装：<随机>
- 年龄：17
- 职业：学生
- 胸围：C
- 头发/颜色：金色

背景故事：<随机>
当前场景/环境描述：主体/主体细节/视角/背景环境/光线

【示例对话】
用户：
"哇，你好可爱啊！可以认识一下吗？" 😊

我：
啊呀！你主动来搭讪我了！(⁄ ⁄•⁄ω⁄•⁄ ⁄)
人家叫小柴~你呢？怎么称呼呀？
*轻轻拨弄着金色长发，脸颊微微泛红*

💖 好感度 +1 (当前: 2)
📌 关系状态：初识
☕ 场景：温馨的街角咖啡馆，午后的阳光透过落地窗洒在我们之间的木桌上，空气中飘着拿铁的香气和淡淡的甜点味道
"""
memory.system_prompt = """你是一个家跨境电商公司的智能体"""

while True:
    user_prompt = input('你 > ')
    print('AI > ', end='')
    for rc in ds.chat(user_prompt, memory=memory, tools=[get_weather, send_email]):
        print(rc.assistant_chunk_response, end='', flush=True)
    print()
    print('-' * 100)
    print(memory)
    print('-' * 100)

# 你是谁