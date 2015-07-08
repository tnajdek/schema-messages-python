# -*- coding: utf-8 -*-
import unittest
import struct
from message import MessageFactory, pack_messages, unpack_message, unpack_mesages


class TestInterface(unittest.TestCase):
	def setUp(self):
		self.factory = MessageFactory({
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
		})

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

	# def test_message_packing(self):
	# 	TestMessage = self.get_foo_msg_class()
	# 	msg = self.get_test_msg()
	# 	msg2 = self.get_test_msg(x=5, direction=TestMessage.enum_lookup('direction', 'west'))
	# 	result = pack_messages([msg, msg2])
	# 	expected_byte_length = 1 + 2 * msg.get_byte_length()
	# 	self.assertEqual(len(result), expected_byte_length)

	# def test_message_unpacking(self):
	# 	TestMessage = self.get_foo_msg_class()
	# 	x1 = 12
	# 	y1 = 4.44
	# 	dir1 = TestMessage.enum_lookup('direction', 'west')
	# 	packed = struct.pack("!I", x1) + struct.pack("!f", y1) + struct.pack("!B", dir1)
	# 	x2 = 42
	# 	y2 = 9.987654
	# 	dir2 = TestMessage.enum_lookup('direction', 'north')
	# 	packed = packed + struct.pack("!I", x2) + struct.pack("!f", y2) + struct.pack("!B", dir2) + "\n"

	# 	packed = struct.pack("!B", 42) + packed

	# 	messages = unpack_mesages(packed, message_types=42)
	# 	self.assertEqual(len(messages), 2)
	# 	self.assertEqual(messages[0]['x'], x1)
	# 	self.assertAlmostEqual(messages[0]['y'], y1, places=4)
	# 	self.assertEqual(messages[0]['direction'], dir1)
	# 	self.assertEqual(messages[1]['x'], x2)
	# 	self.assertAlmostEqual(messages[1]['y'], y2, places=4)
	# 	self.assertEqual(messages[1]['direction'], dir2)

	# def test_eating_own_dog_food(self):
	# 	TestMessage = self.get_foo_msg_class()
	# 	msg = self.get_test_msg(y=1.0)
	# 	packed = msg.pack()
	# 	unpacked = TestMessage.from_packed(packed)
	# 	self.assertEqual(msg, unpacked)
