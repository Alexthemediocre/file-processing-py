"""
A module for converting JSON to Python objects and Python objects to JSON.
Use the methods parse_json and to_json to do this.

Note that to_json can only convert dict, list, str, int, float, bool, and None values.
"""

from __future__ import annotations
from typing import Tuple
import math

# JSON -> Py

JSON_WHITESPACE = (' ', '\t', '\r', '\n')
JSON_NUM_START_CHARS = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-')
JSON_NUM_CHARS = ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.', 'e', 'E', '+', '-')

def parse_json(json: str) -> dict | list | str | float | bool | None:
    """Parses a JSON string into Python values.

    JSON Type => Python Type \n
    `object`   =>   `dict`   \n
    `array`    =>   `list`   \n
    `number`   =>   `float`  \n
    `string`   =>   `str`    \n
    `boolean`  =>   `bool`   \n
    `null`     =>   `None`

    >>> parse_json('{"a": null, "b": [1, true, "a\\\\nb"]}')
    {'a': None, 'b': [1.0, True, 'a\\nb']}
    """
    (parsed, i) = parse_json_base(json)
    i = skip_whitespace(json, i)
    if i < len(json):
        raise SyntaxError(f'Expected end of input at position {i}')
    return parsed

def format_err_str(message: str, text: str, index: int) -> str:
    """
    Replaces the string `$position$` in `message` with `$index$ (line: $line_count$, column: $column$)`.
    Intended to be used to give positional error messages when dealing with a document.
    Both `$line_count$` and `$column$` are zero-indexed.
    """
    line_count = 0
    last_line_index = 0
    for i in range(0, index):
        if text[i] == '\n':
            line_count += 1
            last_line_index = i

    return message.replace("$position$", f"{index} (line: {line_count}, column: {index - last_line_index})")

def parse_json_base(json: str, i: int = 0) -> Tuple[dict | list | str | float | bool | None, int]:
    i = skip_whitespace(json, i)
    if i >= len(json):
        raise SyntaxError(f"Unexpected end of file at position {len(json)}")

    c = json[i]
    if c == '{': return parse_json_obj(json, i)
    elif c == '[': return parse_json_arr(json, i)
    elif c == '"': return parse_json_str(json, i)
    elif c == 'n': return parse_json_null(json, i)
    elif c == 't' or c == 'f': return parse_json_boolean(json, i)
    elif c in JSON_NUM_START_CHARS: return parse_json_number(json, i)
    else:
        raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$", json, i))

def parse_json_obj(json: str, i: int) -> Tuple[dict, int]:
    if json[i] != '{':
        raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected '{'{'}'", json, i))
    i += 1
    i = skip_whitespace(json, i)
    obj = dict()
    try:
        if json[i] == '}':
            return (obj, i + 1)
        while True:
            (key, i) = parse_json_str(json, i)
            i = skip_whitespace(json, i)
            if json[i] != ':':
                raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected ':'", json, i))
            i += 1
            i = skip_whitespace(json, i)
            (val, i) = parse_json_base(json, i)
            obj[key] = val
            i = skip_whitespace(json, i)
            c = json[i]
            if c == '}':
                i += 1
                break
            elif c != ',':
                raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected ',' or '{'}'}'", json, i))
            i += 1
            i = skip_whitespace(json, i)
    except IndexError:
        raise SyntaxError(f"Unexpected end of file at position {len(json)}")
    return (obj, i)

def parse_json_arr(json: str, i: int) -> Tuple[list, int]:
    if json[i] != '[':
        raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected '['", json, i))
    i += 1
    i = skip_whitespace(json, i)
    arr = list()
    try:
        if json[i] == ']':
            return (arr, i + 1)
        while True:
            (val, i) = parse_json_base(json, i)
            arr.append(val)
            i = skip_whitespace(json, i)
            c = json[i]
            if c == ']':
                i += 1
                break
            elif c != ',':
                raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected ',' or ']'", json, i))
            i += 1
            i = skip_whitespace(json, i)
    except IndexError:
        raise SyntaxError(f"Unexpected end of file at position {len(json)}")
    return (arr, i)

def parse_json_null(json: str, i: int) -> Tuple[None, int]:
    if not json.startswith('null', i):
        raise SyntaxError(format_err_str(f"Unexpected string '{json[i:i+4]}' at position $position$. Expected 'null'", json, i))
    return (None, i + 4)

def parse_json_boolean(json: str, i: int) -> Tuple[bool, int]:
    if not json.startswith('true', i) and not json.startswith('false', i):
        raise SyntaxError(format_err_str(f"Unexpected string '{json[i:i+5]}' at position $position$. Expected 'true' or 'false'", json, i))
    return (True, i + 4) if json[i:i+4] == 'true' else (False, i + 5)

def parse_json_str(json: str, i: int) -> Tuple[str, int]:
    if json[i] != '"':
        raise SyntaxError(format_err_str(f"Unexpected character '{json[i]}' at position $position$. Expected '\"'", json, i))
    i += 1
    last_was_esc = False
    char_list = []
    hex_char_str = None
    try:
        while True:
            # current character
            c = json[i]
            i += 1
            # if in hexadecimal escape, use different logic
            if hex_char_str is not None:
                l = c.lower()
                if '0' <= l and '9' >= l or 'a' <= l and 'f' >= l:
                    hex_char_str += l
                else:
                    raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected a hexadecimal character ([0-9A-Fa-f])", json, i))
                if len(hex_char_str) == 4:
                    char_list.append(chr(int(hex_char_str, 16)))
                    hex_char_str = None
                continue
            if c == '"' and not last_was_esc:
                break

            if last_was_esc:
                # unescaped character sequence to append
                s = ''
                if c == 'b': s = '\b'
                elif c == 'f': s = '\f'
                elif c == 'n': s = '\n'
                elif c == 't': s = '\t'
                elif c == 'r': s = '\r'
                elif c == '/': s = '/'
                elif c == '"': s = '"'
                elif c == '\\': s = '\\'
                elif c == 'u': hex_char_str = ''
                else:
                    raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected 'b', 'f', 'n', 't', 'r', '/', '\\', or 'u'", json, i))
                if s: char_list.append(s)
                last_was_esc = False
                continue
            
            if c == '\\':
                last_was_esc = True
                continue
            # %x20-21 / %x23-5B / %x5D-10FFFF
            if not (c >= '\x20' and c <= '\x21' or c >= '\x23' and c <= '\x5b' or c >= '\x5d' and c <= '\U0010ffff'):
                raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected a character in the following ranges: %x20-21 / %x23-5B / %x5D-10FFFF", json, i))
            char_list.append(c)
    except IndexError:
        raise SyntaxError(f"Unexpected end of file at position {len(json)}")
    return (''.join(char_list), i)

def parse_json_number(json: str, i: int) -> Tuple[float, int]:
    ind = i
    while ind < len(json) and json[ind] in JSON_NUM_CHARS:
        ind += 1
    num = json[i:ind]
    negative = num.startswith('-')
    if len(num) == 0:
        raise SyntaxError(format_err_str(f"Unexpected empty number string at position $position$.", json, i))
    if negative:
        num = num[1:]
        i += 1
    if num.startswith('.'):
        raise SyntaxError(format_err_str(f"Unexpected decimal point at position $position$. Expected a digit beforehand", json, i))
    if len(num) >= 2 and num[0] == '0' and num[1] >= '0' and num[1] <= '9':
        raise SyntaxError(format_err_str(f"Unexpected digit following a zero at position $position$. Expected '.', 'e', 'E', or end of number", json, i + 1))

    reached_dec = False
    e_index = num.lower().index('e') if 'e' in num.lower() else len(num)
    before_e = num[:e_index]
    if before_e.endswith('.'):
        raise SyntaxError(format_err_str(f"Unexpected decimal point at position $position$. Expected no decimal point or a following digit", json, i + len(before_e) - 1))
    if len(before_e) == 0:
        raise SyntaxError(format_err_str(f"Unexpected end of non-exponent segment of number at $position$. Expected digits preceding exponent separator ('e' or 'E')", json, i))

    for c in before_e:
        if c == '.':
            if reached_dec:
                raise SyntaxError(format_err_str(f"Unexpected second decimal point at position $position$. Expected 0 or 1 decimal points", json, i))
            reached_dec = True
            i += 1
            continue
        if c < '0' or c > '9':
            raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected a digit", json, i))

    if e_index != len(num):
        i = e_index + 1
        after_e = num[e_index + 1:]
        if after_e.startswith('+') or after_e.startswith('-'):
            after_e = after_e[1:]
            i += 1
        if len(after_e) == 0:
            raise SyntaxError(format_err_str(f"Unexpected end of number at position $position$. Expected a digit", json, i))

        for c in after_e:
            if c < '0' or c > '9':
                raise SyntaxError(format_err_str(f"Unexpected character '{c}' at position $position$. Expected a digit", json, i))
            i += 1
    if negative: num = '-' + num
    return (float(num), ind)

def skip_whitespace(json: str, i: int) -> int:
    """Moves the cursor (starting at position `i`) until it hits a non-whitespace character.
    It then returns the new position of the cursor.
    """
    while i < len(json) and json[i] in JSON_WHITESPACE:
        i += 1
    return i

# Py -> JSON

def increase_indent(text: str, spaces: str) -> str:
    """Inserts the `spaces` string after each newline in `text`."""
    return text.replace("\n", "\n" + spaces)

def escape_str_for_json(string: str) -> str:
    """Formats and escapes characters in a Python string and returns it in the correct format for JSON."""
    string = string.replace('\\', '\\\\').replace('"', '\\"')
    string = string.replace('\n', '\\n').replace('\r', '\\r').replace('\b', '\\b').replace('\t', '\\t').replace('\f', '\\f')

    char_arr = []
    for char in string:
        n = ord(char)
        if n <= 0x1f or (n >= 0xd800 and n <= 0xdfff):
            char_arr.append(f"\\u{hex(n)[2:].rjust(4, '0')}")
        else:
            char_arr.append(char)
    return f'"{"".join(char_arr)}"'

def to_json(data: dict | list | str | int | float | bool | None, spaces: str | int = None) -> str:
    """Converts `data` to a JSON string, using the specified amount of spaces (or no spacing, if `None` is provided).
    If an integer is provided for `spaces`, it uses the space character repeated that amount of times as the spacing string.

    Can only convert dict, list, str, int, float, bool, and None values into JSON.
    """
    if isinstance(spaces, int): spaces = ' ' * spaces

    if data is None: return 'null' # None/null values
    elif isinstance(data, str): return escape_str_for_json(data) # strings
    elif isinstance(data, bool): return 'true' if data else 'false' # booleans
    elif isinstance(data, int) or isinstance(data, float): # numbers
        if not math.isfinite(data):
            raise TypeError(f"Cannot convert the value 'inf' or 'nan' to a JSON number")
        num = str(data)
        if num.endswith('.0'): num = num[:-2] # save a bit of space by chopping off the decimal point if it was added unnecessarily
        return num
    elif isinstance(data, dict): # objects
        keys = data.keys()
        if len(keys) == 0: return '{}' # empty
        str_arr = ['{']
        is_first = True
        for key in keys:
            # every comma must have at least one element before and after it
            if is_first: is_first = False
            else: str_arr.append(',')
            if spaces is not None: # line break in between elements is only added if spaces is not None
                str_arr.append('\n')
                str_arr.append(spaces)
            str_arr.append(escape_str_for_json(key))
            str_arr.append(':')

            if spaces is not None: str_arr.append(' ')

            stringified = to_json(data[key], spaces)
            str_arr.append(stringified if spaces is None else increase_indent(stringified, spaces))

        if spaces is not None: str_arr.append('\n')

        str_arr.append('}')
        return ''.join(str_arr)
    elif isinstance(data, list): # arrays
        if len(data) == 0: return '[]' # empty
        str_arr = ['[']
        is_first = True
        for val in data:
            # every comma must have at least one element before and after it
            if is_first: is_first = False
            else: str_arr.append(',')
            if spaces is not None: # line break in between elements is only added if spaces is not None
                str_arr.append('\n')
                str_arr.append(spaces)

            stringified = to_json(val, spaces)
            str_arr.append(stringified if spaces is None else increase_indent(stringified, spaces))

        if spaces is not None: str_arr.append('\n')

        str_arr.append(']')
        return ''.join(str_arr)
    else:
        raise TypeError(f"Argument 'data' must be a dict, list, int, float, str, bool, or None, not '{type(data).__name__}'")
