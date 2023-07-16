import pprint
from typing import Any, Callable, Dict


class ApiDataType:
    def mock(self) -> None:
        raise NotImplementedError()

    def marshal(self, value) -> None:
        raise NotImplementedError()

    def validate(self, value) -> None:
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__

    __repr__ = __str__


class Field:
    __slots__ = (
        'name',
        'field_type',
        'mock_func',
        'enum_values',
        'comment',
        'nullable',
        'marshal',
    )

    def __init__(
        self,
        field_type: ApiDataType,
        mock_func: Callable = None,
        enum_values: tuple = (),
        comment: str = '',
        nullable: bool = True,
        marshal: Callable = None,
    ) -> None:
        self.name = ''
        self.field_type = field_type
        self.mock_func = mock_func
        self.enum_values = enum_values
        self.comment = comment
        self.nullable = nullable
        self.marshal = marshal or self.field_type.marshal

    def __str__(self):
        return '<Field [{}]: {}>'.format(self.name, self.field_type)

    def __repr__(self):
        return 'Field({})'.format(self.field_type)


class ModelMetaClass(type):
    def __new__(mcs, name: str, bases: tuple, attrs: dict):
        __fields_map__ = {}

        for base in bases:
            for field in getattr(base, '__fields__', ()):
                if field.name not in __fields_map__:
                    __fields_map__[field.name] = field

        for field_name, field in attrs.copy().items():
            if isinstance(field, Field):
                field.name = field_name
                __fields_map__[field_name] = field
                attrs.pop(field_name)

        attrs['__fields__'] = tuple(__fields_map__.values())
        attrs['__fields_map__'] = __fields_map__
        attrs['__slots__'] = tuple(list(__fields_map__.keys()) + ['__storage__'])

        return type.__new__(mcs, name, bases, attrs)


class BaseModel(object, metaclass=ModelMetaClass):
    __fields__ = ()
    __fields_map__ = {}

    def __init__(self, drop_missing=False, **kwargs) -> None:
        for field_name, field in self.__fields_map__.items():
            value = kwargs.get(field_name)
            if not drop_missing and not field.nullable and value is None:
                raise Exception('field [{}] must be initialized'.format(field_name))
            setattr(self, field_name, value)

    def marshal(self, values=None) -> Dict[str, str]:
        dct = {}

        if values is None:
            values = self
        for field_name, field in self.__fields_map__.items():
            value = values.get(field_name)
            dct[field_name] = field.marshal(value)

        return dct

    def get(self, item, default=None) -> Any:
        return getattr(self, item, default)

    def __str__(self):
        return '[<{}>: \n{}]'.format(self.__class__.__name__, pprint.pformat(self.marshal(), indent=4))

    __repr__ = __str__
