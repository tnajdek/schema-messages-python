import struct
from bidict import bidict


class MessageBase(object):
	"""
	Base class for a message that can be packed/unpacked
	"""
	enums = {}

	def __init__(self, classtype):
		self._type = classtype

	def dehydrate(self):
		dehydrated = list()
		for key in self.schema['format']:
			value = self.get(key, 0)
			if(hasattr(self, 'dehydrate_%s' % key)):
				hydrator = getattr(self, 'dehydrate_%s' % key)
				if(hasattr(hydrator, '__call__')):
					value = hydrator(value)
			dehydrated.append(value)
		return dehydrated

	def pack(self):
		dehydrated = self.dehydrate()
		buffer_ = struct.pack(self.schema['byteformat'], *dehydrated)
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
	def from_packed(cls, data):
		buffer_ = buffer(data)
		item = struct.unpack_from(cls.schema['byteformat'], buffer_)
		item = list(item)
		return cls.from_dehydrated(item)

	@classmethod
	def from_dehydrated(cls, data):
		item = cls()
		for idx, key in enumerate(item.schema['format']):
			value = data[idx]

			if(hasattr(item, 'hydrate_%s' % key)):
				hydrator = getattr(item, 'hydrate_%s' % key)
				if(hasattr(hydrator, '__call__')):
					value = hydrator(value)
			item[key] = value
		return item

	@classmethod
	def get_byte_length(self):
		return struct.calcsize(self.schema['byteformat'])

message_types = {}


def MessageFactory(schema, explicit_create=False):
	"""
	Factory generates message classes based on a schema provided
	It also keeps track of message ids using message_types
	and will not allow duplicates
	"""
	def new_class_init(self, *args, **kwargs):
		if(args):
			self.hydrate(args[0])

	if(schema['id'] in message_types.keys() and explicit_create):
		raise Exception("Message type already registered with id {} and explicit_create set to True".format(schema['id']))

	if(schema['id'] in message_types.keys()):
		return message_types[schema['id']]

	newclass = type(schema['name'], (MessageBase,), {
		'__init__': new_class_init
	})

	if('enums' in schema):
		for key in schema['enums'].keys():
			newclass.enums[key] = bidict(schema['enums'][key])

	newclass.schema = schema

	message_types[schema['id']] = newclass
	return newclass


def pack_messages(messages):
	"""
	Packs any number of messages of the same kind into
	a single binary string for network transmission.
	First byte identifies a message id.
	"""
	if(len(messages) == 0):
		return ''

	buffer_ = struct.pack('B', messages[0].schema['id'])
	for message in messages:
		if(message and hasattr(message, 'pack')):
			buffer_ += message.pack()
	return buffer_


def unpack_mesages(data, message_types=message_types):
	"""
	Unpacks any number of messages of the same kind
	from binary string into object instances.
	"""
	buffer_ = buffer(data)
	messages = list()
	message_cls = message_types[struct.unpack('B', buffer_[0])[0]]
	message_count = (len(buffer_) - 1) / message_cls.get_byte_length()
	for i in range(message_count):
		msg_buffer = buffer_[1 + i * message_cls.get_byte_length():1 + (i + 1) * message_cls.get_byte_length()]
		messages.append(message_cls.from_packed(msg_buffer))
	return messages
