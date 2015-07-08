import struct
import math
from bidict import bidict


class MessageBase(dict):
	"""
	Base class for a message that can be packed/unpacked
	"""
	_enums = {}
	_data = {}

	class __metaclass__(type):
		@property
		def id(cls):
			return cls._id

		@property
		def schema(cls):
			return cls._schema

		@property
		def format(cls):
			return cls._format

		@property
		def enums(self):
			return self._enums

		@property
		def binary_format(cls):
			return cls._binary_format

	# def __init__(self, classtype):
	# 	self._type = classtype

	# def __setitem__(self, key, value):
	# 	self._data[key] = value

	# def __getitem__(self, key, value):
	# 	return self._data[key]

	def pack(self):
		binary_format = self.__class__.binary_format
		format_ = self.__class__.format
		keys = format_.keys()
		keys.sort()

		# start off with an id
		data = [self.__class__.id, ]
		# if we encounter any strings, log the length of each one
		str_lengths = []
		for key in keys:
			value = self.get(key, 0)
			if(format_[key] == 'enum'):
				value = self.__class__.enum_lookup(key, value)
			elif(format_[key] == 'string'):
				if(type(value) == unicode):
					value = value.encode('utf-8')
				value = str(value)
				data.append(len(value))
				str_lengths.append(len(value))
			data.append(value)

		if(len(str_lengths)):
			binary_format = binary_format.format(*str_lengths)
		buffer_ = struct.pack(binary_format, *data)
		return buffer_

	@classmethod
	def enum_lookup(cls, enum_name, identifier):
		try:
			enum_field = cls.enums[enum_name]
		except KeyError:
			raise Exception("Attempted to lookup non-existing enum field {}".format(enum_name))
		try:
			return enum_field[identifier]
		except KeyError:
			raise Exception("No value found for identifier {} in enum {}".format(identifier, enum_name))

	@classmethod
	def enum_reverse_lookup(cls, enum_name, value):
		try:
			enum_field = cls.enums[enum_name]
		except KeyError:
			raise Exception("Attempted to lookup non-existing enum field {}".format(enum_name))
		try:
			return enum_field.inv[value]
		except KeyError:
			raise Exception("No identifier found for value {} in enum {}".format(value, enum_name))

	@classmethod
	def get_byte_length(self):
		return struct.calcsize(self.binary_format)


class MessageFactory(object):
	"""
	Factory generates message classes based on a schema provided
	It also keeps track of message ids using message_types
	and will not allow duplicates
	"""

	@classmethod
	def _get_binary_format_symbol(cls, number):
		bytes_needed = math.ceil(math.log(number, 2) / 8)
		if(bytes_needed <= 1):
			binary_format = 'B'
		elif(bytes_needed == 2):
			binary_format = 'H'
		elif(bytes_needed <= 4):
			binary_format = 'I'
		elif(bytes_needed <= 8):
			binary_format = 'Q'
		else:
			raise Exception("Unable to represent number {} in packed structure".format(number))

		return binary_format

	msg_classes_by_name = {}
	msg_classes_by_id = {}
	binary_types = {
		'bool': '?',
		'byte': 'b',
		'ubyte': 'B',
		'char': 'c',
		'short': 'h',
		'ushort': 'H',
		'int': 'i',
		'uint': 'I',
		'int64': 'q',
		'uint64': 'Q',
		'float': 'f',
		'double': 'd'
	}

	def get_binary_format(self, msg_schema):
		fields = msg_schema['format'].keys()
		fields.sort()
		binary_format = '!'  # we always use network (big-endian) byte order
		binary_format += self.id_binary_format

		for field in fields:
			if(msg_schema['format'][field] == 'string'):
				binary_format += 'I{}s'
			elif(msg_schema['format'][field] == 'enum'):
				try:
					binary_format += self.__class__._get_binary_format_symbol(len(msg_schema['format'][field]))
				except Exception:
					raise Exception("Enum field can contain the maximum number of 2^64 - 1 possible values.")
			else:
				try:
					binary_format += self.binary_types[msg_schema['format'][field]]
				except KeyError:
					raise Exception("Unknown field type {}".format(msg_schema['format'][field]))

		return binary_format

	def get(self, id_or_name):
		if(type(id_or_name) == int):
			return self.get_by_id(id_or_name)
		else:
			return self.get_by_name(id_or_name)

	def get_by_name(self, name):
		try:
			return self.msg_classes_by_name[name]
		except KeyError:
			raise Exception("No message by the name of {} found in the schema".format(name))

	def get_by_id(self, id):
		try:
			return self.msg_classes_by_id[id]
		except KeyError:
			raise Exception("No message identified by {} found in the schema".format(id))

	def __init__(self, schema):
		def new_class_init(self, *args, **kwargs):
			if(args):
				self.hydrate(args[0])

		keys = schema.keys()
		keys.sort()
		next_id = 1
		self.bytes_needed_for_id = int(math.ceil(math.log(len(schema), 2) / 8))

		try:
			self.id_binary_format = self.__class__._get_binary_format_symbol(len(schema))
		except Exception:
			raise Exception('Schema can contain the maximum number of 2^64 - 1 message types.')

		for msg_class_name in keys:
			newclass = type(msg_class_name, (MessageBase,), {
				'__init__': new_class_init
			})

			if('enums' in schema[msg_class_name]):
				for key in schema[msg_class_name]['enums'].keys():
					newclass._enums[key] = bidict(schema[msg_class_name]['enums'][key])

			newclass._binary_format = self.get_binary_format(schema[msg_class_name])
			newclass._format = schema[msg_class_name]['format']
			newclass._schema = schema
			newclass._id = next_id

			self.msg_classes_by_name[msg_class_name] = newclass
			self.msg_classes_by_id[next_id] = newclass
			next_id += 1


def pack_messages(messages):
	"""
	Packs any number of messages of the same kind into
	a single binary string for network transmission.
	First byte identifies a message id.
	"""
	if(len(messages) == 0):
		return ''

	buffer_ = struct.pack(messages[0].binaryformat[1], messages[0].id)
	for message in messages:
		if(message and hasattr(message, 'pack')):
			buffer_ += message.pack()
	return buffer_


def unpack_message(data, factory):
	buffer_ = buffer(data)
	(msg_id, ) = struct.unpack_from('!{}'.format(factory.id_binary_format), buffer_[0:factory.bytes_needed_for_id])
	cls = factory.get_by_id(msg_id)
	item = cls()

	keys = cls.format.keys()
	keys.sort()
	string_lengths = list()
	indexes_to_remove = list()

	# proces string msgs here
	for idx, key in enumerate(keys):
		if(cls.format[key] == 'string'):
			offset = factory.bytes_needed_for_id + idx
			(string_length, ) = struct.unpack_from('!I', buffer_[offset:offset + 4])
			string_lengths.append(string_length)
			indexes_to_remove.append(idx)

	binary_format = cls.binary_format.format(*string_lengths)
	data = list(struct.unpack_from(binary_format, buffer_)[1:])

	for idx in indexes_to_remove:
		del data[idx]

	for idx, key in enumerate(keys):
		item[key] = data[idx]
		if(cls.format[key] == 'string'):
			item[key] = item[key].decode('utf-8')

	return item


def unpack_mesages(data, factory):
	"""
	Unpacks any number of messages of the same kind
	from binary string into object instances.
	"""
	buffer_ = buffer(data)
	messages = list()
	message_cls = factory.get_by_id([struct.unpack(self.id_binary_format, buffer_[0])[0]])
	# message_count = (len(buffer_) - 1) / message_cls.get_byte_length()
	# for i in range(message_count):
	# 	msg_buffer = buffer_[1 + i * message_cls.get_byte_length():1 + (i + 1) * message_cls.get_byte_length()]
	# 	messages.append(message_cls.from_packed(msg_buffer))
	return messages
