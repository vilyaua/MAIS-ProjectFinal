# Python json Module

## Serialize to String
```python
import json

json.dumps(['foo', {'bar': ('baz', None, 1.0, 2)}])
# '["foo", {"bar": ["baz", null, 1.0, 2]}]'

json.dumps({"c": 0, "b": 0, "a": 0}, sort_keys=True)
# '{"a": 0, "b": 0, "c": 0}'

print(json.dumps({'4': 5, '6': 7}, sort_keys=True, indent=4))
```

## Serialize to File
```python
with open('data.json', 'w') as f:
    json.dump(data, f, indent=2)
```

## Deserialize from String
```python
json.loads('["foo", {"bar":["baz", null, 1.0, 2]}]')
# ['foo', {'bar': ['baz', None, 1.0, 2]}]
```

## Deserialize from File
```python
with open('data.json') as f:
    data = json.load(f)
```

## Python ↔ JSON Type Mapping

| Python | JSON |
|--------|------|
| dict | object |
| list, tuple | array |
| str | string |
| int, float | number |
| True/False | true/false |
| None | null |

## Custom Serialization
```python
def custom_json(obj):
    if isinstance(obj, complex):
        return {'__complex__': True, 'real': obj.real, 'imag': obj.imag}
    raise TypeError(f'Cannot serialize {type(obj)}')

json.dumps(1 + 2j, default=custom_json)
```

## Custom Deserialization
```python
def as_complex(dct):
    if '__complex__' in dct:
        return complex(dct['real'], dct['imag'])
    return dct

json.loads('{"__complex__": true, "real": 1, "imag": 2}',
    object_hook=as_complex)
```

## Subclassing JSONEncoder
```python
class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, complex):
            return [obj.real, obj.imag]
        return super().default(obj)
```

## Key Parameters
- `indent`: Pretty-print with indentation
- `sort_keys`: Sort dictionary keys
- `separators`: Custom separators `(',', ':')`
- `default`: Function for non-standard types
- `object_hook`: Custom deserialization
- `ensure_ascii`: Escape non-ASCII (default: True)
