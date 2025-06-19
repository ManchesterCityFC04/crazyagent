
from .memory import *
from ._response import Response

import inspect
from typing import Literal
from collections import defaultdict
from abc import abstractmethod, ABC
import json

from openai import OpenAI

class Chat(ABC):

    @abstractmethod
    def stream(self):
        pass

    def check_tools(self, tools: list[callable]) -> tuple[dict[str, callable], list[dict]]:
        tool_map = {tool.__name__: tool for tool in tools}
        tools_definition = []
        for tool in tools:
            if inspect.iscoroutinefunction(tool):
                raise ValueError("工具函数不能是异步函数")
            if not hasattr(tool, '_tool_definition'):
                raise ValueError("工具函数必须使用 @tool 装饰器")
            tools_definition.append(tool._tool_definition)
        return tool_map, tools_definition

    def get_tool_response(
        self, 
        tool_map: dict[str, callable], 
        tool_name: str, 
        tool_args: dict
    ) -> dict:
        """获取工具函数的响应"""
        tool_response = tool_map[tool_name](**tool_args)
        return tool_response

class Deepseek(Chat):

    def __init__(
        self,
        api_key: str,
        model: str = 'deepseek-chat',
        base_url: str = 'https://api.deepseek.com'
    ):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def stream(
        self,
        user_prompt: str, 
        memory: Memory = None, 
        tools: list[callable] = [],
    ):
        if not isinstance(user_prompt, str):
            raise ValueError('user_prompt 必须是字符串')
        if memory:
            if not isinstance(memory, Memory):
                raise ValueError("memory 必须是 Memory 类的实例")
        else:
            memory = Memory()

        memory.add(HumanMessage(content=user_prompt))
        
        tool_map, tools_definition = self.check_tools(tools)

        resp = Response()       
        assistant_response: str = ''
        while True:
            chat_completion_stream = self._client.chat.completions.create(
                model=self.model,
                messages=list(memory),
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
                    memory.add(AIMessage(content=assistant_response))
                    resp.stop_usage = {
                        'prompt_tokens': chunk.usage.prompt_tokens,
                        'completion_tokens': chunk.usage.completion_tokens,
                        'total_tokens': chunk.usage.total_tokens
                    }
                    yield resp
                    return
                # 工具调用终止
                elif finish_reason == 'tool_calls':
                    for k, v in dict(tools_to_call).items():
                        tool_call_id: str = k
                        tool_name: str = v['tool_name']
                        tool_args: str = v['tool_args']
                        tool_args_dict: dict = json.loads(v['tool_args'])

                        tool_response: str = self.get_tool_response(
                            tool_map=tool_map,
                            tool_name=tool_name,
                            tool_args=tool_args_dict
                        )
                        memory.add(AICallToolMessage(tool_call_id, tool_name, tool_args))
                        memory.add(ToolMessage(tool_response, tool_call_id))
                        resp.add_tool_call_info(
                            name=tool_name, 
                            args=tool_args, 
                            response=tool_response, 
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens
                        )
                        # 这里限制了大模型每次只能调用一次工具, 事实上证明这是对的
                        # 调用工具 -> Chat -> 调用工具 -> Chat, 这是最稳定的形式
                        # 如果一次性调用多个工具, 如果下面的工具参数依赖上面工具的返回值, 那就寄了
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
                    yield Response(content=content)

