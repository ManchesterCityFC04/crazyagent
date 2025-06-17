from .utils import CS
import json

class Memory:

    def __init__(self):
        # 消息列表(聊天记录)的最大长度, 必须是双数
        # 单数会出现 tool 找不到对应的 tool_calls 的情况
        self.k: int = 10  
        self.system_prompt: str = None  # 系统提示词
        self._messages: list[dict] = []  # 消息列表(聊天记录)

    def __str__(self):

        def cut(s: str, k: int = 50):
            if len(s) < k:
                return s
            else:
                return s[:k] + '...'

        lines = []
        for msg in self.get_messages():
            match msg['role']:
                case 'system':
                    lines.append(CS.red(f"[system] > {cut(msg['content'])}"))
                case 'user':
                    lines.append(CS.blue(f"[user] > {cut(msg['content'])}"))
                case 'assistant':
                    if 'tool_calls' in msg:
                        tool_call = msg['tool_calls'][0]
                        args = json.loads(tool_call['function']['arguments'])
                        lines.append(CS.yellow(f"[assistant] > {tool_call['function']['name']}({': '.join(f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in args.items())})"))
                    else:
                        lines.append(CS.purple(f"[assistant] > {cut(msg['content'])}"))
                case 'tool':
                    lines.append(CS.green(f"[tool] > {msg['content']}"))
        return '\n'.join(lines)

    def get_messages(self):
        """获取聊天信息, 用于对话"""
        m = self._messages
        if len(m) > self.k:
            m = self._messages[-self.k:]
        if self.system_prompt:
            m = [{'role': 'system', 'content': self.system_prompt}] + m
        return m

    def add_user_message(self, user_prompt: str):
        """添加用户消息"""
        self._messages.append({'role': 'user', 'content': user_prompt})

    def add_assistant_message(self, assistant_response: str):
        """添加助手消息"""
        self._messages.append({'role': 'assistant', 'content': assistant_response})

    def add_assistant_tool_call_message(
        self, 
        tool_call_id: str, 
        tool_name: str, 
        tool_args: dict
    ):
        self._messages.append(
            {
                'role': 'assistant', 
                'content': None, 
                'tool_calls': [
                    {
                        'id': tool_call_id,
                        'type': 'function',
                        'function': {
                            'name': tool_name,
                            'arguments': json.dumps(tool_args, ensure_ascii=False),
                        },
                        'type': 'function',
                        'index': 0
                    }
                ]
            }
        )

    def add_tool_message(self, tool_call_id: str, tool_response: str):
        self._messages.append({'role': 'tool', 'content': tool_response, 'tool_call_id': tool_call_id})
