import io
from ctypes import create_string_buffer

def pack_message(message):
    return message.struct.pack(message.__class__.id, *message.deflate())

def pack_messages(messages):
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
    lng = messages[0].binary_length * len(messages)
    buf = create_string_buffer(lng)
    offset = 0

    for msg in messages:
        msg.struct.pack_into(buf, offset, message.__class__.id, *msg.deflate())
        offset += msg.__class__.binary_length

    return buf.raw
