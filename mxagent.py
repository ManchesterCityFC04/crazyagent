import inspect
from enum import Enum
from collections import defaultdict
from functools import wraps
import json
from typing import Literal

from pydantic_core._pydantic_core import PydanticUndefinedType
from pydantic import Field
from pydantic.fields import FieldInfo

from openai import OpenAI
from colorama import Fore, Style

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

class ChatMemory:

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
                    lines.append(CS.green(f"[tool] > {cut(msg['content'])}"))
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

    def add_tool_message(self, tool_call_id: str, tool_response: list | dict):
        self._messages.append({'role': 'tool', 'content': json.dumps(tool_response, ensure_ascii=False), 'tool_call_id': tool_call_id})

class ChatResponse:

    # 为属性分配固定大小的内存空间, 减少内存占用, 
    # 直接通过固定偏移量访问属性, 比字典查找更快
    __slots__ = (
        'user_prompt',
        'assistant_response',
        'assistant_chunk_response',
        'stop_usage',
        'tool_calls_info',
    )

    def __init__(
        self,
        user_prompt: str = None,
        assistant_response: str = None,
        assistant_chunk_response: str = None,
        stop_usage: dict = None,
    ):
        """
        Args Examples:
            user_prompt = '今天北京的天气怎么样呀？'

            assistant_response = '北京的天气是 24°C。'

            stop_usage = {
                'prompt_tokens': 100,
                'completion_tokens': 100,
                'total_tokens': 200,
            }

            tool_calls_info = [
                {
                    'name': 'get_weather',
                    'args': {"city": "北京"},
                    'response': {"temp": "24°C"},
                    'usage': {
                        'prompt_tokens': 100,
                        'completion_tokens': 100,
                        'total_tokens': 200
                    }
                },
                ...
            ]
        """
        self.user_prompt: str = user_prompt
        self.assistant_response: str = assistant_response
        self.assistant_chunk_response: str = assistant_chunk_response
        self.stop_usage: dict = stop_usage
        self.tool_calls_info: list[dict] = []

    def add_tool_call_info(
        self,
        name: str, 
        args: dict,
        response: list | dict, 
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int
    ):
        self.tool_calls_info.append({
            'name': name,
            'args': args,
            'response': response,
            'usage': {
                'prompt_tokens': prompt_tokens,
                'completion_tokens': completion_tokens,
                'total_tokens': total_tokens
            }
        })

    @property
    def total_tokens(self) -> int:
        """消耗的总 token 数量(包括工具调用)"""
        if self.stop_usage is None:
            raise Exception('stop_usage 未被设置')
        return self.stop_usage.get('total_tokens', 0) + sum([t['usage']['total_tokens'] for t in self.tool_calls_info])

class ChatDeepseek:

    def __init__(
        self,
        api_key: str,
        model: str = 'deepseek-chat',
        base_url: str = 'https://api.deepseek.com'
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat(
        self,
        user_prompt: str, 
        memory: ChatMemory = None, 
        tools: list[callable] = [],
    ):
        if memory:
            if not isinstance(memory, ChatMemory):
                raise ValueError("memory 必须是 ChatMemory 类的实例")
        else:
            memory = ChatMemory()
        memory.add_user_message(user_prompt)
        
        tool_map, tools_definition = self._check_tools(tools)

        chat_response = ChatResponse()
        assistant_response: str = ''
        while True:
            chat_completion_stream = self._client.chat.completions.create(
                model=self.model,
                messages=memory.get_messages(),
                tools=tools_definition if tools_definition else None,
                stream=True
            )

            tools_to_call = defaultdict(dict)
            now_tool_call_id: str = None

            for chunk in chat_completion_stream:
                choice: dict = chunk.choices[0]  
                finish_reason: Literal['stop', 'tool_calls', None] = choice.finish_reason
                content: str | None = choice.delta.content  
                if content == '' and finish_reason not in ['stop', 'tool_calls']: continue

                # 正常对话终止
                if finish_reason == 'stop':
                    memory.add_assistant_message(assistant_response)
                    chat_response.user_prompt = user_prompt
                    chat_response.assistant_response = assistant_response
                    chat_response.stop_usage = {
                        'prompt_tokens': chunk.usage.prompt_tokens,
                        'completion_tokens': chunk.usage.completion_tokens,
                        'total_tokens': chunk.usage.total_tokens
                    }
                    chat_response.assistant_chunk_response = ''
                    yield chat_response
                    return
                # 工具调用终止
                elif finish_reason == 'tool_calls':
                    for k, v in dict(tools_to_call).items():
                        tool_call_id: str = k
                        tool_name: str = v['tool_name']
                        tool_args: dict = json.loads(v['tool_args'])

                        tool_response: list | dict = self._get_tool_response(
                            tool_map=tool_map,
                            tool_name=tool_name,
                            tool_args=tool_args
                        )

                        memory.add_assistant_tool_call_message(tool_call_id, tool_name, tool_args)
                        memory.add_tool_message(tool_call_id, tool_response)
                        chat_response.add_tool_call_info(
                            name=tool_name, 
                            args=tool_args, 
                            response=tool_response, 
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens
                        )
                        break
                
                # 非终止情况下处理工具调用
                if (tool_calls := choice.delta.tool_calls) is not None:
                    tool_call = tool_calls[0]  # 获取第一个工具调用
                    # func_name 第一次出现是字符串, 其余出现是 None
                    func_name = tool_call.function.name  # 工具调用的函数名
                    # func_args 第一次出现是空字符串, 其余出现是非空字符串
                    func_args = tool_call.function.arguments  # 工具调用的参数  
                    if tool_call.id not in tools_to_call and tool_call.id is not None:
                        now_tool_call_id = tool_call.id
                        tools_to_call[now_tool_call_id]['tool_name'] = func_name

                    if not tools_to_call[now_tool_call_id].get('tool_args'):
                        tools_to_call[now_tool_call_id]['tool_args'] = ''
                    tools_to_call[now_tool_call_id]['tool_args'] += func_args
                    continue
                # 非终止情况下处理正常输出
                else:
                    assistant_response += content
                    yield ChatResponse(assistant_chunk_response=content)

    def _check_tools(self, tools: list[callable]) -> tuple[dict[str, callable], list[dict]]:
        tool_map = {tool.__name__: tool for tool in tools}
        tools_definition = []
        for tool in tools:
            if inspect.iscoroutinefunction(tool):
                raise ValueError("工具函数不能是异步函数")
            if not hasattr(tool, 'tool_definition'):
                raise ValueError("工具函数必须使用 @tool 装饰器")
            tools_definition.append(tool.tool_definition)
        return tool_map, tools_definition

    def _get_tool_response(
        self, 
        tool_map: dict[str, callable], 
        tool_name: str, 
        tool_args: dict
    ) -> dict:
        """获取工具函数的响应"""
        tool_response = tool_map[tool_name](**tool_args)
        return tool_response


# def chat(
#     self, 
#     user_prompt: str, 
#     memory: ChatMemory = None, 
#     tools: list[callable] = [],
# ):
#     if memory:
#         if not isinstance(memory, ChatMemory):
#             raise ValueError("memory 必须是 ChatMemory 类的实例")
#     else:
#         memory = ChatMemory()
#     memory.add_user_message(user_prompt)
    
#     tool_map, tools_definition = self._check_tools(tools)

#     chat_response = ChatResponse()
#     while True:
#         chat_completion = self._client.chat.completions.create(
#             model=self.model,
#             messages=memory.get_messages(),
#             tools=tools_definition if tools_definition else None
#         )
#         prompt_tokens = chat_completion.usage.prompt_tokens
#         completion_tokens = chat_completion.usage.completion_tokens
#         total_tokens = chat_completion.usage.total_tokens

#         if (choice := chat_completion.choices[0]).finish_reason == 'stop':
#             memory.add_assistant_message(choice.message.content)
#             chat_response.user_prompt = user_prompt
#             chat_response.assistant_response = choice.message.content
#             chat_response.stop_usage = {
#                 'prompt_tokens': prompt_tokens,
#                 'completion_tokens': completion_tokens,
#                 'total_tokens': total_tokens
#             }
#             return chat_response
        
#         elif choice.finish_reason == 'tool_calls':
#             tool_call_id: str = choice.message.tool_calls[0].id
#             tool_name: str = choice.message.tool_calls[0].function.name
#             tool_args: dict = json.loads(choice.message.tool_calls[0].function.arguments)

#             tool_response: list | dict = self._get_tool_response(
#                 tool_map=tool_map,
#                 tool_name=tool_name,
#                 tool_args=tool_args
#             )

#             memory.add_assistant_tool_call_message(tool_call_id, tool_name, tool_args)
#             memory.add_tool_message(tool_call_id, tool_response)
#             chat_response.add_tool_call_info(
#                 name=tool_name, 
#                 args=tool_args, 
#                 response=tool_response, 
#                 prompt_tokens=prompt_tokens,
#                 completion_tokens=completion_tokens,
#                 total_tokens=total_tokens
#             )