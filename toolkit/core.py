"""
+-------------------+---------------+
| Python            | JSON          |
+===================+===============+
| dict              | object        |
+-------------------+---------------+
| list, tuple       | array         |
+-------------------+---------------+
| str               | string        |
+-------------------+---------------+
| int, float        | number        |
+-------------------+---------------+
| True              | true          |
+-------------------+---------------+
| False             | false         |
+-------------------+---------------+
| None              | null          |
+-------------------+---------------+
"""
from types import UnionType, NoneType
JSONType: UnionType = dict | list | tuple | str | int | float | bool | NoneType
# print(JSONType.__args__)  # (<class 'dict'>, <class 'list'>, <class 'tuple'>, <class 'str'>, <class 'int'>, <class 'float'>, <class 'bool'>, <class 'NoneType'>)

_PYTHON_JSON_TYPE_MAP = {
    dict: 'object',
    list: 'array',
    tuple: 'array',
    str: 'string',
    int: 'number',
    float: 'number',
    bool: 'boolean',
    NoneType: 'null'
}

_all_supported_types = '、'.join([i.__name__ for i in list(_PYTHON_JSON_TYPE_MAP.keys())])

class Argument:

    def __init__(
        self, 
        description: str, 
        default: JSONType = ...,  # type: ignore
        required: bool = True,
        enum: list[JSONType] = ... # type: ignore
    ):
        if not description or not isinstance(description, str):
            raise ValueError('description 必须是非空字符串')
        if (default is not ...) and (type(default) not in _PYTHON_JSON_TYPE_MAP):
            raise ValueError(f'default 类型必须是支持的类型: {_all_supported_types}')
        if enum is not ...:
            for e in enum:
                if type(e) not in _PYTHON_JSON_TYPE_MAP:
                    raise ValueError(f'enum 中的值必须是支持的类型: {_all_supported_types}')
        self.description = description
        self.default = default
        self.required = required
        self.enum = enum

import inspect
from collections import defaultdict
from functools import wraps
import json

def agent_tool(func: callable) -> callable:
    """将函数转换为 agent 工具"""
    properties = defaultdict(dict)
    required_s = []

    for _, param in inspect.signature(func).parameters.items():
        # param.name 是参数的名称, 和 _ 一样
        # param.default 是参数的默认值, 如果未指定默认值, 则为 inspect._empty
        # param.annotation 是参数的注释, 即参数的类型, 例如 <class 'int'>、<class 'str'>
        # param.annotation.__name__ 是参数的类型的字符串表示, 例如 'int'、'str' 
        if param.annotation is inspect._empty:
            raise ValueError(f'函数 {func.__name__} 的参数 {param.name} 必须指定类型')

        if isinstance(param.annotation, UnionType):
            param_types = []
            for sub_type in param.annotation.__args__:
                if sub_type not in _PYTHON_JSON_TYPE_MAP:
                    raise ValueError(f'函数 {func.__name__} 只支持的参数类型: {_all_supported_types}')
                param_types.append(_PYTHON_JSON_TYPE_MAP[sub_type])
            properties[param.name]['type'] = param_types
        else:
            if param.annotation not in _PYTHON_JSON_TYPE_MAP:
                raise ValueError(f'函数 {func.__name__} 只支持的参数类型: {_all_supported_types}')
            properties[param.name]['type'] = _PYTHON_JSON_TYPE_MAP[param.annotation]

        if not isinstance(param.default, Argument):
            raise ValueError(f'函数 {func.__name__} 的参数 {param.name} 的必须有默认值且是 Argument 类型')

        arguement: Argument = param.default
        properties[param.name]['description'] = arguement.description
        if arguement.default is not ...:
            properties[param.name]['default'] = arguement.default
        if arguement.required:
            required_s.append(param.name)
        if arguement.enum is not ...:
            properties[param.name]['enum'] = arguement.enum

        if not func.__doc__:
            raise ValueError(f'函数 {func.__name__} 的文档字符串不能为空')

        tool_definition = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "strict": True,  # 严格模式, 参数类型必须严格匹配
                "description": func.__doc__ if func.__doc__ else '',
                "parameters": {"type": "object", "properties": dict(properties), "additionalProperties": False},
                "required": required_s
            }
        }

    @wraps(func)
    def wrap(*args, **kwargs):
        try:
            r = {'error_occur': False, 'result': func(*args, **kwargs)}
        except Exception as e:
            r = {'error_occur': True, 'detail': str(e)}
        return json.dumps(r, ensure_ascii=False)
    
    wrap._tool_definition = tool_definition
    return wrap

__all__ = [
    'Argument',
    'agent_tool'
]