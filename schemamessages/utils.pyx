import sys
import math

byte_number_to_symbol = {
    1: 'B',
    2: 'H',
    3: 'I',
    4: 'I',
    5: 'Q',
    6: 'Q',
    7: 'Q',
    8: 'Q'
}

def get_bytes_to_represent(number):
    return math.ceil(math.log(number + 1, 2) / 8)

def get_symbol_to_represent(number):
    if(number > sys.maxsize or number > 1.8446744073709552e+19):
        raise OverflowError(
            "Unable to represent number {} in packed structure".format(
                number
            )
        )
    return get_binary_format_symbol(get_bytes_to_represent(number))

def get_binary_format_symbol(bytes_needed):
    return byte_number_to_symbol[bytes_needed]
