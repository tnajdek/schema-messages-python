# -*- coding: utf-8 -*-
import unittest
import struct
import math
import sys
from mock import MagicMock
from message import MessageFactory, ImproperlyConfigured, pack_messages, unpack_message, unpack_mesages


class TestInterface(unittest.TestCase):
	schema = {
		'FooMessage': {
			'enums': {
				'direction': {
					'north': 1,
					'south': 2,
					'east': 3,
					'west': 4
				}
			},
			'format': {
				'x': 'uint',
				'y': 'uint',
				'direction': 'enum'
			}
		},
		'BarMessage': {
			'format': {
				'name': 'string',
				'score': 'ushort',
			}
		},
		'VectorMessage': {
			'format': {
				'x': 'float',
				'y': 'float'
			}
		}
	}

	def setUp(self):
		self.factory = MessageFactory(self.schema)

	def get_foo_msg(self, x=1, y=3, direction='south'):
		msg = self.factory.get('FooMessage')()
		msg['x'] = x
		msg['y'] = y
		msg['direction'] = direction
		return msg

	def get_bar_msg(self, name="Yoda", score=42):
		msg = self.factory.get("BarMessage")()
		msg['name'] = name
		msg['score'] = score
		return msg

	def get_vector_msg(self, x=1, y=7.77):
		msg = self.factory.get("VectorMessage")()
		msg['x'] = x
		msg['y'] = y
		return msg

	def test_message_factory(self):
		FooMessage = self.factory.get('FooMessage')
		BarMessage = self.factory.get('BarMessage')
		self.assertEqual(FooMessage.__name__, 'FooMessage')
		self.assertEqual(FooMessage.binary_format, '!BBII')
		self.assertEqual(FooMessage.id, 2)
		self.assertEqual(FooMessage.schema, self.schema)

		self.assertEqual(BarMessage.binary_format, '!BI{}sH')
		self.assertEqual(BarMessage.id, 1)

	def test_packing(self):
		msg = self.get_foo_msg(x=2, y=4, direction='east')
		packed = msg.pack()
		self.assertEqual(len(packed), 1 + 1 + 4 + 4)
		self.assertEqual(packed[0:1], struct.pack('!B', 2))  # msg id
		self.assertEqual(packed[1:2], struct.pack('!B', 3))  # direction
		self.assertEqual(packed[2:6], struct.pack('!I', 2))  # x
		self.assertEqual(packed[6:10], struct.pack('!I', 4))  # y

	def test_packing_with_string(self):
		msg = self.get_bar_msg(name=u'Mr ☃')
		string_length = len(str(u'Mr ☃'.encode('utf-8')))
		packed = msg.pack()
		self.assertEqual(len(packed), 1 + 2 + 4 + string_length)
		self.assertEqual(packed[0:1], struct.pack('!B', 1))  # msg id
		self.assertEqual(packed[1:5], struct.pack('!I', string_length))  # length of the following string
		self.assertEqual(packed[5:5 + string_length], struct.pack('!{}s'.format(string_length), str(u'Mr ☃'.encode('utf-8'))))  # name
		self.assertEqual(packed[5 + string_length:7 + string_length], struct.pack('!H', 42))  # score

	def test_unpacking(self):
		x = 1
		y = 7.77
		msg = self.get_vector_msg(x=1, y=7.77)
		packed = struct.pack("!B", 3) + struct.pack("!f", 1) + struct.pack("!f", 7.77)

		msg = unpack_message(packed, self.factory)
		self.assertEqual(msg['x'], x)
		self.assertAlmostEqual(msg['y'], y, places=4)

	def test_unpacking_with_string(self):
		msg = self.get_bar_msg(name=u'Mr ☃')
		string_length = len(str(u'Mr ☃'.encode('utf-8')))
		packed = struct.pack("!B", 1) + \
			struct.pack("!I", string_length) + \
			struct.pack("!{}s".format(string_length), str(u'Mr ☃'.encode('utf-8'))) + \
			struct.pack("!H", 42)

		msg = unpack_message(packed, self.factory)
		self.assertEqual(msg['name'], u'Mr ☃')
		self.assertEqual(msg['score'], 42)

	def test_eating_own_dog_food(self):
		msg = self.get_foo_msg(y=1.0)
		packed = msg.pack()
		unpacked = unpack_message(packed, self.factory)
		self.assertEqual(msg, unpacked)

	def test_unpacking_many(self):
		msg = self.get_foo_msg()
		packed = struct.pack("!B", msg.__class__.id) + struct.pack("!B", 2) + \
			struct.pack('!I', 1) + struct.pack('!I', 3)

		msg = self.get_bar_msg()
		string_length = len(str(msg['name']))
		packed += struct.pack("!B", msg.__class__.id) + \
			struct.pack("!I", string_length) + \
			struct.pack("!{}s".format(string_length), msg['name']) + \
			struct.pack("!H", 42)
		msg = self.get_vector_msg()
		packed += struct.pack("!B", msg.__class__.id) + struct.pack("!f", 1) + struct.pack("!f", 7.77)

		unpacked = unpack_mesages(packed, self.factory)
		self.assertEqual(unpacked[0].__class__.__name__, 'FooMessage')
		self.assertEqual(unpacked[1].__class__.__name__, 'BarMessage')
		self.assertEqual(unpacked[2].__class__.__name__, 'VectorMessage')

		self.assertEqual(unpacked[0]['direction'], 'south')
		self.assertEqual(unpacked[0]['x'], 1)
		self.assertEqual(unpacked[0]['y'], 3)

		self.assertEqual(unpacked[1]['name'], u'Yoda')
		self.assertEqual(unpacked[1]['score'], 42)

		self.assertEqual(unpacked[2]['x'], 1)
		self.assertAlmostEqual(unpacked[2]['y'], 7.77, places=2)

	def test_packing_many(self):
		messages = []
		msg1 = self.get_foo_msg()
		messages.append(msg1)
		our_packed = struct.pack("!B", msg1.__class__.id) + struct.pack("!B", 2) + \
			struct.pack('!I', 1) + struct.pack('!I', 3)

		msg2 = self.get_bar_msg()
		messages.append(msg2)
		string_length = len(str(msg2['name']))
		our_packed += struct.pack("!B", msg2.__class__.id) + \
			struct.pack("!I", string_length) + \
			struct.pack("!{}s".format(string_length), msg2['name']) + \
			struct.pack("!H", 42)

		msg3 = self.get_vector_msg()
		messages.append(msg3)
		our_packed += struct.pack("!B", msg3.__class__.id) + struct.pack("!f", 1) + struct.pack("!f", 7.77)

		their_packed = pack_messages(messages)
		self.assertEqual(our_packed, their_packed)

	def test_bad_schema(self):
		large_schema = MagicMock()
		large_schema.__len__.return_value = 300

		very_large_schema = MagicMock()
		very_large_schema.__len__.return_value = math.pow(2, 32) - 1

		edge_case_schema = MagicMock()
		edge_case_schema.__len__.return_value = sys.maxsize

		bad_schema = MagicMock()
		bad_schema.__len__.return_value = sys.maxsize + 1

		bad_format_schema = {
			'BadMessage': {
				'format': {
					'bad_property': 'shibboleth',
				}
			}
		}

		try:
			MessageFactory(large_schema)
			MessageFactory(very_large_schema)
			MessageFactory(edge_case_schema)
		except ImproperlyConfigured:
			self.fail()

		self.assertRaises(ImproperlyConfigured, MessageFactory, bad_schema)
		self.assertRaises(ImproperlyConfigured, MessageFactory, bad_format_schema)

	def test_bad_enum(self):
		FooMessage = self.factory.get('FooMessage')

		try:
			FooMessage.enum_lookup('direction', 'south')
		except KeyError:
			self.fail()

		try:
			FooMessage.enum_reverse_lookup('direction', 2)
		except KeyError:
			self.fail()

		self.assertRaises(KeyError, FooMessage.enum_lookup, 'direction', 'shibboleth')
		self.assertRaises(KeyError, FooMessage.enum_lookup, 'shibboleth', 'south')
		self.assertRaises(KeyError, FooMessage.enum_reverse_lookup, 'direction', 5)
		self.assertRaises(KeyError, FooMessage.enum_reverse_lookup, 'shibboleth', 2)
