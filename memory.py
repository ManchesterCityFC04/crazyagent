from __future__ import annotations

from .utils import CS

from abc import ABC, abstractmethod
import json

from tabulate import tabulate
from typeguard import typechecked

# 当使用 list[str] 作为类型注解时，typeguard 的行为会有以下区别：
# 对于 print(x([dict(), 1, 'abc']))
# 列表内至少包含一个 str 类型的元素
# typeguard 执行"最宽松匹配"检查，发现存在匹配的 str 类型，认为这是一个"部分符合"的情况

class Message(ABC):

    @abstractmethod
    def __iter__(self):
        pass

@typechecked
class SystemMessage(Message):

    def __init__(self, content: str):
        self.role = 'system'
        self.content = content

    def __iter__(self):
        yield 'role', self.role
        yield 'content', self.content

    def format(self, **kwargs) -> SystemMessage:
        self.content = self.content.format(**kwargs)
        return self

@typechecked
class HumanMessage(Message):

    def __init__(self, content: str):
        self.role = 'user'
        self.content = content

    def __iter__(self):
        yield 'role', self.role
        yield 'content', self.content

@typechecked
class AIMessage(Message):

    def __init__(self, content: str):
        self.role = 'assistant'
        self.content = content

    def __iter__(self):
        yield 'role', self.role
        yield 'content', self.content

@typechecked
class AICallToolMessage(Message):

    def __init__(self, tool_call_id: str, tool_name: str, tool_args: str):
        self.role = 'assistant'
        self.content = None
        self.tool_call_id = tool_call_id
        self.tool_name = tool_name
        self.tool_args = tool_args

    def __iter__(self):
        yield 'role', self.role
        yield 'content', self.content
        yield 'tool_calls', [
            {
                'id': self.tool_call_id,
                'type': 'function',
                'function': {
                    'name': self.tool_name,
                    'arguments': self.tool_args,
                },
                'type': 'function',
                'index': 0
            }
        ]

@typechecked
class ToolMessage(Message):

    def __init__(self, content: str, tool_call_id: str):
        self.role = 'tool'
        self.content = content
        self.tool_call_id = tool_call_id
    
    def __iter__(self):
        yield 'role', self.role
        yield 'content', self.content
        yield 'tool_call_id', self.tool_call_id

class Memory:

    def __init__(self, max_turns: int = 5):
        self._messages: list[Message] = []
        self._system_message: SystemMessage = None
        self.max_turns = max_turns

    @property
    def system_message(self) -> SystemMessage:
        return self._system_message

    @system_message.setter
    def system_message(self, system_message: SystemMessage) -> None:
        if not isinstance(system_message, SystemMessage):
            raise ValueError('系统消息必须是 SystemMessage 类的实例')
        self._system_message = system_message

    def add(self, *args) -> None:
        for m in args:
            if not isinstance(m, Message):
                raise ValueError('消息必须是 Message 类的实例')
            if isinstance(m, SystemMessage):
                raise ValueError('系统消息请使用 system_message 属性设置')
        for m in args:
            self._messages.append(m)

    def pop(self) -> Message:
        return self._messages.pop()

    def __iter__(self):
        messages = self._messages
        if len(messages) > self.max_turns * 2:
            messages = messages[-self.max_turns*2:]
        if self._system_message:
            messages = [self._system_message] + messages
        yield from [dict(m) for m in messages]

    def __str__(self):
        r = [[CS.purple('角色'), CS.purple('内容')]]
        for m in self._messages:
            if isinstance(m, SystemMessage):
                role = CS.red(m.role)
                content = CS.red(m.content)
            elif isinstance(m, HumanMessage):
                role = m.role
                content = m.content
            elif isinstance(m, AIMessage):
                role = CS.blue(m.role)
                content = CS.blue(m.content)
            elif isinstance(m, AICallToolMessage):
                role = CS.yellow(m.role)
                content = CS.yellow(f"{m.tool_name}({': '.join(f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}' for k, v in json.loads(m.tool_args).items())})")
            elif isinstance(m, ToolMessage):
                role = CS.green(m.role)
                content = CS.green(m.content)

            if len(content) > 50:
                content = content[:50] + '...'
            r.append([role, content])
        return tabulate(r, headers='firstrow', tablefmt='grid')
