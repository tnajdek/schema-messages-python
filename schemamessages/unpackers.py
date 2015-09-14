import struct

def unpack_message(packed, factory):
    (msg_id, ) = struct.unpack_from(
        factory.id_binary_format,
        packed, 0
    )
    MsgCls = factory.get_by_id(msg_id)
    try:
        data = MsgCls.struct.unpack(packed)
    except AttributeError as e:
        strings_lengths = [struct.unpack_from('!I', packed, o)[0] for o in MsgCls._string_offsets]
        binary_format = MsgCls._base_binary_format.format(*strings_lengths)
        data = [i for idx, i in enumerate(struct.unpack(binary_format, packed)) if idx not in MsgCls._string_indexes]
    item = MsgCls()
    item.inflate(data[1:])
    return item


def unpack_messages(packed, factory):
    messages = []
    offset = 0
    lng = len(packed)

    while offset < lng:
        (msg_id, ) = struct.unpack_from(
            factory.id_binary_format,
            packed, offset
        )

        MsgCls = factory.get_by_id(msg_id)

        try:
            data = MsgCls.struct.unpack_from(packed, offset)
            offset += MsgCls.binary_length
        except AttributeError as e:
            strings_lengths = [struct.unpack_from('!I', packed, offset + o)[0] for o in MsgCls._string_offsets]
            binary_format = MsgCls._base_binary_format.format(*strings_lengths)
            msg_struct = struct.Struct(binary_format)
            data = [i for idx, i in enumerate(msg_struct.unpack_from(packed, offset)) if idx not in MsgCls._string_indexes]
            offset += msg_struct.size

        item = MsgCls()
        item.inflate(data[1:])
        messages.append(item)

    return messages

def unpack_messages_of_single_type(packed, factory):
    # @TODO: optimise me :)
    return unpack_messages(packed, factory)
# def pack_messages_of_single_type():
#     messages = []
#     offset = 0
#     lng = len(packed)
#     (msg_id, ) = struct.unpack_from(
#         factory.id_binary_format,
#         packed, 0
#     )
#     offset += factory.bytes_needed_for_id
#     MsgCls = factory.get_by_id(msg_id)

#     while offset < lng:
#         try:
#             data = MsgCls.struct.unpack_from(packed, offset)
#         except Exception as e:
#             strings_lengths = [struct.unpack_from('!I', packed, offset + o)[0] for o in MsgCls._string_offsets]
#             binary_format = MsgCls._base_binary_length.format(strings_lengths)
#             msg_struct = struct.Struct(binary_format)
#             data = msg_struct.unpack_from(packed, offset)
#             offset += msg_struct.size - factory.bytes_needed_for_id

#         item = MsgCls(*data[1:])
#         messages.append(item)

#     return messages

