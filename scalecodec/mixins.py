import dataclasses
from dataclasses import is_dataclass
import enum
from typing import Type, TypeVar, Union
import typing
import json

from scalecodec.base import ScaleTypeDef, ScaleType, ScaleBytes
from scalecodec.types import Struct, Option, Vec, Enum

T = TypeVar('T')


class ScaleSerializable:
    @classmethod
    def scale_type_def(cls) -> ScaleTypeDef:
        if is_dataclass(cls):

            arguments = {}
            for field in dataclasses.fields(cls):
                arguments[field.name] = cls.dataclass_field_to_scale_typ_def(field)

            return Struct(**arguments)
        elif issubclass(cls, enum.Enum):
            variants = {status.name: None for status in cls}
            return Enum(**variants)

        raise NotImplementedError

    def serialize(self) -> Union[str, int, float, bool, dict, list]:
        scale_type = self.to_scale_type()
        return scale_type.serialize()

    @classmethod
    def deserialize(cls: Type[T], data: Union[str, int, float, bool, dict, list]) -> T:
        scale_type = cls.scale_type_def().new()
        scale_type.deserialize(data)
        return cls.from_scale_type(scale_type)

    def to_scale_type(self) -> ScaleType:

        if not is_dataclass(self) and not issubclass(self.__class__, enum.Enum):
            raise NotImplementedError("Type not supported.")

        scale_type = self.scale_type_def().new()

        if issubclass(self.__class__, enum.Enum):
            scale_type.deserialize(self.name)
        elif is_dataclass(self):
            value = {}
            for field in dataclasses.fields(self):

                actual_type = field.type
                field_name = field.name[:-1] if field.name.endswith('_') else field.name

                if typing.get_origin(actual_type) is typing.Union:
                    # Extract the arguments of the Union type
                    args = typing.get_args(actual_type)
                    if type(None) in args:
                        # If NoneType is in the args, it's an Optional
                        actual_type = [arg for arg in args if arg is not type(None)][0]

                if getattr(self, field.name) is None:
                    value[field_name] = None
                else:

                    if typing.get_origin(actual_type) is list:
                        actual_type = typing.get_args(actual_type)[0]

                        if issubclass(actual_type, ScaleSerializable):
                            value[field_name] = [i.serialize() for i in getattr(self, field.name)]
                        else:
                            value[field_name] = getattr(self, field.name)

                    # TODO too simplified now
                    elif issubclass(actual_type, ScaleSerializable):

                        value[field_name] = getattr(self, field.name).serialize()
                    else:
                        value[field_name] = getattr(self, field.name)

            scale_type.deserialize(value)

        return scale_type

    @classmethod
    def from_scale_type(cls: Type[T], scale_type: ScaleType) -> T:
        if is_dataclass(cls):

            fields = {}

            for field in dataclasses.fields(cls):

                scale_field_name = field.name[:-1] if field.name.endswith('_') else field.name

                actual_type = field.type

                if typing.get_origin(field.type) is typing.Union:
                    # Extract the arguments of the Union type
                    args = typing.get_args(field.type)
                    if type(None) in args:
                        # If NoneType is in the args, it's an Optional
                        if field.name in scale_type.value:
                            if scale_type.value[field.name] is None:
                                fields[field.name] = None
                                continue
                            else:
                                actual_type = [arg for arg in args if arg is not type(None)][0]
                        else:
                            # print(field.name)
                            continue

                if typing.get_origin(actual_type) is list:
                    items = []
                    actual_type = typing.get_args(actual_type)[0]

                    if issubclass(type(scale_type.type_def), (Struct, Option)):
                        list_items = scale_type.value_object[scale_field_name].value_object
                    elif issubclass(type(scale_type.type_def), (Vec, Enum)):
                        list_items = scale_type.value_object[1].value_object
                    else:
                        raise ValueError(f'Unsupported type: {type(scale_type.type_def)}')

                    for item in list_items:
                        if actual_type in [str, int, float, bool]:
                            items.append(item.value)
                        elif actual_type is bytes:
                            items.append(item.to_bytes())
                        elif is_dataclass(actual_type):
                            items.append(actual_type.from_scale_type(item))

                    fields[field.name] = items

                elif actual_type in [str, int, float, bool]:
                    fields[field.name] = scale_type.value[scale_field_name]
                elif actual_type is bytes:
                    fields[field.name] = scale_type.value_object[scale_field_name].to_bytes()
                elif is_dataclass(actual_type):
                    try:

                        # TODO unwrap Option
                        if issubclass(type(scale_type.type_def), (Struct, Option)):

                            field_scale_type = scale_type.value_object[scale_field_name]
                        elif issubclass(type(scale_type.type_def), Enum):
                            field_scale_type = scale_type.value_object[1]
                        else:
                            raise ValueError(f"Unexpected type {type(scale_type.type_def)}")

                        fields[field.name] = actual_type.from_scale_type(field_scale_type)
                    except (KeyError, TypeError) as e:
                        print('oeps', str(e))
                elif issubclass(actual_type, enum.Enum):
                    fields[field.name] = actual_type[scale_type.value_object[1].value]
            return cls(**fields)
        raise NotImplementedError

    def to_scale_bytes(self) -> ScaleBytes:
        scale_obj = self.to_scale_type()
        return scale_obj.encode()

    @classmethod
    def from_scale_bytes(cls: Type[T], scale_bytes: ScaleBytes) -> T:
        scale_obj = cls.scale_type_def().new()
        scale_obj.decode(scale_bytes)
        return cls.from_scale_type(scale_obj)

    def to_json(self) -> str:
        return json.dumps(self.serialize(), indent=4)

    @classmethod
    def from_json(cls: Type[T], json_data: str) -> T:
        # data = json.loads(json_data)
        return cls.deserialize(json_data)

    @classmethod
    def dataclass_field_to_scale_typ_def(cls, field) -> ScaleTypeDef:

        if 'scale' in field.metadata:
            return field.metadata['scale']

        # Check if the field type is an instance of Optional
        actual_type = field.type
        wrap_option = False
        wrap_vec = False

        if typing.get_origin(field.type) is typing.Union:
            # Extract the arguments of the Union type
            args = typing.get_args(field.type)
            if type(None) in args:
                # If NoneType is in the args, it's an Optional
                wrap_option = True
                actual_type = [arg for arg in args if arg is not type(None)][0]
                # print(f"The field '{field.name}' is Optional with inner type: {actual_type}")

        if typing.get_origin(actual_type) is list:
            wrap_vec = True
            actual_type = typing.get_args(actual_type)[0]

        if is_dataclass(actual_type):
            if issubclass(actual_type, ScaleSerializable):
                scale_def = actual_type.scale_type_def()
            else:
                raise ValueError(f"Cannot serialize dataclass {field.type.__class__}")

        elif actual_type is bytes:
            raise ValueError("bytes is ambiguous; specify SCALE type def in metadata e.g. {'scale': H256}")
        elif actual_type is int:
            raise ValueError("int is ambiguous; specify SCALE type def in metadata e.g. {'scale': U32}")

        elif issubclass(actual_type, enum.Enum):
            variants = {status.name: None for status in actual_type}
            scale_def = Enum(**variants)

        else:
            raise ValueError(f"Cannot convert {actual_type} to ScaleTypeDef")

        if wrap_vec:
            scale_def = Vec(scale_def)
        if wrap_option:
            scale_def = Option(scale_def)

        return scale_def
