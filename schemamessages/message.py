"""
This module contains classes and functions to pack and unpack arbitrary
messages into binary strings based on schema provided.

This module contains the following classes:
    * MessageBase - base class for generated message classes
    * MessageFactory - generates message classes based on schema
    * ImproperlyConfigured - exception for misconfiguration cases

This module contains the following functions:
    * unpack_message - unpack single message from binary
    * unpack_messages - unpack multiple messages from binary
    * pack_message - pack one message into binary
    * pack_messages - packe multiple messages into binary
"""
import sys
import struct
import math
from future.utils import with_metaclass
from builtins import bytes
from bidict import bidict


class ImproperlyConfigured(Exception):
    """
    This exception is thrown when invalid schema is detected
    """
    pass

class MessageBaseMeta(type):
    @property
    def id(cls):
        """
        Unique id generated for this message class based on the schema
        """
        return cls._id

    @property
    def schema(cls):
        """
        Reference to the entire schema dict
        """
        return cls._schema

    @property
    def format(cls):
        """
        Format of this message as per schema
        """
        return cls._format

    @property
    def enums(cls):
        """
        2-way dictionary for looking up enum values both ways
        """
        return cls._enums

    @property
    def binary_format(cls):
        """
        Binary format of this message class. This cannot be passed to
        struct directly as it needs ot be processed by the class instance
        first to handle dynamic length of a string
        """
        return cls._binary_format


class MessageBase(with_metaclass(MessageBaseMeta, dict)):
    """
    Base class for a message that can be packed/unpacked
    """

    _enums = {}
    _data = {}

    def get_binary_length(self):
        """
        Returns actual binary length of the message in it's current state
        """
        keys = list(self.__class__.format.keys())
        keys.sort()
        binary_format = self.__class__.binary_format
        string_lengths = []
        for key in keys:
            if(self.__class__.format[key] == 'string'):
                string_lengths.append(len(self[key]))

        binary_format = binary_format.format(*string_lengths)
        return struct.calcsize(binary_format)

    def pack(self):
        binary_format = self.__class__.binary_format
        format_ = self.__class__.format
        keys = list(format_.keys())
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
                # if(type(value) == unicode):
                    # value = value.encode('utf-8')
                value = bytes(value, 'utf-8')
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
            raise KeyError(
                "Attempted to lookup non-existing enum field {}".format(
                    enum_name
                )
            )
        try:
            return enum_field[identifier]
        except KeyError:
            raise KeyError(
                "No value found for identifier {} in enum {}".format(
                    identifier, enum_name
                )
            )

    @classmethod
    def enum_reverse_lookup(cls, enum_name, value):
        try:
            enum_field = cls.enums[enum_name]
        except KeyError:
            raise KeyError(
                "Attempted to lookup non-existing enum field {}".format(
                    enum_name
                )
            )
        try:
            return enum_field.inv[value]
        except KeyError:
            raise KeyError(
                "No identifier found for value {} in enum {}".format(
                    value, enum_name
                )
            )


class MessageFactory(object):
    """
    Factory generates message classes based on a schema provided
    It also keeps track of message ids using message_types
    """

    @classmethod
    def _get_binary_format_symbol(cls, number):
        if(number > sys.maxsize or number > 1.8446744073709552e+19):
            raise OverflowError(
                "Unable to represent number {} in packed structure".format(
                    number
                )
            )

        bytes_needed = math.ceil(math.log(number, 2) / 8)
        if(bytes_needed <= 1):
            binary_format = 'B'
        elif(bytes_needed == 2):
            binary_format = 'H'
        elif(bytes_needed <= 4):
            binary_format = 'I'
        elif(bytes_needed <= 8):
            binary_format = 'Q'

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
        """
        Build binary format for give message schema.
        Used internally to populate "binary_format" field on
        the message class.

        Output of thes method cannot be used directly with struct
        as it needs to be processed by the message instance first
        for handling dynamic-length strings.

        """
        fields = list(msg_schema['format'].keys())
        fields.sort()
        binary_format = '!'  # we always use network (big-endian) byte order
        binary_format += self.id_binary_format

        for field in fields:
            if(msg_schema['format'][field] == 'string'):
                binary_format += 'I{}s'
            elif(msg_schema['format'][field] == 'enum'):
                try:
                    binary_format += self.__class__._get_binary_format_symbol(
                        len(msg_schema['enums'][field])
                    )
                except Exception:
                    raise ImproperlyConfigured(
                        '''Enum field can contain the
                        maximum number {} possible values'''.format(
                            sys.maxsize
                        )
                    )
            else:
                try:
                    field_type = msg_schema['format'][field]
                    binary_format += self.binary_types[field_type]
                except KeyError:
                    raise ImproperlyConfigured(
                        "Unknown field type {}".format(
                            msg_schema['format'][field]
                        )
                    )

        return binary_format

    def get(self, id_or_name):
        """
        Convinience method to return message class for given name or id
        If number is given, we assume id, otheriwse - name.
        """
        if(type(id_or_name) == int):
            return self.get_by_id(id_or_name)
        else:
            return self.get_by_name(id_or_name)

    def get_by_name(self, name):
        """ Return message class given a name (string) """
        try:
            return self.msg_classes_by_name[name]
        except KeyError:
            raise KeyError(
                'No message by the name of {} found in the schema'.format(
                    name
                )
            )

    def get_by_id(self, id):
        """ Return message class for given id """
        try:
            return self.msg_classes_by_id[id]
        except KeyError:
            raise KeyError(
                'No message identified by {} found in the schema'.format(
                    id
                )
            )

    def __init__(self, schema):
        """
        Constructor for message factory, takes schema (dict) as the first
        argument and generates message classes based on the schema.
        """
        def new_class_init(self, *args, **kwargs):
            if(args):
                self.hydrate(args[0])

        keys = list(schema.keys())
        keys.sort()
        next_id = 1
        try:
            self.bytes_needed_for_id = int(
                math.ceil(math.log(len(schema) + 1, 2) / 8)
            )
            self.id_binary_format = self.__class__._get_binary_format_symbol(
                len(schema)
            )
        except OverflowError:
            raise ImproperlyConfigured(
                '''Schema can contain the maximum
                number of {} message types.'''.format(sys.maxsize))

        for msg_class_name in keys:
            newclass = type(msg_class_name, (MessageBase,), {
                '__init__': new_class_init
            })

            if('enums' in schema[msg_class_name]):
                for key in schema[msg_class_name]['enums'].keys():
                    newclass._enums[key] = bidict(
                        schema[msg_class_name]['enums'][key]
                    )

            newclass._binary_format = self.get_binary_format(
                schema[msg_class_name]
            )
            newclass._format = schema[msg_class_name]['format']
            newclass._schema = schema
            newclass._id = next_id

            self.msg_classes_by_name[msg_class_name] = newclass
            self.msg_classes_by_id[next_id] = newclass
            next_id += 1


def unpack_message(data, factory):
    """
    Unpacks a single message from a binary string to an object instance
    """
    buffer_ = memoryview(data)

    (msg_id, ) = struct.unpack_from(
        '!{}'.format(factory.id_binary_format),
        buffer_[0:factory.bytes_needed_for_id]
    )
    cls = factory.get_by_id(msg_id)
    item = cls()

    keys = list(cls.format.keys())
    keys.sort()
    string_lengths = list()
    indexes_to_remove = list()

    # proces string msgs here
    for idx, key in enumerate(keys):
        if(cls.format[key] == 'string'):
            offset = factory.bytes_needed_for_id + idx
            (string_length, ) = struct.unpack_from(
                '!I', buffer_[offset:offset + 4]
            )
            string_lengths.append(string_length)
            indexes_to_remove.append(idx)

    binary_format = cls.binary_format.format(*string_lengths)
    msg_data = list(struct.unpack_from(binary_format, buffer_)[1:])

    for idx in indexes_to_remove:
        del msg_data[idx]

    for idx, key in enumerate(keys):
        item[key] = msg_data[idx]
        if(cls.format[key] == 'string'):
            item[key] = item[key].decode('utf-8')
        if(cls.format[key] == 'enum'):
            item[key] = cls.enum_reverse_lookup(key, item[key])

    return item


def unpack_mesages(data, factory):
    """
    Unpacks any number of messages from binary string into object instances.
    """
    buffer_ = memoryview(data)
    messages = []
    while(len(buffer_)):
        msg = unpack_message(buffer_, factory)
        buffer_ = memoryview(buffer_)[msg.get_binary_length():]
        messages.append(msg)
    return messages


def pack_messages(messages):
    """
    Packs any number of message into a binary string
    """
    binary_string = b''
    for msg in messages:
        binary_string += msg.pack()

    return binary_string
