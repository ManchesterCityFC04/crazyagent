class Response:

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
