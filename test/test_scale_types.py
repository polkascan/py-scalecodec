# Python SCALE Codec Library
#
# Copyright 2018-2020 Stichting Polkascan (Polkascan Foundation).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
import unittest

from scalecodec.base import ScaleBytes, RuntimeConfigurationObject
from scalecodec.exceptions import RemainingScaleBytesNotEmptyException, InvalidScaleTypeValueException, \
    ScaleEncodeException, ScaleDecodeException
# from scalecodec.types import GenericContractExecResult
#
# from scalecodec.base import ScaleDecoder, ScaleBytes, RemainingScaleBytesNotEmptyException, \
#     InvalidScaleTypeValueException, RuntimeConfiguration, RuntimeConfigurationObject
# from scalecodec.types import GenericMultiAddress
from scalecodec.type_registry import load_type_registry_preset, load_type_registry_file
from scalecodec.types import MetadataVersioned, Compact, U32, U16, I16, Tuple, String, Vec, AccountId, BitVec, Era, \
    MultiAddress, AccountId, Bool, Balance, Array, HashMap, Bytes, U8, MultiAccountId
from scalecodec.utils.ss58 import ss58_encode, ss58_decode, ss58_decode_account_index, ss58_encode_account_index


class TestScaleTypes(unittest.TestCase):

    metadata_fixture_dict = {}
    metadata_decoder = None
    runtime_config_v14 = None
    metadata_v14_obj = None

    @classmethod
    def setUpClass(cls):
        module_path = os.path.dirname(__file__)
        cls.metadata_fixture_dict = load_type_registry_file(
            os.path.join(module_path, 'fixtures', 'metadata_hex.json')
        )

        cls.metadata_v14_obj = MetadataVersioned.new()

        cls.metadata_v14_obj.decode(ScaleBytes(cls.metadata_fixture_dict['V14']))

    def test_multiple_decode_without_error(self):
        obj = U16.new()
        obj.decode(ScaleBytes("0x2efb"))
        obj.decode(ScaleBytes("0x2efb"))
        self.assertEqual(obj.value, 64302)

    def test_value_equals_value_serialized_and_value_object(self):
        obj = RuntimeConfiguration().create_scale_object('(Compact<u32>,Compact<u32>)', ScaleBytes("0x0c00"))
        obj.decode()
        self.assertEqual(obj.value, obj.value_serialized)
        self.assertEqual(obj.value, obj.value_object)

    def test_value_object(self):
        obj = Tuple(Compact(U32), Compact(U32)).new()
        obj.decode(ScaleBytes("0x0c00"))
        self.assertEqual(obj.value_object[0].value_object, 3)
        self.assertEqual(obj.value_object[1].value_object, 0)

    def test_value_object_shorthand(self):
        obj = Tuple(Compact(U32), Compact(U32)).new()
        obj.decode(ScaleBytes("0x0c00"))
        self.assertEqual(obj[0], 3)
        self.assertEqual(obj[1], 0)

    def test_compact_u32(self):
        obj = Compact(U32).new()
        obj.decode(ScaleBytes("0x02093d00"))
        self.assertEqual(obj.value, 1000000)

    def test_compact_u32_1byte(self):
        obj = Compact(U32).new()
        obj.decode(ScaleBytes("0x18"))
        self.assertEqual(obj.value, 6)

    def test_compact_u32_remaining_bytes(self):
        obj = Compact(U32).new()
        with self.assertRaises(ScaleDecodeException):
            obj.decode(ScaleBytes("0x02093d0001"), check_remaining=True)

    def test_compact_u32_invalid(self):
        obj = Compact(U32).new()
        self.assertRaises(RemainingScaleBytesNotEmptyException, obj.decode, ScaleBytes("0x"))

    def test_u16(self):
        obj = U16.new()
        obj.decode(ScaleBytes("0x2efb"))
        self.assertEqual(obj.value, 64302)

    def test_i16(self):
        obj = I16.new()
        obj.decode(ScaleBytes("0x2efb"))
        self.assertEqual(obj.value, -1234)

    def test_f64(self):
        obj = RuntimeConfiguration().create_scale_object('f64', ScaleBytes("0x0000000000000080"))
        obj.decode()
        self.assertEqual(obj.value, -0.0)

    def test_f32(self):
        obj = RuntimeConfiguration().create_scale_object('f32', ScaleBytes("0x00000080"))
        obj.decode()
        self.assertEqual(obj.value, -0.0)

    def test_bool_true(self):
        obj = Bool().new()
        obj.decode(ScaleBytes("0x01"))
        self.assertEqual(obj.value, True)

    def test_bool_false(self):
        obj = Bool().new()
        obj.decode(ScaleBytes("0x00"))
        self.assertEqual(obj.value, False)

    def test_bool_invalid(self):
        obj = Bool().new()
        self.assertRaises(ScaleDecodeException, obj.decode, ScaleBytes("0x02"))

    def test_string(self):
        obj = String.new()
        obj.decode(ScaleBytes("0x1054657374"))
        self.assertEqual(obj.value, "Test")

        data = obj.encode("Test")

        self.assertEqual("0x1054657374", data.to_hex())

    def test_string_multibyte_chars(self):
        obj = String.new()

        data = obj.encode('µ')
        self.assertEqual('0x08c2b5', data.to_hex())

        obj.decode(data)
        self.assertEqual(obj.value, "µ")

    def test_vec_accountid(self):
        obj = Vec(AccountId()).new()

        obj.decode(ScaleBytes("0x0865d2273adeb04478658e183dc5edf41f1d86e42255442af62e72dbf1e6c0b97765d2273adeb04478658e183dc5edf41f1d86e42255442af62e72dbf1e6c0b977"))
        self.assertListEqual(obj.value, [
            '5END82tfD39fvgwxe9qCkZJxtyQCtFJXzeSnBXpAR2D7vkVM',
            '5END82tfD39fvgwxe9qCkZJxtyQCtFJXzeSnBXpAR2D7vkVM'
        ])

    def test_tuple(self):
        obj = Tuple(Compact(U32), Compact(U32)).new()
        obj.decode(ScaleBytes("0x0c00"))
        self.assertEqual(obj.value, (3, 0))

    def test_tuple_deserialize(self):
        obj = Tuple(Compact(U32), Compact(U32)).new()
        obj.deserialize((3, 2))
        self.assertEqual(obj.value, (3, 2))

    def test_balance(self):
        obj = Compact(Balance).new()
        obj.decode(ScaleBytes("0x130080cd103d71bc22"))
        self.assertEqual(obj.value, 2503000000000000000)

    def test_dynamic_fixed_array_type_decode(self):
        obj = Array(U32, 1).new()
        self.assertEqual([1], obj.decode(ScaleBytes("0x01000000")))

        obj = Array(U32, 3).new()
        self.assertEqual([1, 2, 3], obj.decode(ScaleBytes("0x010000000200000003000000")))

        obj = Array(U32, 0).new()
        self.assertEqual([], obj.decode(ScaleBytes(bytes())))

    def test_dynamic_fixed_array_type_decode_u8(self):
        obj = Array(U8, 65).new()
        self.assertEqual(
            '0xc42b82d02bce3202f6a05d4b06d1ad46963d3be36fd0528bbe90e7f7a4e5fcd38d14234b1c9fcee920d76cfcf43b4ed5dd718e357c2bc1aae3a642975207e67f01',
            obj.decode(ScaleBytes("0xc42b82d02bce3202f6a05d4b06d1ad46963d3be36fd0528bbe90e7f7a4e5fcd38d14234b1c9fcee920d76cfcf43b4ed5dd718e357c2bc1aae3a642975207e67f01"))
        )

    def test_dynamic_fixed_array_type_encode_u8(self):
        obj = Array(U8, 2).new()
        self.assertEqual('0x0102', str(obj.encode('0x0102')))
        self.assertEqual('0x0102', str(obj.encode(b'\x01\x02')))
        self.assertEqual('0x0102', str(obj.encode([1, 2])))

    def test_dynamic_fixed_array_type_encode(self):
        obj = Array(U32, 2).new()
        self.assertEqual('0x0100000002000000', str(obj.encode([1, 2])))

        obj = Array(U8, 3).new()
        self.assertEqual('0x010203', str(obj.encode('0x010203')))

    def test_invalid_fixed_array_type_encode(self):
        obj = Array(U8, 3).new()
        self.assertRaises(ScaleEncodeException, obj.encode, '0x0102')

        obj = Array(U32, 3).new()
        self.assertRaises(ScaleEncodeException, obj.encode, '0x0102')

    def test_create_multi_sig_address(self):

        account1 = AccountId(ss58_format=2).new()
        account1.deserialize("CdVuGwX71W4oRbXHsLuLQxNPns23rnSSiZwZPN4etWf6XYo")

        account2 = AccountId(ss58_format=2).new()
        account2.deserialize("J9aQobenjZjwWtU2MsnYdGomvcYbgauCnBeb8xGrcqznvJc")

        account3 = AccountId(ss58_format=2).new()
        account3.deserialize("HvqnQxDQbi3LL2URh7WQfcmi8b2ZWfBhu7TEDmyyn5VK8e2")

        multi_account_id = MultiAccountId([account1, account2, account3], 2, ss58_format=2).new()

        self.assertEqual(multi_account_id.ss58_address, "HFXXfXavDuKhLLBhFQTat2aaRQ5CMMw9mwswHzWi76m6iLt")

    def test_era_immortal(self):
        obj = Era().new()
        obj.decode(ScaleBytes('0x00'))
        self.assertEqual(obj.value, 'Immortal')
        self.assertIsNone(obj.period)
        self.assertIsNone(obj.phase)

    def test_era_mortal(self):
        obj = Era().new()
        obj.decode(ScaleBytes('0x4e9c'))
        self.assertDictEqual(obj.value, {'Mortal': (32768, 20000)})
        self.assertEqual(obj.period, 32768)
        self.assertEqual(obj.phase, 20000)

        obj = Era().new()
        obj.decode(ScaleBytes('0xc503'))
        self.assertDictEqual(obj.value, {'Mortal': (64, 60)})
        self.assertEqual(obj.period, 64)
        self.assertEqual(obj.phase, 60)

        obj = Era().new()
        obj.decode(ScaleBytes('0x8502'))
        self.assertDictEqual(obj.value, {'Mortal': (64, 40)})
        self.assertEqual(obj.period, 64)
        self.assertEqual(obj.phase, 40)

    def test_era_methods(self):
        obj = Era.new()
        obj.encode('Immortal')
        self.assertTrue(obj.is_immortal())
        self.assertEqual(obj.birth(1400), 0)
        self.assertEqual(obj.death(1400), 2**64 - 1)

        obj = Era.new()
        obj.encode({'Mortal': (256, 120)})
        self.assertFalse(obj.is_immortal())
        self.assertEqual(obj.birth(1400), 1400)
        self.assertEqual(obj.birth(1410), 1400)
        self.assertEqual(obj.birth(1399), 1144)
        self.assertEqual(obj.death(1400), 1656)

    def test_era_invalid_encode(self):
        obj = Era.new()
        self.assertRaises(ValueError, obj.encode, (1, 120))
        self.assertRaises(ValueError, obj.encode, ('64', 60))
        self.assertRaises(ValueError, obj.encode, 'x')
        self.assertRaises(ValueError, obj.encode, {'phase': 2})
        self.assertRaises(ValueError, obj.encode, {'period': 2})

    def test_era_invalid_decode(self):
        obj = Era().new()
        self.assertRaises(ValueError, obj.decode, ScaleBytes('0x0101'))

    def test_multiaddress_ss58_address_as_str(self):
        obj = MultiAddress(ss58_format=2).new()
        ss58_address = "CdVuGwX71W4oRbXHsLuLQxNPns23rnSSiZwZPN4etWf6XYo"

        public_key = ss58_decode(ss58_address)

        data = obj.encode(ss58_address)
        decode_obj = MultiAddress(ss58_format=2).new()
        value = decode_obj.decode(data)

        self.assertEqual(value, f'0x{public_key}')

    def test_multiaddress_ss58_address_as_str_runtime_config(self):

        runtime_config = RuntimeConfigurationObject(ss58_format=2)
        runtime_config.update_type_registry(load_type_registry_preset("legacy"))

        obj = RuntimeConfiguration().create_scale_object('Multiaddress', runtime_config=runtime_config)
        ss58_address = "CdVuGwX71W4oRbXHsLuLQxNPns23rnSSiZwZPN4etWf6XYo"

        data = obj.encode(ss58_address)
        decode_obj = RuntimeConfiguration().create_scale_object('MultiAddress', data=data, runtime_config=runtime_config)

        self.assertEqual(decode_obj.decode(), ss58_address)

    def test_multiaddress_ss58_index_as_str(self):
        obj = RuntimeConfiguration().create_scale_object('MultiAddress')
        ss58_address = "F7Hs"

        index_id = ss58_decode_account_index(ss58_address)

        data = obj.encode(ss58_address)
        decode_obj = RuntimeConfiguration().create_scale_object('MultiAddress', data=data)

        self.assertEqual(decode_obj.decode(), index_id)

    def test_multiaddress_account_id(self):
        # Decoding
        obj = MultiAddress().new()
        obj.decode(ScaleBytes('0x00f6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'))
        self.assertEqual({'Id': '5He5wScLMseSXNqdkS5pVoTag7w9GXwXSNHZUFw5j1r3czsF'}, obj.value)
        self.assertEqual(
            '0xf6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45',
            obj.value_object[1].public_key
        )

        # Encoding
        self.assertEqual(
            ScaleBytes('0x00f6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'),
            obj.encode('0xf6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45')
        )
        self.assertEqual(
            ScaleBytes('0x00f6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'),
            obj.encode({'Id': '0xf6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'})
        )

    def test_multiaddress_index(self):
        # Decoding
        obj = MultiAddress().new()
        obj.decode(data=ScaleBytes('0x0104'))
        self.assertEqual({'Index': 1}, obj.value)

        # Encoding
        self.assertEqual(ScaleBytes('0x0104'), obj.encode(1))
        self.assertEqual(ScaleBytes('0x0104'), obj.encode({'Index': 1}))
        self.assertEqual(ScaleBytes('0x0104'), obj.encode('F7NZ'))

    def test_multiaddress_address20(self):
        obj = MultiAddress().new()
        obj.decode(ScaleBytes('0x0467f89207abe6e1b093befd84a48f033137659292'))
        self.assertEqual({'Address20': '0x67f89207abe6e1b093befd84a48f033137659292'}, obj.value)

    def test_multiaddress_address32(self):
        obj = MultiAddress().new()
        obj.decode(ScaleBytes('0x03f6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'))
        self.assertEqual({'Address32': '0xf6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'}, obj.value)

        # Encoding
        self.assertEqual(
            ScaleBytes('0x03f6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'),
            obj.encode({'Address32': '0xf6a299ecbfec56e238b5feedfb4cba567d2902af5d946eaf05e3badf05790e45'})
        )

    def test_multiaddress_bytes_cap(self):
        # Test decoding
        obj = MultiAddress().new()
        obj.decode(ScaleBytes(
            '0x02b4111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
        ))
        self.assertEqual(
            {'Raw': '0x111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'},
            obj.value
        )

        # Test encoding
        self.assertEqual(
            ScaleBytes(
                '0x02b4111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'
            ),
            obj.encode(
                {'Raw': '0x111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111'}
            )
        )

        with self.assertRaises(ScaleEncodeException):
            obj.encode('0x111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111')

    def test_multiaddress_bytes_pad(self):
        # Test decoding
        obj = GenericMultiAddress(data=ScaleBytes(
            '0x02081234'
        ))
        obj.decode()
        self.assertEqual(
            {'Raw': '0x1234'},
            obj.value
        )
        self.assertEqual('1234000000000000000000000000000000000000000000000000000000000000', obj.account_id)

        # Test encoding
        self.assertEqual(
            ScaleBytes(
                '0x02081234'
            ),
            obj.encode(
                {'Raw': '0x1234'}
            )
        )

        with self.assertRaises(NotImplementedError):
            obj.encode('0x1234')

    def test_ss58_encode_index(self):
        self.assertEqual(ss58_encode_account_index(0), 'F7Hs')

    def test_bitvec_decode(self):
        obj = BitVec().new()
        obj.decode(ScaleBytes('0x0c07'))
        self.assertEqual(obj.value, '0b111')

    def test_bitvec_decode_size2(self):
        obj = BitVec().new()
        obj.decode(ScaleBytes('0x0803'))
        self.assertEqual(obj.value, '0b11')

    def test_bitvec_decode_size_2bytes(self):
        obj = BitVec().new()
        obj.decode(ScaleBytes('0x28fd02'))
        self.assertEqual(obj.value, '0b1011111101')

    def test_bitvec_encode_list(self):
        obj = BitVec().new()
        data = obj.encode([True, True, True])
        self.assertEqual(data.to_hex(), '0x0c07')

    def test_bitvec_encode_list2(self):
        obj = BitVec().new()
        data = obj.encode([True, False])
        self.assertEqual(data.to_hex(), '0x0802')

    def test_bitvec_encode_list3(self):
        obj = BitVec().new()
        data = obj.encode([False, True])
        self.assertEqual(data.to_hex(), '0x0401')

    def test_bitvec_encode_list4(self):
        obj = BitVec().new()
        data = obj.encode([True, False, False, True, True, True, True, True, False, True])
        self.assertEqual(data.to_hex(), '0x287d02')

    def test_bitvec_encode_bin_str(self):
        obj = BitVec().new()
        data = obj.encode('0b00000111')
        self.assertEqual(data.to_hex(), '0x0c07')

    def test_bitvec_encode_bin_str2(self):
        obj = BitVec().new()
        data = obj.encode('0b00000010')
        self.assertEqual(data.to_hex(), '0x0802')

    def test_bitvec_encode_bin_str3(self):
        obj = BitVec().new()
        data = obj.encode('0b00000001')
        self.assertEqual(data.to_hex(), '0x0401')

    def test_bitvec_encode_bin_str4(self):
        obj = BitVec().new()
        data = obj.encode('0b00000010_01111101')
        self.assertEqual(data.to_hex(), '0x287d02')

    def test_bitvec_encode_int(self):
        obj = BitVec().new()
        data = obj.encode(0b00000111)
        self.assertEqual(data.to_hex(), '0x0c07')

    def test_bitvec_encode_int2(self):
        obj = BitVec().new()
        data = obj.encode(0b00000010)
        self.assertEqual(data.to_hex(), '0x0802')

    def test_bitvec_encode_int3(self):
        obj = BitVec().new()
        data = obj.encode(0b00000001)
        self.assertEqual(data.to_hex(), '0x0401')

    def test_bitvec_encode_int4(self):
        obj = BitVec().new()
        data = obj.encode(0b00000010_01111101)
        self.assertEqual(data.to_hex(), '0x287d02')

    def test_bitvec_encode_empty_list(self):
        obj = BitVec().new()
        data = obj.encode([])
        self.assertEqual(data.to_hex(), '0x00')

    def test_hashmap_encode(self):
        obj = HashMap(Vec(U8), U32).new()
        data = obj.encode([('1', 2), ('23', 24), ('28', 30), ('45', 80)])
        self.assertEqual(data.to_hex(), '0x10043102000000083233180000000832381e00000008343550000000')

    def test_hashmap_decode(self):
        obj = HashMap(String, U32).new()
        data = ScaleBytes("0x10043102000000083233180000000832381e00000008343550000000")
        self.assertEqual([('1', 2), ('23', 24), ('28', 30), ('45', 80)], obj.decode(data))

    def test_account_id(self):

        ss58_address = "CdVuGwX71W4oRbXHsLuLQxNPns23rnSSiZwZPN4etWf6XYo"
        public_key = '0x' + ss58_decode(ss58_address)

        # Encode
        obj = AccountId().new(ss58_format=2)
        data = obj.encode(ss58_address)

        # Decode
        decode_obj = AccountId().new(ss58_format=2)
        decode_obj.decode(data)

        self.assertEqual(decode_obj.value, ss58_address)
        self.assertEqual(decode_obj.ss58_address, ss58_address)
        self.assertEqual(decode_obj.public_key, public_key)

    def test_generic_vote(self):
        runtime_config = RuntimeConfigurationObject(ss58_format=2)

        vote = runtime_config.create_scale_object('GenericVote')
        data = vote.encode({'aye': True, 'conviction': 'Locked2x'})

        self.assertEqual('0x82', data.to_hex())

        vote.decode(ScaleBytes('0x04'))

        self.assertEqual(vote.value, {'aye': False, 'conviction': 'Locked4x'})

    def test_raw_bytes(self):
        runtime_config = RuntimeConfigurationObject(ss58_format=2)

        raw_bytes_obj = runtime_config.create_scale_object('RawBytes')
        data = '0x01020304'

        raw_bytes_obj.decode(ScaleBytes(data))
        self.assertEqual(data, raw_bytes_obj.value)

        raw_bytes_obj.encode(data)
        self.assertEqual(ScaleBytes(data), raw_bytes_obj.data)

