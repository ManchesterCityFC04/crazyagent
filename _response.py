class Response:

    # Allocate fixed-size memory for attributes to reduce memory usage,
    # and access attributes directly by fixed offsets, which is faster than dictionary lookup
    __slots__ = (
        'content',
        'stop_usage',
        'tool_calls_info',
    )

    def __init__(self, content: str = '', stop_usage: dict = None):
        """
        Args:
            content: The (chunk) content of the response.

            stop_usage: The usage information of the response.
                e.g.: {
                    'input_tokens': 100,
                    'output_tokens': 100,
                    'total_tokens': 200,
                }

            *tool_calls_info: The information of the tool calls.
                e.g.: [
                    {
                        'name': 'get_weather',
                        'args': {"city": "北京"},
                        'response': {"temp": "24°C"},
                        'usage': {
                            'input_tokens': 100,
                            'output_tokens': 100,
                            'total_tokens': 200
                        }
                    },
                    ...
                ]
        """
        self.content: str = content
        self.stop_usage: dict = stop_usage
        self.tool_calls_info: list[dict] = []

    def add_tool_call_info(
        self,
        name: str, 
        args: dict,
        response: list | dict, 
        usage: dict[str, int]
    ):
        self.tool_calls_info.append({
            'name': name,
            'args': args,
            'response': response,
            'usage': usage
        })

    @property
    def total_tokens(self) -> int:
        """Total number of tokens consumed (including tool calls)."""
        if self.stop_usage is None:
            return None
        return self.stop_usage.get('total_tokens', 0) + sum([t['usage']['total_tokens'] for t in self.tool_calls_info])
