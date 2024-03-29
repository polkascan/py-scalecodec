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
import os
import unittest

from scalecodec.base import ScaleBytes
from scalecodec.types import Extrinsic, MetadataVersioned
from scalecodec.type_registry import load_type_registry_preset, load_type_registry_file

from test.fixtures import metadata_1045_hex, metadata_substrate_node_template


class TestScaleTypeEncoding(unittest.TestCase):

    def setUp(self) -> None:
        pass

    @classmethod
    def setUpClass(cls):
        cls.metadata_fixture_dict = load_type_registry_file(
            os.path.join(os.path.dirname(__file__), 'fixtures', 'metadata_hex.json')
        )

        cls.metadata_obj = MetadataVersioned.new()

        cls.metadata_obj.decode(ScaleBytes(cls.metadata_fixture_dict['V14']))

    def test_encode_utility_batch_single_payload_scaletype_v14(self):
        call = self.metadata_obj.get_call_type_def().new()

        call.encode({
            'Balances': {
                'transfer_keep_alive': {
                    'dest': 'EaG2CRhJWPb7qmdcJvy3LiWdh26Jreu9Dx6R1rXxPmYXoDk',
                    'value': 1000000000000
                }
            }
        })

        extrinsic = self.metadata_obj.get_extrinsic_type_def().new()

        payload = extrinsic.encode({'call': call})

        self.assertEqual(
            "0xa804050700586cb27c291c813ce74e86a60dad270609abf2fc8bee107e44a80ac00225c409070010a5d4e8", str(payload)
        )

    def test_encode_utility_batch_multiple_payload_scaletype_v14(self):
        call = self.metadata_obj.get_call_type_def().new()

        call.encode(
            {
                'Balances': {
                    'transfer_keep_alive': {
                        'dest': 'EaG2CRhJWPb7qmdcJvy3LiWdh26Jreu9Dx6R1rXxPmYXoDk',
                        'value': 1000000000000
                    }
                }
            }
        )

        extrinsic = self.metadata_obj.get_extrinsic_type_def().new()

        payload = extrinsic.encode({'call': {'Utility': {'batch': {'calls': [call, call]}}}})

        self.assertEqual("0x5901041a0008050700586cb27c291c813ce74e86a60dad270609abf2fc8bee107e44a80ac00225c409070010a5d4e8050700586cb27c291c813ce74e86a60dad270609abf2fc8bee107e44a80ac00225c409070010a5d4e8", str(payload))

    def test_encode_utility_cancel_as_multi_payload(self):
        extrinsic = Extrinsic(metadata=self.metadata_decoder)

        payload = extrinsic.encode({
            'call_module': 'Utility',
            'call_function': 'cancel_as_multi',
            'call_args': {
                'call_hash': '0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
                'other_signatories': [],
                'threshold': 5,
                'timepoint': {
                    'height': 10000,
                    'index': 1
                }
            }
        })

        self.assertEqual(str(payload), "0xb804180405000010270000010000000123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")

    def test_signed_extrinsic(self):
        extrinsic = Extrinsic(metadata=self.metadata_decoder)

        extrinsic_value = {
            'account_id': '5E9oDs9PjpsBbxXxRE9uMaZZhnBAV38n2ouLB28oecBDdeQo',
            'signature_version': 1,
            'signature': '0x728b4057661816aa24918219ff90d10a34f1db4e81494d23c83ef54991980f77cf901acd970cb36d3c9c9e166d27a83a3aee648d4085e2bdb9e7622c0538e381',
            'call': {
                'call_function': 'transfer_keep_alive',
                'call_module': 'Balances',
                'call_args': {
                    'dest': '0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d',
                    'value': 1000000000000
                }
            },
            'nonce': 0,
            'era': '00',
            'tip': 0
        }

        extrinsic_hex = extrinsic.encode(extrinsic_value)

        obj = RuntimeConfiguration().create_scale_object(
            "Extrinsic",
            data=extrinsic_hex,
            metadata=self.metadata_decoder
        )

        decoded_extrinsic = obj.decode()

        self.assertEqual(extrinsic_value['signature'], decoded_extrinsic['signature'])
        self.assertEqual(extrinsic_value['call']['call_args']['dest'], decoded_extrinsic['call']['call_args'][0]['value'])

    def test_decode_mortal_extrinsic(self):
        RuntimeConfiguration().update_type_registry(load_type_registry_preset("substrate-node-template"))
        RuntimeConfiguration().set_active_spec_version_id(1)

        metadata_decoder = RuntimeConfiguration().create_scale_object(
            'MetadataVersioned', ScaleBytes(metadata_substrate_node_template)
        )
        metadata_decoder.decode()

        extrinsic_scale = '0x4102841c0d1aa34c4be7eaddc924b30bab35e45ec22307f2f7304d6e5f9c8f3753de560186be385b2f7b25525518259b00e6b8a61e7e821544f102dca9b6d89c60fc327922229c975c2fa931992b17ab9d5b26f9848eeeff44e0333f6672a98aa8b113836935040005031c0d1aa34c4be7eaddc924b30bab35e45ec22307f2f7304d6e5f9c8f3753de560f0080c6a47e8d03'

        extrinsic = Extrinsic(metadata=metadata_decoder, data=ScaleBytes(extrinsic_scale))
        extrinsic.decode()

        self.assertEqual(extrinsic['call']['call_function'].name, 'transfer_keep_alive')

        era_obj = RuntimeConfiguration().create_scale_object('Era')
        era_obj.encode({'period': 666, 'current': 4950})

        self.assertEqual(extrinsic['era'].period, era_obj.period)
        self.assertEqual(extrinsic['era'].phase, era_obj.phase)
        self.assertEqual(extrinsic['era'].get_used_bytes(), era_obj.data.data)

        # Check lifetime of transaction
        self.assertEqual(extrinsic['era'].birth(4955), 4950)
        self.assertEqual(extrinsic['era'].death(4955), 5974)

    def test_encode_mortal_extrinsic(self):
        RuntimeConfiguration().update_type_registry(load_type_registry_preset("substrate-node-template"))
        RuntimeConfiguration().set_active_spec_version_id(1)

        metadata_decoder = RuntimeConfiguration().create_scale_object(
            'MetadataVersioned', ScaleBytes(metadata_substrate_node_template)
        )
        metadata_decoder.decode()

        extrinsic = Extrinsic(metadata=metadata_decoder)

        extrinsic_value = {
            'account_id': '5ChV6DCRkvaTfwNHsiE2y3oQyPwTJqDPmhEUoEx1t1dupThE',
            'signature_version': 1,
            'signature': '0x86be385b2f7b25525518259b00e6b8a61e7e821544f102dca9b6d89c60fc327922229c975c2fa931992b17ab9d5b26f9848eeeff44e0333f6672a98aa8b11383',
            'call': {
                'call_function': 'transfer_keep_alive',
                'call_module': 'Balances',
                'call_args': {
                    'dest': '5ChV6DCRkvaTfwNHsiE2y3oQyPwTJqDPmhEUoEx1t1dupThE',
                    'value': 1000000000000000
                }
            },
            'nonce': 1,
            'era': {'period': 666, 'current': 4950},
            'tip': 0
        }

        extrinsic_hex = extrinsic.encode(extrinsic_value)
        extrinsic_scale = '0x4102841c0d1aa34c4be7eaddc924b30bab35e45ec22307f2f7304d6e5f9c8f3753de560186be385b2f7b25525518259b00e6b8a61e7e821544f102dca9b6d89c60fc327922229c975c2fa931992b17ab9d5b26f9848eeeff44e0333f6672a98aa8b113836935040005031c0d1aa34c4be7eaddc924b30bab35e45ec22307f2f7304d6e5f9c8f3753de560f0080c6a47e8d03'

        self.assertEqual(str(extrinsic_hex), extrinsic_scale)
