import os

from prompts import LOVE_GAME
from tools import get_weather, send_email
from core import ChatDeepseek, ChatMemory

ds = ChatDeepseek(api_key='sk-1537300d758f4a848446175ec44c72d3')
memory = ChatMemory()
memory.system_prompt = LOVE_GAME

while True:
    user_prompt = input('你 > ')
    print('AI > ', end='')
    for rc in ds.chat(user_prompt, memory=memory, tools=[get_weather, send_email]):
        print(rc.assistant_chunk_response, end='', flush=True)
    print()
    print('-' * 100)
    print(memory)
    print('-' * 100)

# "模块化（核心、提示词、工具、辅助函数）"