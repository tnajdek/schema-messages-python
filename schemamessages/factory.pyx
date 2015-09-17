import sys
import struct
from bidict import bidict
from .utils import get_bytes_to_represent, get_binary_format_symbol, get_symbol_to_represent
from .exceptions import ImproperlyConfigured
from .message import MessageEnumMixin, MessageStringMixing, MessageBase


class MessageFactory(object):
    """
    Factory generates message classes based on a schema provided
    It also keeps track of message ids using message_types
    """

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
                    binary_format += get_symbol_to_represent(
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
        keys = list(schema.keys())
        keys.sort()
        next_id = 1

        try:
            schema_length = len(schema)
            self.bytes_needed_for_id = get_bytes_to_represent(schema_length)
            self.id_binary_format = get_symbol_to_represent(schema_length)
        except OverflowError:
            raise ImproperlyConfigured(
                '''Schema can contain the maximum
                number of {} message types.'''.format(sys.maxsize))

        for msg_class_name in keys:
            schema_types_used = schema[msg_class_name]['format'].values()
            mixins = []

            if('enum' in schema_types_used):
                mixins.append(MessageEnumMixin)
            if('string' in schema_types_used):
                mixins.append(MessageStringMixing)

            mixins.append(MessageBase)

            newclass = type(msg_class_name, tuple(mixins), {})

            if('enum' in schema_types_used):
                newclass._enums = {}
                for key in schema[msg_class_name]['enums'].keys():
                    newclass._enums[key] = bidict(
                        schema[msg_class_name]['enums'][key]
                    )

            newclass._binary_format = self.get_binary_format(
                schema[msg_class_name]
            )
            newclass._format = schema[msg_class_name]['format']
            newclass._keys = list(newclass._format)
            newclass._keys.sort()
            # newclass._schema = schema
            newclass._id = next_id
            newclass._length = len(newclass._keys)

            if('string' in schema_types_used):
                newclass._base_binary_format = newclass._binary_format
                newclass._base_binary_length = struct.calcsize(newclass._binary_format.replace('{}s', ''))
                newclass._string_keys = [key for key in newclass.keys
                    if schema[msg_class_name]['format'][key] == 'string'
                ]
                newclass._string_offsets = [
                    struct.calcsize(o) for o in newclass._base_binary_format.split('I{}s')
                ][:-1]
                newclass._string_indexes = [idx for idx, key in enumerate(newclass.keys)
                    if schema[msg_class_name]['format'][key] == 'string'
                ]
            else:
                newclass._struct = struct.Struct(newclass._binary_format)
                newclass._binary_length = newclass._struct.size


            if('enum' in schema_types_used):
                newclass._enum_keys = [key for key in newclass.keys
                    if schema[msg_class_name]['format'][key] == 'enum'
                ]
                newclass._enum_indexes = [idx for idx, key in enumerate(newclass.keys)
                    if schema[msg_class_name]['format'][key] == 'enum'
                ]

            self.msg_classes_by_name[msg_class_name] = newclass
            self.msg_classes_by_id[next_id] = newclass
            next_id += 1
