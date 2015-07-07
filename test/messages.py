import unittest
import struct
from message import MessageFactory, pack_messages, unpack_mesages


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
					'user_name': 'string'
				}
			}
		})

	def get_foo_msg_class(self):
		return self.factory.get('FooMessage')

	def get_bar_msg_class(self):
		return self.factory.get('BarMessage')

	def get_test_msg(self, x=1, y=3.33, direction=2):
		msg = self.get_foo_msg_class()
		msg['x'] = x
		msg['y'] = y
		msg['direction'] = direction
		return msg

	def test_message_factory(self):
		TestMessage = self.get_foo_msg_class()
		BarMessage = self.get_bar_msg_class()
		self.assertEqual(TestMessage.__name__, 'FooMessage')
		msg = TestMessage()
		self.assertEqual(msg.binary_format, '!BBII')
		msg2 = BarMessage()
		self.assertEqual(msg2.binary_format, '!BI{}s')


	# def test_packing(self):
	# 	msg = self.get_test_msg()
	# 	packed = msg.pack()
	# 	self.assertEqual(packed[0:4], struct.pack('!I', 1))
	# 	self.assertEqual(packed[4:8], struct.pack('!f', 3.33))
	# 	self.assertEqual(packed[8:9], struct.pack('!B', get_foo_msg_class().enum_lookup('direction', 'south')))

	# def test_dehydration(self):
	# 	TestMessage = self.get_foo_msg_class()
	# 	x = 12
	# 	y = 4.44
	# 	dir = TestMessage.enum_lookup('direction', 'west')

	# 	dehydrated_item = [x, y, dir]
	# 	msg = TestMessage.from_dehydrated(dehydrated_item)

	# 	self.assertEqual(msg['x'], x)
	# 	self.assertEqual(msg['y'], y)
	# 	self.assertEqual(msg['direction'], dir)

	# def test_unpacking(self):
	# 	# packed = '\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x02\x02\n'
	# 	TestMessage = self.get_foo_msg_class()
	# 	x = 12
	# 	y = 7.77
	# 	dir = TestMessage.enum_lookup('direction', 'west')

	# 	packed = struct.pack("!I", x) + struct.pack("!f", y) + struct.pack("!B", dir) + "\n"
	# 	msg = TestMessage.from_packed(packed)
	# 	self.assertEqual(msg['x'], x)
	# 	self.assertAlmostEqual(msg['y'], y, places=4)
	# 	self.assertEqual(msg['direction'], dir)

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
