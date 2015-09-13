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


class MessageBaseMeta(type):
    @property
    def id(cls):
        """
        Unique id generated for this message class based on the schema
        """
        return cls._id

    @property
    def format(cls):
        """
        Format of this message as per schema
        """
        return cls._format

    @property
    def keys(cls):
        """
        Format of this message as per schema
        """
        return cls._keys

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

    @property
    def binary_length(cls):
        """
        """
        return cls._binary_length

    @property
    def struct(cls):
        """
        """
        return cls._struct


class MessageBase(with_metaclass(MessageBaseMeta, dict)):
    """
    Base class for a message that can be packed/unpacked
    """
    def __init__(self, *args, **kwargs):
        self.struct = self.__class__._struct
        self.binary_length = self.__class__._binary_length
        super(MessageBase, self).__init__(*args, **kwargs)

    def inflate(self, data):
        self.update(zip(self.__class__.keys, data))

    def deflate(self):
        return [self[key] for key in self.__class__.keys]




class MessageEnumMixin(object):
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

    def inflate(self, data):
        super(MessageEnumMixin, self).inflate(data)
        for key in self.__class__._enum_keys:
            self[key] = self.__class__.enums[key].inv[self[key]]

    def deflate(self):
        deflated = super(MessageEnumMixin, self).deflate()
        for i, idx in enumerate(self.__class__._enum_indexes):
            deflated[idx] = self.__class__.enums[self.__class__._enum_keys[i]][deflated[idx]]

        return deflated


class MessageStringMixing(object):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

        if(args or kwargs):
            self._calc_binary_length()
        else:
            self.binary_length = self.__class__._base_binary_length

    def _calc_binary_length(self):
        self._strings_lengths = [len(bytes(self[key], 'utf-8')) for key in self.__class__._string_keys]
        self.binary_length = self.__class__._base_binary_length + sum(self._strings_lengths)
        self.binary_format = self.__class__._base_binary_format.format(*self._strings_lengths)
        self.struct = struct.Struct(self.binary_format)

    def __setitem__(self, key, value):
        super(MessageStringMixing, self).__setitem__(key, value)
        if(key in self.__class__._string_keys):
            self._calc_binary_length()

    def inflate(self, data):
        super(MessageStringMixing, self).inflate(data)
        for key in self.__class__._string_keys:
            self[key] = self[key].decode('utf-8')

    def deflate(self):
        deflated = super(MessageStringMixing, self).deflate()
        for i, idx in enumerate(self.__class__._string_indexes):
            deflated[i + idx] = bytes(deflated[i + idx], 'utf-8')
            deflated.insert(i + idx, self._strings_lengths[i])

        return deflated
