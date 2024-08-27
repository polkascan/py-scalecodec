import enum
import json
import os
import unittest
from dataclasses import dataclass, field
from os import path
from typing import Optional, Type, Union, List

from scalecodec.base import ScaleBytes, ScaleType
from scalecodec.mixins import ScaleSerializable, T
from scalecodec.types import H256, U8, Array, Enum


# Test definitions


@dataclass
class ValidatorData(ScaleSerializable):
    bandersnatch: bytes = field(metadata={'scale': H256})
    ed25519: bytes = field(metadata={'scale': H256})
    bls: bytes = field(metadata={'scale': Array(U8, 144)})
    metadata: bytes = field(metadata={'scale': Array(U8, 128)})


@dataclass
class EpochMark(ScaleSerializable):
    entropy: bytes = field(metadata={'scale': H256})
    validators: List[bytes] = field(metadata={'scale': Array(H256, 6)})

@dataclass
class OutputMarks(ScaleSerializable):
    epoch_mark: Optional[EpochMark] = None


class CustomErrorCode(ScaleSerializable, enum.Enum):
    bad_slot = 0  # Timeslot value must be strictly monotonic.
    unexpected_ticket = 1  # Received a ticket while in epoch's tail.
    bad_ticket_order = 2  # Tickets must be sorted.
    bad_ticket_proof = 3  # Invalid ticket ring proof.
    bad_ticket_attempt = 4  # Invalid ticket attempt value.
    reserved = 5  # Reserved
    duplicate_ticket = 6  # Found a ticket duplicate.
    too_many_tickets = 7  # Found amount of tickets > K


@dataclass
class Output(ScaleSerializable):
    ok: Optional[OutputMarks] = None  # Markers
    err: Optional[CustomErrorCode] = None

    @classmethod
    def scale_type_def(cls):

        return Enum(
            ok=OutputMarks.scale_type_def(),
            err=CustomErrorCode.scale_type_def()
        )

    def to_scale_type(self) -> ScaleType:
        scale_type = self.scale_type_def().new()
        scale_type.deserialize(self.serialize())
        return scale_type

    @classmethod
    def deserialize(cls: Type[T], data: Union[str, int, float, bool, dict, list]) -> T:

        return super().deserialize(data)

    def serialize(self) -> Union[str, int, float, bool, dict, list]:
        if self.err is not None:
            return {'err': self.err.serialize()}
        else:
            return {'ok': self.ok.serialize()}


class TestSerializableMixin(unittest.TestCase):

    def setUp(self):
        data = {
            'bandersnatch': '0x5e465beb01dbafe160ce8216047f2155dd0569f058afd52dcea601025a8d161d',
            'ed25519': '0x3b6a27bcceb6a42d62a3a8d02a6f0d73653215771de243a63ac048a18b59da29',
            'bls': '0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'metadata': '0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        }

        self.test_obj = ValidatorData.deserialize(data)

    def test_dataclass_serialization(self):
        output = Output(ok=OutputMarks(epoch_mark=None))
        value = output.serialize()
        self.assertEqual({'ok': {'epoch_mark': None}}, value)

        output = Output(err=CustomErrorCode.duplicate_ticket)
        value = output.serialize()

        self.assertEqual({'err': 'duplicate_ticket'}, value)

    def test_dataclass_to_scale_type(self):
        output = Output(
            ok=OutputMarks(
                epoch_mark=EpochMark(
                    entropy=bytes(32),
                    validators=[bytes(32), bytes(32), bytes(32), bytes(32), bytes(32), bytes(32)]
                )
            )
        )
        scale_type = output.to_scale_type()
        output2 = Output.from_scale_type(scale_type)
        self.assertEqual(output, output2)

    def test_deserialize(self):

        data = {
            'bandersnatch': '0x5e465beb01dbafe160ce8216047f2155dd0569f058afd52dcea601025a8d161d',
            'ed25519': '0x3b6a27bcceb6a42d62a3a8d02a6f0d73653215771de243a63ac048a18b59da29',
            'bls': '0x000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000',
            'metadata': '0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        }

        validator_obj = ValidatorData.deserialize(data)

        self.assertEqual(self.test_obj, validator_obj)
        self.assertEqual(data, validator_obj.serialize())

    def test_from_to_scale_bytes(self):

        scale_data = self.test_obj.to_scale_bytes()

        validator_obj = ValidatorData.from_scale_bytes(scale_data)

        self.assertEqual(self.test_obj, validator_obj)


if __name__ == '__main__':
    unittest.main()
