#!/usr/bin/env python3

import argparse
import base64
import os
import re
import subprocess
import sys
from io import StringIO

# --- CodeQuilt v0.2.1 Constants and Mappings ---

# Based on Spec v0.2.1 / EBNF v0.2.0 Illustrative Tokens (§5)
# NOTE: These are illustrative and language-dependent (Python focus here)
CQ_TO_PYTHON_KEYWORDS = {
    "D": "def",
    "C": "class",
    "R": "return",
    "?": "if",
    # ':' is tricky, used for else/elif/slice/type hint. Handled contextually.
    "F": "for",
    "W": "while",
    "T": "try",
    "X": "except",
    "Y": "finally",
    "M": "import", # Simplified - imports are complex
    "A": "await",
    "S": "async",
    "P": "pass",
    # Add more as needed based on actual CQ generation
    "E": "==",
    "G": ">=",
    "L": "<=",
    # Single char operators often map directly: =, +, -, *, /, %, >, <, ., (, ), [, ], {, }
}

PYTHON_TO_CQ_KEYWORDS = {v: k for k, v in CQ_TO_PYTHON_KEYWORDS.items()}

# --- Helper Functions ---

def parse_header(header_str):
    """Parses the CodeQuilt header string into a dictionary."""
    header_data = {}
    if not (header_str.startswith('[') and header_str.endswith(']')):
        raise ValueError("Invalid header format: Missing brackets.")
    
    content = header_str[1:-1]
    if not content:
        return header_data # Empty header is technically possible if spec allows

    fields = content.split(';')
    for field in fields:
        if not field: continue # Skip empty parts from potential double semicolons
        parts = field.split(':', 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid header field format: '{field}'")
        key, value = parts
        header_data[key.strip()] = value.strip()

    # Further parse dict and lit_dict
    if 'dict' in header_data:
        header_data['dict_map'] = parse_dict_field(header_data['dict'])
    if 'lit_dict' in header_data:
         header_data['lit_map'] = parse_lit_dict_field(header_data['lit_dict'])
    if 'imports' in header_data:
        header_data['import_list'] = parse_imports_field(header_data['imports'])

    return header_data

def parse_dict_field(dict_str):
    """Parses the dict field into a lookup map."""
    if not (dict_str.startswith('[') and dict_str.endswith(']')):
        raise ValueError("Invalid dict field format: Missing brackets.")
    content = dict_str[1:-1]
    d_map = {}
    if not content: return d_map
    
    entries = content.split(',')
    for entry in entries:
        entry = entry.strip()
        if not entry: continue
        parts = entry.split('=', 1)
        if len(parts) != 2 or not re.match(r'^d\d+$', parts[0]):
            raise ValueError(f"Invalid dict entry format: '{entry}'")
        d_map[parts[0]] = parts[1]
    return d_map

def parse_lit_dict_field(lit_dict_str):
    """Parses the lit_dict field into a lookup map with decoded literals."""
    if not (lit_dict_str.startswith('[') and lit_dict_str.endswith(']')):
        raise ValueError("Invalid lit_dict field format: Missing brackets.")
    content = lit_dict_str[1:-1]
    l_map = {}
    if not content: return l_map

    entries = content.split(',')
    for entry in entries:
        entry = entry.strip()
        if not entry: continue
        parts = entry.split('=', 1)
        if len(parts) != 2 or not re.match(r'^l\d+$', parts[0]):
             raise ValueError(f"Invalid lit_dict entry format: '{entry}'")
        try:
            # Base64 decode - must handle padding
            encoded = parts[1]
            # Add padding if necessary
            missing_padding = len(encoded) % 4
            if missing_padding:
                encoded += '=' * (4 - missing_padding)
            decoded_bytes = base64.b64decode(encoded)
            l_map[parts[0]] = decoded_bytes.decode('utf-8') # Assume UTF-8
        except (base64.binascii.Error, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode Base64 for {parts[0]}: {e}")
    return l_map

def parse_imports_field(imports_str):
    """Parses the imports field into a list."""
    if not (imports_str.startswith('[') and imports_str.endswith(']')):
        raise ValueError("Invalid imports field format: Missing brackets.")
    content = imports_str[1:-1]
    if not content: return []
    return [item.strip() for item in content.split(',') if item.strip()]

def format_python_code(code_string):
    """Formats Python code using black, if available."""
    try:
        process = subprocess.run(
            [sys.executable, '-m', 'black', '--quiet', '-'],
            input=code_string.encode('utf-8'),
            capture_output=True,
            check=True,
        )
        return process.stdout.decode('utf-8')
    except FileNotFoundError:
        print("Warning: 'black' formatter not found. Output may not be perfectly formatted.", file=sys.stderr)
        return code_string
    except subprocess.CalledProcessError as e:
        print(f"Warning: 'black' formatter failed: {e.stderr.decode()}", file=sys.stderr)
        return code_string
    except Exception as e:
        print(f"Warning: Error running 'black': {e}", file=sys.stderr)
        return code_string

# --- Core Conversion Functions ---

def codequilt_to_python(codequilt_string):
    """Converts a CodeQuilt string to Python source code."""
    if '|||' not in codequilt_string:
        raise ValueError("Invalid CodeQuilt format: Missing '|||' separator.")

    header_part, body_part = codequilt_string.split('|||', 1)
    
    try:
        header_data = parse_header(header_part)
    except ValueError as e:
        raise ValueError(f"Error parsing header: {e}")

    d_map = header_data.get('dict_map', {})
    l_map = header_data.get('lit_map', {})
    import_list = header_data.get('import_list', [])

    # Basic reconstruction logic
    output = StringIO()
    indent_level = 0
    indent_spaces = "    " # 4 spaces for Python
    needs_indent = True # Indent after newline
    
    # Prepend imports if any
    if import_list:
        for imp in import_list:
             # Heuristic: Assume simple 'import x' or 'import x as y'
            if " as " in imp:
                parts = imp.split(" as ")
                output.write(f"import {parts[0].strip()} as {parts[1].strip()}\n")
            else:
                 output.write(f"import {imp.strip()}\n")
        output.write("\n") # Add a blank line after imports

    # Simple body tokenizer
    i = 0
    while i < len(body_part):
        # Apply indentation if needed
        if needs_indent:
            output.write(indent_spaces * indent_level)
            needs_indent = False

        # Check for identifier/literal references first
        match_d = re.match(r'd(\d+)', body_part[i:])
        match_l = re.match(r'l(\d+)', body_part[i:])
        
        token_processed = False

        if match_d:
            d_key = f"d{match_d.group(1)}"
            if d_key in d_map:
                output.write(d_map[d_key])
                i += len(match_d.group(0))
                token_processed = True
            # else: Error? Fall through to treat 'd' as potential token?
        elif match_l:
            l_key = f"l{match_l.group(1)}"
            if l_key in l_map:
                # Need to represent the literal correctly (e.g., with quotes)
                # Heuristic: if it contains newlines, use triple quotes
                literal_content = l_map[l_key]
                if '\n' in literal_content:
                    # Escape triple quotes inside the literal if needed
                    escaped_content = literal_content.replace('"""', '\\"\\"\\"')
                    output.write(f'"""{escaped_content}"""')
                else:
                     # Simple quotes, escape appropriately
                    output.write(repr(literal_content)) # repr() handles quotes and escapes well
                i += len(match_l.group(0))
                token_processed = True
            # else: Error? Fall through

        if token_processed:
            # Add heuristic space after identifiers/literals if needed before operators etc.
            # This is complex; relying on black is better.
             if i < len(body_part) and body_part[i] not in '().[]{},:;':
                 output.write(' ')
             continue

        # Check for single/double char tokens
        char = body_part[i]
        next_char = body_part[i+1] if i+1 < len(body_part) else None
        
        processed_len = 1 # Default length of token processed

        if char == 'N':
            output.write('\n')
            needs_indent = True
        elif char == 'I' and next_char == '+':
            indent_level += 1
            processed_len = 2
            # Don't write anything, affects next line's indent
        elif char == 'I' and next_char == '-':
            if indent_level > 0:
                indent_level -= 1
            processed_len = 2
            # Don't write anything, affects next line's indent
        elif char == "'": # String literal
            start = i
            i += 1
            str_content = ""
            while i < len(body_part):
                if body_part[i] == '\\' and i + 1 < len(body_part):
                    str_content += body_part[i:i+2] # Keep escape sequence
                    i += 2
                elif body_part[i] == "'":
                    i += 1 # Consume closing quote
                    break
                else:
                    str_content += body_part[i]
                    i += 1
            else:
                 raise ValueError(f"Unterminated single-quoted string starting at index {start}")
            output.write(f"'{str_content}'") # Write including quotes
            processed_len = 0 # i is already advanced
        elif char == '"': # Double-quoted string literal (similar logic)
            start = i
            i += 1
            str_content = ""
            while i < len(body_part):
                if body_part[i] == '\\' and i + 1 < len(body_part):
                    str_content += body_part[i:i+2]
                    i += 2
                elif body_part[i] == '"':
                    i += 1
                    break
                else:
                    str_content += body_part[i]
                    i += 1
            else:
                raise ValueError(f"Unterminated double-quoted string starting at index {start}")
            output.write(f'"{str_content}"')
            processed_len = 0
        elif char in CQ_TO_PYTHON_KEYWORDS:
            py_keyword = CQ_TO_PYTHON_KEYWORDS[char]
            output.write(py_keyword)
            # Add space after keywords if needed (heuristic)
            if i + processed_len < len(body_part) and body_part[i + processed_len] not in '().:':
                 output.write(' ')
        elif char == 't': # boolean True
            output.write("True ")
        elif char == 'f': # boolean False
            output.write("False ")
        elif char == 'n': # None
            output.write("None ")
        elif char == '#': # Comment
             # Assume comment content is a string literal following '#'
             if next_char == "'":
                 i += 1 # Move to start of string
                 start = i
                 i += 1
                 str_content = ""
                 while i < len(body_part):
                    if body_part[i] == '\\' and i + 1 < len(body_part):
                        str_content += body_part[i:i+2] # Keep escape sequence
                        i += 2
                    elif body_part[i] == "'":
                        i += 1 # Consume closing quote
                        break
                    else:
                        str_content += body_part[i]
                        i += 1
                 else:
                      raise ValueError(f"Unterminated comment string starting at index {start}")
                 output.write(f'# {str_content}') # Add space after #
                 processed_len = 0 # i is already advanced
             else:
                  # Simple '#' might be used directly? Add fallback.
                  output.write(char)
        elif char.isdigit() or (char in '+-' and next_char and next_char.isdigit()): # Number literal
             num_match = re.match(r'[+-]?\d+(\.\d+)?', body_part[i:])
             if num_match:
                 num_str = num_match.group(0)
                 output.write(num_str)
                 output.write(' ') # Heuristic space
                 processed_len = len(num_str)
             else: # Fallback if match fails unexpectedly
                 output.write(char)
        elif char.isspace(): # Skip whitespace between tokens in body
            pass
        else:
            # Assume other chars are operators/delimiters that map directly
            # Handle potential multi-char operators if needed (e.g., **, //, >=, <=, ==)
            # Basic: map single chars
            output.write(char)
            # Add heuristic spacing around operators (complex, rely on black)
            if char in '+-*/%=&|<>':
                output.write(' ')
            elif char in '[](){}.,:;':
                 pass # Usually no space needed after these
                 
        if processed_len > 0:
           i += processed_len

    reconstructed_code = output.getvalue()
    
    # Optionally format with black
    return format_python_code(reconstructed_code)


def python_to_codequilt(python_code):
    """
    Converts Python source code to a CodeQuilt string.
    
    NOTE: This is a placeholder. A full implementation requires
    parsing Python code using AST/tokenize, which is complex.
    This function demonstrates the intended structure but not the full logic.
    """
    print("Warning: python_to_codequilt conversion is complex and only implemented as a placeholder.", file=sys.stderr)
    
    # --- Placeholder / Basic Example ---
    # 1. Identify Identifiers & Literals (Requires parsing)
    # Example: identifiers = {"my_var": "d0", "print": "d1"}
    # Example: literals = {"Hello": "l0"} # Base64('Hello') -> SGVsbG8=

    # 2. Build Header
    version = "0.2.1"
    lang = "python-3.11" # Example
    # Example dict_str = "dict:[d0=my_var,d1=print]"
    # Example lit_dict_str = "lit_dict:[l0=SGVsbG8=]"
    # Example header = f"[v:{version};lang:{lang};{dict_str};{lit_dict_str}]"
    header = f"[v:{version};lang:{lang};dict:[d0=example,d1=print];lit_dict:[l0=IkhlbGxvLCBXb3JsZCEi]]" # Placeholder header

    # 3. Build Body (Requires tokenizing and mapping)
    # Example: body = "d1(l0)" # for print("Hello, World!") after mapping
    body = "d1(l0)N" # Placeholder body

    return header + "|||" + body
    # raise NotImplementedError("Python-to-CodeQuilt conversion requires a full Python parser (AST/tokenize).")


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(
        description="Convert between Python (.py) and CodeQuilt (.cq) files.",
        epilog="Based on CodeQuilt Spec v0.2.1. Note: .py -> .cq conversion is a complex placeholder."
    )
    parser.add_argument("input_file", help="Path to the input file (.py or .cq)")

    args = parser.parse_args()

    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    base, ext = os.path.splitext(input_path)
    ext = ext.lower()

    output_path = None
    result_content = None

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()

        if ext == '.py':
            print(f"Converting Python (.py) to CodeQuilt (.cq)...")
            output_path = base + ".cq"
            result_content = python_to_codequilt(input_content)
            print(f"Note: Python-to-CodeQuilt is a placeholder implementation.")

        elif ext == '.cq':
            print(f"Converting CodeQuilt (.cq) to Python (.py)...")
            output_path = base + ".py"
            result_content = codequilt_to_python(input_content)

        else:
            print(f"Error: Unsupported file extension '{ext}'. Please use '.py' or '.cq'.", file=sys.stderr)
            sys.exit(1)

        if output_path and result_content is not None:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result_content)
            print(f"Successfully saved result to: {output_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error processing {input_path}: {e}", file=sys.stderr)
        sys.exit(1)
    except NotImplementedError as e:
         print(f"Error: {e}", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()