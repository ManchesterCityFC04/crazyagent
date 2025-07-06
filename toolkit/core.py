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
            raise ValueError('description must be a non-empty string')
        if (default is not ...) and (type(default) not in _PYTHON_JSON_TYPE_MAP):
            raise ValueError(f'default type must be one of the supported types: {_all_supported_types}')
        if enum is not ...:
            for e in enum:
                if type(e) not in _PYTHON_JSON_TYPE_MAP:
                    raise ValueError(f'enum values must be one of the supported types: {_all_supported_types}')
        self.description = description
        self.default = default
        self.required = required
        self.enum = enum

import inspect
from collections import defaultdict
from functools import wraps
import json


def crazy_tool(func: callable) -> callable:
    properties = defaultdict(dict)
    required_s = []

    for _, param in inspect.signature(func).parameters.items():
        # param.name is the parameter name, same as _
        # param.default is the default value of the parameter, if not specified, it is inspect._empty
        # param.annotation is the annotation of the parameter, i.e., the type of the parameter, such as <class 'int'>, <class 'str'>
        # param.annotation.__name__ is the string representation of the parameter type, such as 'int', 'str'
        if param.annotation is inspect._empty:
            raise ValueError(f'Parameter {param.name} of function {func.__name__} must have a type annotation')

        if isinstance(param.annotation, UnionType):
            param_types = []
            for sub_type in param.annotation.__args__:
                if sub_type not in _PYTHON_JSON_TYPE_MAP:
                    raise ValueError(f'Function {func.__name__} only supports parameter types: {_all_supported_types}')
                param_types.append(_PYTHON_JSON_TYPE_MAP[sub_type])
            properties[param.name]['type'] = param_types
        else:
            if param.annotation not in _PYTHON_JSON_TYPE_MAP:
                raise ValueError(f'Function {func.__name__} only supports parameter types: {_all_supported_types}')
            properties[param.name]['type'] = _PYTHON_JSON_TYPE_MAP[param.annotation]

        if not isinstance(param.default, Argument):
            raise ValueError(f'Parameter {param.name} of function {func.__name__} must have a default value of type Argument')

        arguement: Argument = param.default
        properties[param.name]['description'] = arguement.description
        if arguement.default is not ...:
            properties[param.name]['default'] = arguement.default
        if arguement.required:
            required_s.append(param.name)
        if arguement.enum is not ...:
            properties[param.name]['enum'] = arguement.enum

        if not func.__doc__:
            raise ValueError(f'Docstring of function {func.__name__} cannot be empty')

        tool_definition = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "strict": True,  # Strict mode, if the parameters are not specified, an error will be returned
                "description": func.__doc__ if func.__doc__ else '',
                "parameters": {"type": "object", "properties": dict(properties), "additionalProperties": False},
                "required": required_s
            }
        }

    if inspect.iscoroutinefunction(func):
        @wraps(func)
        async def wrap(**kwargs):
            try:
                for required in required_s:
                    if required not in kwargs:
                        raise ValueError(f'Missing required parameter: {required}')
                r = {'result': await func(**kwargs)}
            except Exception as e:
                r = {'error': str(e)}
            return json.dumps(r, ensure_ascii=False, separators=(',', ':'), indent=None)
        wrap._is_async = True
    else:
        @wraps(func)
        def wrap(**kwargs):
            try:
                for required in required_s:
                    if required not in kwargs:
                        raise ValueError(f'Missing required parameter: {required}')
                r = {'result': func(**kwargs)}
            except Exception as e:
                r = {'error': str(e)}
            return json.dumps(r, ensure_ascii=False)
        wrap._is_async = False
        
    wrap._tool_definition = tool_definition
    return wrap

__all__ = [
    'Argument',
    'crazy_tool'
]