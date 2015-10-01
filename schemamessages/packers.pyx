import io
from ctypes import create_string_buffer

def pack_message(message):
    """
    Pack a single message into a binary string
    """
    return message.struct.pack(message.__class__.id, *message.deflate())

def pack_messages(messages):
    """
    Pack a list of messages into a a binary string
    """
    lng = 0
    for msg in messages:
        lng += msg.binary_length

    buf = create_string_buffer(lng)
    offset = 0

    for msg in messages:
        msg.struct.pack_into(buf, offset, msg.__class__.id, *msg.deflate())
        offset += msg.binary_length

    return buf.raw


def pack_messages_of_single_type(messages):
    """
    Pack a list of single type, fixed-size (i.e. no string) messages
    into a binary string
    Offers slightly higher performance than pack_messages
    but produces invalid results if arguments contains
    non-uniform or non-fixed-size messages (no checks are done)
    """
    buf = create_string_buffer(messages[0].binary_length * len(messages))
    offset = 0

    for msg in messages:
        msg.struct.pack_into(buf, offset, msg.__class__.id, *msg.deflate())
        offset += msg.binary_length

    return buf.raw
