"""
A module for converting CSV text into a 2d list of strings and vice versa.

To convert CSV to Python, use the parse_csv function. To convert Python to CSV, use the strs_to_csv function.
"""

from __future__ import annotations
from typing import Tuple

def parse_csv(csv: str, quote_char: str = '"', comma_char: str = ',', new_line_char: str = '\n') -> list[list[str]]:
    """
    Takes in the contents of a CSV file as a string and returns its parsed contents as a 2d array of strings.
    """
    # List of all rows
    lines = []
    # List of strings representing the current row being parsed
    current_row = []
    
    # Whether or not the cursor is inside a cell
    out_of_cell = True
    # The index of the start of the current cell
    cell_start_ind = 0
    # Whether or not the cell started with a quote
    cell_is_quoted = False
    # True if the last character was a quote and was not the start of a quoted cell
    last_was_quote = False

    # Iterates over each character in the CSV string
    for i in range(len(csv)):
        c = csv[i]
        # Whether or not the current character is a possible cell end character
        could_be_cell_end = (c == comma_char or c == new_line_char)

        # Update state to be inside of a cell
        if out_of_cell:
            out_of_cell = False
            cell_start_ind = i
            last_was_quote = False
            cell_is_quoted = c == quote_char
            # if check is necessary so that empty cells (e.g. `,,`) can be parsed correctly
            if not could_be_cell_end:
                continue

        # Syntax check to make sure that quotes are not included in unquoted cells
        if not cell_is_quoted and c == quote_char:
            (line, col) = get_line_and_col(csv, i)
            raise SyntaxError(f"Unexpected quote in CSV at position {i} (row: {len(lines)}, cell: {len(current_row)}, line: {line}, col: {col})")

        # Handle double-quote escaping
        if cell_is_quoted and last_was_quote and not could_be_cell_end:
            if c == quote_char:
                last_was_quote = False
                continue
            else:
                # Throw on single quotes not followed by a newline, comma, or end of file
                (line, col) = get_line_and_col(csv, i)
                raise SyntaxError(f"Expected comma, new line, or quote following another quote at position {i} (row: {len(lines)}, cell: {len(current_row)}, line: {line}, col: {col})")
        # End cell
        if (last_was_quote if cell_is_quoted else True) and could_be_cell_end:
            out_of_cell = True
            last_was_quote = False

            # Grab cell text
            cell_text = csv[cell_start_ind : i]
            # Unescape cell if necessary
            if cell_is_quoted:
                cell_text = unescape_csv_cell(cell_text)

            current_row.append(cell_text)
            # If the cell ends on a newline, not a comma, end current row
            if c == new_line_char:
                lines.append(current_row)
                current_row = []
            cell_is_quoted = False
            continue

        # Part of double-quote escaping handling
        if cell_is_quoted and c == quote_char:
            last_was_quote = True
        else:
            last_was_quote = False

    # Handle trailing cells
    if cell_is_quoted:
        # quoted cells
        if last_was_quote:
            current_row.append(unescape_csv_cell(csv[cell_start_ind:]))
        else:
            raise SyntaxError(f"Unexpected end of input in CSV, expected quote at position {len(csv)} (End Of File)")
    elif not out_of_cell:
        # unquoted cells
        current_row.append(csv[cell_start_ind:])
    elif csv.endswith(comma_char):
        # empty cells
        current_row.append('')

    # If the current row list has elements in it, add it to the lines list
    if len(current_row):
        lines.append(current_row)

    return lines

def unescape_csv_cell(cell: str):
    """
    Converts a single, escaped CSV cell to plain, unescaped text
    """
    return cell.strip('"').replace('""', '"')

def get_line_and_col(text: str, index: int) -> Tuple[int, int]:
    """
    Takes in a string and an index and returns the line and column (zero-indexed)
    referenced by the index parameter, in the form (line, col)
    """
    line_count = 0
    last_line_index = 0
    for i in range(0, index):
        if text[i] == '\n':
            line_count += 1
            last_line_index = i
    return (line_count, index - last_line_index)

# Encoding CSV

def strs_to_csv(csv: list[list[str]], quote_char: str = '"', comma_char: str = ',', new_line_char: str = '\n') -> str:
    """
    Escapes and formats the given 2d list of strings into the CSV format.
    """
    rows = [comma_char.join([str_to_csv(cell, quote_char, comma_char, new_line_char) for cell in row]) for row in csv]
    return new_line_char.join(rows)

def str_to_csv(csv: str, quote_char: str, comma_char: str, new_line_char: str) -> str:
    """
    Escapes a single string (if necessary) to be a single cell in the CSV format.
    It will wrap the string with quotes and escape it if it contains the given quote,
    comma, or newline character.
    """
    if quote_char in csv or comma_char in csv or new_line_char in csv:
        csv = '"' + csv.replace('"', '""') + '"'
    return csv
