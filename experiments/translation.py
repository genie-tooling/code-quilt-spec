#!/usr/bin/env python3

import argparse
import base64
import os
import re
import subprocess
import sys
from io import StringIO
import json # Using json for easier parsing of bracketed lists/dicts initially

# --- CodeQuilt v0.7.1-semantic-py3.11-std25-v1 Constants ---

SPEC_VERSION = "0.7.1-semantic-py3.11-std25-v1"
DEFAULT_LITERAL_THRESHOLD = 80

# Implied Corpus Dictionary (C) for the specified version
# (Truncated for brevity - use the full list from the spec in production)
CORPUS_DICT = {
    "c0": "Exception", "c1": "AttributeError", "c2": "IndexError", "c3": "KeyError",
    "c4": "ValueError", "c5": "TypeError", "c6": "ImportError", "c7": "ModuleNotFoundError",
    "c8": "FileNotFoundError", "c9": "NotImplementedError", "c10": "RuntimeError",
    "c11": "OSError", "c12": "sqlite3", "c13": "JSONDecodeError", "c14": "StopIteration",
    "c15": "BaseException", "c16": "LookupError", "c17": "AssertionError", "c18": "UnicodeError",
    "c19": "UnicodeDecodeError", "c20": "ConnectionError", "c21": "TimeoutError",
    "c22": "PermissionError", "c23": "ReferenceError", "c24": "SyntaxError",
    "c25": "IndentationError", "c26": "SystemError", "c27": "RecursionError",
    "c28": "return", "c29": "import", "c30": "except", "c31": "finally",
    "c32": "lambda", "c33": "assert", "c34": "global", "c35": "yield",
    "c36": "async", "c37": "await", "c38": "class", "c39": "continue",
    "c40": "isinstance", "c41": "getattr", "c42": "setattr", "c43": "hasattr",
    "c44": "enumerate", "c45": "filter", "c46": "sorted", "c47": "property",
    "c48": "classmethod", "c49": "staticmethod", "c50": "__init__",
    "c51": "__repr__", "c52": "__str__", "c53": "__call__", "c54": "__getitem__",
    "c55": "__setitem__", "c56": "__delitem__", "c57": "__contains__",
    "c58": "__enter__", "c59": "__exit__", "c60": "__iter__", "c61": "__next__",
    "c62": "append", "c63": "extend", "c64": "insert", "c65": "remove",
    "c66": "reverse", "c67": "update", "c68": "values", "c69": "items",
    "c70": "popitem", "c71": "setdefault", "c72": "discard", "c73": "startswith",
    "c74": "endswith", "c75": "replace", "c76": "strip", "c77": "split",
    "c78": "join", "c79": "format", "c80": "encode", "c81": "decode",
    "c82": "streamlit", "c83": "session_state", "c84": "sidebar", "c85": "button",
    "c86": "text_input", "c87": "text_area", "c88": "slider", "c89": "selectbox",
    "c90": "toggle", "c91": "expander", "c92": "markdown", "c93": "caption",
    "c94": "warning", "c95": "success", "c96": "toast", "c97": "spinner",
    "c98": "rerun", "c99": "chat_message", "c100": "chat_input", "c101": "columns",
    "c102": "container", "c103": "set_page_config", "c104": "logging",
    "c105": "logger", "c106": "getLogger", "c107": "basicConfig",
    "c108": "FileHandler", "c109": "StreamHandler", "c110": "setLevel",
    "c111": "datetime", "c112": "timedelta", "c113": "fromisoformat",
    "c114": "strftime", "c115": "pathlib", # Assuming os.path or pathlib context
    "c116": "resolve", "c117": "exists", "c118": "is_file", "c119": "is_dir",
    "c120": "read_text", "c121": "mkdir", # often used with exist_ok=True
    "c122": "connect", "c123": "cursor", "c124": "execute", "c125": "fetchone",
    "c126": "fetchall", "c127": "commit", "c128": "rollback", "c129": "lastrowid",
    "c130": "rowcount", "c131": "contextlib", "c132": "contextmanager",
    "c133": "loads", "c134": "dumps", "c135": "google", "c136": "generativeai",
    "c137": "configure", "c138": "list_models", "c139": "get_model",
    "c140": "GenerativeModel", "c141": "GenerationConfig", "c142": "generate_content",
    "c143": "start_chat", "c144": "send_message", "c145": "count_tokens",
    "c146": "safety_settings", "c147": "candidates", "c148": "prompt_feedback",
    "c149": "block_reason", "c150": "citation_metadata", "c151": "citation_sources",
    "c152": "grounding_metadata", "c153": "web_search_results", "c154": "search_entry_point",
    "c155": "rendered_content", "c156": "GoogleSearchRetrieval", "c157": "dynamic_retrieval_config",
    "c158": "dynamic_threshold", "c159": "disable_attribution", "c160": "database",
    "c161": "manager", "c162": "context_manager", "c163": "actions",
    "c164": "requests", "c165": "response", "c166": "session", "c167": "collections",
    "c168": "defaultdict", "c169": "OrderedDict", "c170": "Counter", "c171": "deque",
    "c172": "namedtuple", "c173": "argparse", "c174": "ArgumentParser",
    "c175": "add_argument", "c176": "parse_args", "c177": "subprocess",
    "c178": "communicate", "c179": "unittest", "c180": "TestCase",
    "c181": "assertEqual", "c182": "assertTrue", "c183": "assertFalse",
    "c184": "assertRaises", "c185": "threading", "c186": "Thread",
    "c187": "Condition", "c188": "Semaphore", "c189": "multiprocessing",
    "c190": "Process", "c191": "Queue", "c192": "Pool", "c193": "shutil",
    "c194": "copy", "c195": "move", "c196": "rmtree", "c197": "pickle",
    "c198": "struct", "c199": "socket", "c200": "asyncio", "c201": "gather",
    "c202": "create_task", "c203": "run_until_complete", "c204": "sleep",
    "c205": "wait", "c206": "warnings", "c207": "warn", "c208": "simplefilter",
    "c209": "traceback", "c210": "format_exc", "c211": "print_exc", "c212": "inspect",
    "c213": "getmembers", "c214": "signature", "c215": "Parameter", "c216": "functools",
    "c217": "partial", "c218": "lru_cache", "c219": "wraps", "c220": "operator",
    "c221": "itemgetter", "c222": "attrgetter", "c223": "methodcaller",
    "c224": "tempfile", "c225": "NamedTemporaryFile", "c226": "TemporaryDirectory",
    "c227": "itertools", "c228": "product", "c229": "permutations",
    "c230": "combinations", "c231": "chain", "c232": "message", "c233": "content",
    "c234": "conversation", "c235": "metadata", "c236": "timestamp",
    "c237": "instruction", "c238": "parameter", "c239": "context",
    "c240": "history", "c241": "variable", "c242": "argument",
    "c243": "function", "c244": "module", "c245": "package", "c246": "default",
    "c247": "result", "c248": "status", "c249": "client", "c250": "server",
    "c251": "request",
    # Add c252 onwards if needed
}

# Fixed Token Mappings (CodeQuilt -> Python) based on Spec v0.7.1 / Reduced Spec
# Using the reduced spec's map as it seems more concrete.
FIXED_TOKEN_MAP = {
    # Structure
    'N': '\n', '>': '_INDENT_', '<': '_DEDENT_',
    '(': '(', ')': ')', '[': '[', ']': ']', '{': '{', '}': '}',
    ',': ',', ':': ':', '.': '.', ';': ';',
    # Operators
    '=': '=', '+': '+', '-': '-', '*': '*', '/': '/', '%': '%',
    '&': ' and ', '|': ' or ', '^': ' ^ ', # XOR often needs spaces, pow is **
    '~': ' is ', # requires spaces
    '<': '<', '>': '>',
    '!': ' not ', # requires spaces (logical not)
    '@': ' in ', # requires spaces
    # Keywords (Uppercase)
    'D': 'def', 'C': 'class', 'R': 'return', '?': 'if', 'T': 'try',
    'X': 'except', 'Y': 'finally', 'P': 'pass', 'M': 'import', 'J': 'from',
    'E': 'elif', 'B': 'break', 'K': 'continue', 'Q': 'del', 'A': 'await',
    'S': 'async', 'U': 'raise', 'Z': 'assert', 'W': 'with', 'G': 'global',
    'L': 'lambda',
    # Literals
    't': 'True', 'f': 'False', 'n': 'None',
}

# Pre-compiled regex for efficiency
# Basic C/D/L references
RE_REF = re.compile(r"([cdl])(\d+)")
# Semantic tokens (simple name capture)
RE_SEMANTIC_START = re.compile(r"([A-Z][A-Z0-9_]+)\(")
# Numbers (int/float)
RE_NUMBER = re.compile(r"[+-]?\d+(\.\d+)?")
# Identifiers (for basic validation where needed)
RE_IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
# Escape hatch L'{...}'
RE_ESCAPE_HATCH = re.compile(r"L'{(.*?)}'", re.DOTALL) # Non-greedy match

class CodeQuiltDecodeError(ValueError):
    """Custom exception for decoding errors."""
    pass

class CodeQuiltDecoder:
    """Decodes a CodeQuilt v0.7.1 string into Python code."""

    def __init__(self, codequilt_string):
        self.codequilt_string = codequilt_string
        self.header = {}
        self.body = ""
        self.dynamic_map = {}
        self.literal_map = {}
        self.options = {}
        self.literal_threshold = DEFAULT_LITERAL_THRESHOLD
        self.keep_comments = False
        self.indent_level = 0
        self.indent_spaces = "    " # Standard Python indent
        self.output = StringIO()
        self.needs_indent = False
        self.pos = 0 # Current position in the body string

    def _parse_header_list_or_dict(self, field_value, entry_sep=',', kv_sep='='):
        """Helper to parse bracketed, separated lists or dicts from header."""
        if not (field_value.startswith('[') and field_value.endswith(']')):
            raise CodeQuiltDecodeError(f"Invalid field format: Missing brackets in '{field_value}'")
        content = field_value[1:-1].strip()
        if not content:
            return {} if kv_sep else []

        entries = content.split(entry_sep)
        if kv_sep:
            result_map = {}
            for entry in entries:
                entry = entry.strip()
                if not entry: continue
                parts = entry.split(kv_sep, 1)
                if len(parts) != 2:
                    raise CodeQuiltDecodeError(f"Invalid key-value entry format: '{entry}'")
                result_map[parts[0].strip()] = parts[1].strip()
            return result_map
        else:
            return [item.strip() for item in entries if item.strip()]

    def _parse_header(self, header_str):
        """Parses the CodeQuilt header string."""
        if not (header_str.startswith('[') and header_str.endswith(']')):
            raise CodeQuiltDecodeError("Invalid header format: Missing brackets.")

        content = header_str[1:-1]
        if not content:
            raise CodeQuiltDecodeError("Header cannot be empty (must contain V:).")

        fields = content.split(';')
        header_data = {}
        for field in fields:
            if not field: continue
            parts = field.split(':', 1)
            if len(parts) != 2:
                raise CodeQuiltDecodeError(f"Invalid header field format: '{field}'")
            key, value = parts[0].strip(), parts[1].strip()
            header_data[key] = value

        # Validate required V field
        if 'V' not in header_data:
            raise CodeQuiltDecodeError("Missing required header field: V")
        if header_data['V'] != SPEC_VERSION:
             print(f"Warning: Header version '{header_data['V']}' does not match tool's expected version '{SPEC_VERSION}'. Proceeding with caution.", file=sys.stderr)
             # Allow processing but warn. For strict mode, raise error here.

        self.header = header_data

        # Parse D: field
        if 'D' in self.header:
            d_entries = self._parse_header_list_or_dict(self.header['D'])
            for key, val in d_entries.items():
                if not re.fullmatch(r"d\d+", key):
                    raise CodeQuiltDecodeError(f"Invalid dynamic dictionary key: {key}")
                if not re.fullmatch(RE_IDENTIFIER, val):
                     print(f"Warning: Dynamic dictionary value '{val}' for key '{key}' may not be a standard Python identifier.", file=sys.stderr)
                self.dynamic_map[key] = val

        # Parse X: field
        if 'X' in self.header:
            x_entries = self._parse_header_list_or_dict(self.header['X'])
            for key, b64_val in x_entries.items():
                if not re.fullmatch(r"l\d+", key):
                    raise CodeQuiltDecodeError(f"Invalid literal dictionary key: {key}")
                try:
                    # Add padding if necessary before decoding
                    missing_padding = len(b64_val) % 4
                    if missing_padding:
                        b64_val += '=' * (4 - missing_padding)
                    decoded_bytes = base64.b64decode(b64_val, validate=True)
                    self.literal_map[key] = decoded_bytes.decode('utf-8') # Assume UTF-8
                except (base64.binascii.Error, UnicodeDecodeError, ValueError) as e:
                    raise CodeQuiltDecodeError(f"Failed to decode Base64 for {key}: {e}")

        # Parse O: field
        if 'O' in self.header:
            o_entries = self._parse_header_list_or_dict(self.header['O'], kv_sep=None) # Treat as list first
            for entry in o_entries:
                if '=' in entry:
                    opt_key, opt_val = entry.split('=', 1)
                    self.options[opt_key] = opt_val
                else:
                    self.options[entry] = True # Flag options

            if 'lth' in self.options:
                try:
                    self.literal_threshold = int(self.options['lth'])
                except ValueError:
                    raise CodeQuiltDecodeError(f"Invalid value for option lth: {self.options['lth']}")
            if self.options.get('cmt') == 'k':
                self.keep_comments = True

        # Parse I: field (store for potential future use/info)
        if 'I' in self.header:
            self.header['import_list'] = self._parse_header_list_or_dict(self.header['I'], kv_sep=None)

        # Parse C: field (store for potential future use/verification)
        if 'C' in self.header:
            if '-' not in self.header['C']:
                 raise CodeQuiltDecodeError(f"Invalid checksum format: {self.header['C']}")
            # Further validation could check algo/hash format

    def _write(self, text):
        """Writes text to output, handling indentation."""
        if self.needs_indent:
            self.output.write(self.indent_spaces * self.indent_level)
            self.needs_indent = False
        self.output.write(text)

    def _write_token(self, token_text, spacing='heuristic'):
        """Writes a token with potential spacing."""
        # Basic heuristic: Add space after keywords/identifiers/literals
        # if followed by another identifier/keyword/literal/some operators.
        # Rely mostly on black formatter.
        space_before = False
        space_after = False

        last_char = self.output.getvalue()[-1:] if self.output.tell() > 0 else ''

        # Crude spacing - black formatter is preferred
        if spacing == 'heuristic':
             is_alphanum_token = token_text[0].isalnum() or token_text[0]=='_'
             is_symbol = not is_alphanum_token and token_text not in ['\n','_INDENT_','_DEDENT_']

             if is_alphanum_token and last_char.isalnum():
                 space_before = True
             elif is_symbol and token_text in '+-*/%<>=&|~!' and last_char.isalnum():
                 space_before = True
             elif is_alphanum_token and last_char in '+-*/%<>=&|~!':
                 space_before = True


             if space_before:
                 self._write(" ")
             self._write(token_text)

             # Space after most keywords/operators
             if token_text in ['def', 'class', 'return', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with', 'import', 'from', 'await', 'async', 'raise', 'assert', 'global', 'lambda', 'yield', 'and', 'or', 'not', 'is', 'in'] \
                or token_text in FIXED_TOKEN_MAP.values() and token_text.strip() in '+-*/%=<>!&|~^':
                 self._write(" ")

        elif spacing == 'literal':
             # Space before if last char was alphanumeric
             if last_char.isalnum():
                  self._write(" ")
             self._write(token_text)
             # Space after unless followed by ), ], }, ,, :, ;
             self._write(" ") # Over-generous space, let black fix

        elif spacing == 'none':
             self._write(token_text)


    def _peek(self, length=1):
        """Peek ahead in the body string."""
        if self.pos + length <= len(self.body):
            return self.body[self.pos : self.pos + length]
        return None

    def _consume(self, length=1):
        """Consume characters from the body string."""
        consumed = self.body[self.pos : self.pos + length]
        self.pos += length
        return consumed

    def _parse_string_literal(self, quote_char):
        """Parses an inline string literal from the body."""
        start_pos = self.pos - 1 # Already consumed the opening quote
        content = StringIO()
        while self.pos < len(self.body):
            char = self._consume()
            if char == '\\':
                if self.pos < len(self.body):
                    escaped = self._consume()
                    # Handle standard Python escapes
                    if escaped == 'n': content.write('\n')
                    elif escaped == 't': content.write('\t')
                    elif escaped == 'r': content.write('\r')
                    elif escaped == 'b': content.write('\b')
                    elif escaped == 'f': content.write('\f')
                    elif escaped == '\\': content.write('\\')
                    elif escaped == "'": content.write("'")
                    elif escaped == '"': content.write('"')
                    elif escaped == 'u': # Basic unicode \uXXXX
                        if self.pos + 4 <= len(self.body):
                             hex_code = self._peek(4)
                             if all(c in '0123456789abcdefABCDEF' for c in hex_code):
                                 content.write(chr(int(hex_code, 16)))
                                 self._consume(4)
                             else:
                                 # Not a valid hex escape, treat literally? Or error?
                                 # Spec implies valid escapes. Let's be strict.
                                 raise CodeQuiltDecodeError(f"Invalid unicode escape sequence at pos {self.pos}")
                        else:
                            raise CodeQuiltDecodeError(f"Incomplete unicode escape sequence at pos {self.pos}")
                    # Add other escapes (\N{...}, \xHH, octal) if spec requires
                    else:
                        # Unknown escape, treat literally? Or error? Spec implies standard.
                        # For now, let's assume it shouldn't happen per spec.
                        raise CodeQuiltDecodeError(f"Unsupported escape sequence '\\{escaped}' at pos {self.pos-1}")
                else:
                    raise CodeQuiltDecodeError(f"Dangling escape character at end of body")
            elif char == quote_char:
                full_literal = quote_char + content.getvalue() + quote_char
                if len(full_literal) - 2 > self.literal_threshold: # Check length constraint
                     print(f"Warning: Inline string literal '{full_literal[:20]}...' exceeds threshold {self.literal_threshold} at pos {start_pos}", file=sys.stderr)
                return full_literal # Return with original quotes
            else:
                content.write(char)
        raise CodeQuiltDecodeError(f"Unterminated string literal starting at pos {start_pos}")

    def _parse_bytes_literal(self, quote_char):
        """Parses an inline bytes literal."""
        # Similar logic to _parse_string_literal but returns bytes repr
        start_pos = self.pos - 2 # Consumed b' or b"
        content = StringIO() # Store raw string content first
        while self.pos < len(self.body):
            char = self._consume()
            if char == '\\':
                 if self.pos < len(self.body):
                    escaped = self._consume()
                    # Bytes escapes are different (\xHH is common)
                    if escaped == 'x':
                         if self.pos + 2 <= len(self.body):
                             hex_code = self._peek(2)
                             if all(c in '0123456789abcdefABCDEF' for c in hex_code):
                                 content.write(f'\\x{hex_code}')
                                 self._consume(2)
                             else:
                                  raise CodeQuiltDecodeError(f"Invalid hex escape sequence \\x{hex_code} at pos {self.pos}")
                         else:
                              raise CodeQuiltDecodeError(f"Incomplete hex escape sequence at pos {self.pos}")
                    # Handle other valid bytes escapes (\', \", \\, \n, \r, \t, \b, \f)
                    elif escaped in "'\"\\nrtbf":
                         content.write(f'\\{escaped}')
                    # Octal escapes (\ooo) could be added if needed
                    else:
                         # Treat other escapes literally within bytes? Python does.
                         content.write(f'\\{escaped}')
                 else:
                      raise CodeQuiltDecodeError(f"Dangling escape character at end of body")

            elif char == quote_char:
                 # Construct the final representation 'b"..."' or b'...'
                 final_repr = f"b{quote_char}{content.getvalue()}{quote_char}"
                 if len(final_repr) - 3 > self.literal_threshold:
                     print(f"Warning: Inline bytes literal '{final_repr[:20]}...' exceeds threshold {self.literal_threshold} at pos {start_pos}", file=sys.stderr)
                 return final_repr # Return the Python literal representation
            else:
                 # Check if char needs escaping in bytes literal context (e.g. non-ASCII)
                 # For simplicity, assume input CodeQuilt uses valid ASCII or escapes
                 content.write(char)
        raise CodeQuiltDecodeError(f"Unterminated bytes literal starting at pos {start_pos}")


    def _parse_semantic_token(self, name):
        """Parses parameters and potential body of a semantic token."""
        # Expects '(' to be consumed already
        params = []
        body_tokens = None

        # Parse parameters until ')' or ':{'
        while self.pos < len(self.body):
             # Need to parse the *next* full token to be a parameter
             param_token = self._parse_next_token(in_semantic_param=True)
             if param_token is None: # End of body unexpectedly
                 raise CodeQuiltDecodeError(f"Unterminated parameter list for semantic token {name}")

             params.append(param_token) # Store the raw token structure

             # Check for separators or end
             next_char = self._peek()
             if next_char == ':':
                 self._consume() # Consume ':' separator
                 # Check if followed by '{' indicating a body block
                 if self._peek() == '{':
                      self._consume() # Consume '{'
                      # Now parse the body tokens until '}'
                      body_tokens_list = []
                      nesting_level = 1
                      while self.pos < len(self.body):
                          # Important: Need to handle nested structures correctly
                          if self._peek() == '{': nesting_level += 1
                          elif self._peek() == '}':
                              nesting_level -= 1
                              if nesting_level == 0:
                                  self._consume() # Consume final '}'
                                  break # End of body block
                          # Parse the next token *within* the block
                          # This recursive call needs careful state management if done properly
                          # Simpler: capture the raw string segment for now
                          # TODO: Implement proper nested parsing if needed.
                          # For PoC, let's assume simple bodies or handle specific cases
                          tok = self._parse_next_token(in_semantic_body=True)
                          if tok is None: break # End of input
                          body_tokens_list.append(tok) # Append raw token structure
                      else: # Loop finished without finding closing '}'
                          raise CodeQuiltDecodeError(f"Unterminated body block {{...}} for semantic token {name}")
                      body_tokens = body_tokens_list # Store list of token structures
                      # After body block, expect ')'
                      if self._peek() == ')':
                          self._consume()
                          return name, params, body_tokens
                      else:
                          raise CodeQuiltDecodeError(f"Expected ')' after body block {{...}} in semantic token {name}")
                 else:
                      continue # Just a parameter separator, continue parsing params
             elif next_char == ')':
                  self._consume() # Consume ')'
                  return name, params, body_tokens # No body block
             else:
                 # Might allow whitespace between param and separator? Spec says ignore WS between tokens.
                 # Let's assume separators follow immediately or after WS handled by main loop.
                 # If we are here, something is wrong (e.g., missing separator or ')')
                  raise CodeQuiltDecodeError(f"Expected ':' or ')' after parameter in semantic token {name}, got '{next_char}'")

        raise CodeQuiltDecodeError(f"Unterminated parameter list or body for semantic token {name}")

    def _expand_semantic_token(self, name, params, body_tokens):
        """Expands a parsed semantic token into Python code."""
        # Requires resolving the parameter tokens first
        resolved_params = [self._resolve_token_value(p) for p in params]

        # Implement expansion logic based on the spec's definitions
        # This needs to be robust and handle parameter substitution correctly.

        # Example Expansions (based on reduced spec):
        if name == "LOG":
            if len(resolved_params) < 2: raise CodeQuiltDecodeError("LOG needs at least level and format string")
            lvl_map = {'i': 'info', 'd': 'debug', 'e': 'error', 'w': 'warning', 'c': 'critical'}
            level = lvl_map.get(resolved_params[0])
            if not level: raise CodeQuiltDecodeError(f"Invalid LOG level: {resolved_params[0]}")
            fmt = resolved_params[1]
            args = resolved_params[2:]
            args_str = ", ".join(args)
            self._write_token(f"{CORPUS_DICT['c105']}.{level}({fmt}" + (f", {args_str}" if args_str else "") + ")", spacing='none')

        elif name == "ATTR":
             if len(resolved_params) != 3: raise CodeQuiltDecodeError("ATTR needs object, attribute, and value")
             obj, attr, val = resolved_params
             # Need to be careful if attr is a plain string or ref
             # Assuming params are resolved to Python code snippets here
             self._write_token(f"{obj}.{attr} = {val}", spacing='none') # Let black handle spacing

        elif name == "RETN":
             if len(resolved_params) != 1: raise CodeQuiltDecodeError("RETN needs one variable")
             var = resolved_params[0]
             # ? <var> ~ n : N > R n N <
             self._write_token(f"if {var} is None:", spacing='none')
             self.indent_level += 1
             self._write('\n')
             self.needs_indent = True
             self._write_token("return None", spacing='none')
             self.indent_level -= 1
             self._write('\n')
             self.needs_indent = True # Prepare for next line

        elif name == "TRYLOG":
             if len(resolved_params) != 2: raise CodeQuiltDecodeError("TRYLOG needs error type and variable name parameters before body")
             if body_tokens is None: raise CodeQuiltDecodeError("TRYLOG requires a body block {}")
             err_type, err_var = resolved_params

             # T : N > <body> N < X <err> as <var> : N > c105.e(f"FAIL: {<var>}", exc_info=t) N <
             self._write_token("try:", spacing='none')
             self.indent_level += 1
             self._write('\n'); self.needs_indent = True
             # Recursively expand body tokens
             for token in body_tokens:
                 self._process_token(token)
             # Ensure final newline if body didn't end with one? Handled by structure tokens usually.
             self.indent_level -= 1
             self._write('\n'); self.needs_indent = True # End of try block needs dedent handled BEFORE except

             self._write_token(f"except {err_type} as {err_var}:", spacing='none')
             self.indent_level += 1
             self._write('\n'); self.needs_indent = True
             log_msg = f'f"FAIL: {{{err_var}}}"' # Format string for the error
             self._write_token(f"{CORPUS_DICT['c105']}.error({log_msg}, exc_info=True)", spacing='none')
             self.indent_level -= 1
             self._write('\n')
             self.needs_indent = True # Prepare for next line after except block

        # Add other semantic token expansions (RETF, RAISE, DGET, DBEXEC, etc.) following the spec patterns
        # ... (implementation detail for each semantic token) ...

        else:
             print(f"Warning: Unsupported semantic token '{name}'. Ignoring.", file=sys.stderr)


    def _resolve_token_value(self, token_struct):
         """Converts a parsed token structure back into its Python string representation."""
         token_type = token_struct['type']
         token_value = token_struct['value']

         if token_type == 'corpus_ref':
             return CORPUS_DICT.get(token_value, f"__UNKNOWN_CORPUS_{token_value}__")
         elif token_type == 'dynamic_ref':
             return self.dynamic_map.get(token_value, f"__UNKNOWN_DYNAMIC_{token_value}__")
         elif token_type == 'literal_ref':
             lit = self.literal_map.get(token_value, f"__UNKNOWN_LITERAL_{token_value}__")
             # Represent the literal correctly (handle multi-line, quotes etc.)
             if self.keep_comments and lit.strip().startswith('#'): # Check if it was stored as a comment
                 return lit # Return comment as is
             else:
                 return repr(lit) # Use repr for safe string/bytes representation
         elif token_type == 'fixed_token':
             py_val = FIXED_TOKEN_MAP.get(token_value)
             # Handle structural tokens that shouldn't be directly resolved as values
             if py_val in ['_INDENT_', '_DEDENT_', '\n']: return f"__STRUCTURAL_{token_value}__"
             return py_val.strip() # Return the Python equivalent, strip spaces added for parsing convenience
         elif token_type in ['string_literal', 'bytes_literal', 'number_literal']:
             return token_value # Already in Python literal format
         elif token_type == 'boolean_literal':
             return "True" if token_value == 't' else "False"
         elif token_type == 'null_literal':
             return "None"
         elif token_type == 'escape_hatch':
             return token_struct['raw_code'] # Return raw code from escape hatch
         else:
             return f"__UNRESOLVED_{token_type}_{token_value}__"


    def _parse_next_token(self, in_semantic_param=False, in_semantic_body=False):
         """Parses the next token from the current body position."""
         # Skip whitespace between tokens
         while self.pos < len(self.body) and self.body[self.pos].isspace():
             self.pos += 1

         if self.pos >= len(self.body):
             return None # End of body

         start_pos = self.pos
         char = self.body[self.pos]

         # 1. Check for References (c<n>, d<n>, l<n>)
         ref_match = RE_REF.match(self.body, self.pos)
         if ref_match:
             ref_type_char = ref_match.group(1)
             ref_key = ref_match.group(0)
             self._consume(len(ref_key))
             ref_type = {'c': 'corpus_ref', 'd': 'dynamic_ref', 'l': 'literal_ref'}[ref_type_char]
             return {'type': ref_type, 'value': ref_key, 'pos': start_pos}

         # 2. Check for Semantic Tokens (NAME(...) or NAME(...){...})
         #    Avoid matching if inside a parameter list already unless nested semantics allowed
         sem_match = RE_SEMANTIC_START.match(self.body, self.pos)
         # Also check it's not just an uppercase fixed token like 'D' or 'C'
         is_fixed = char in FIXED_TOKEN_MAP and len(char) == 1 and char.isupper()

         if sem_match and not is_fixed:
              name = sem_match.group(1)
              # Check if name is one of the defined semantic tokens
              # (could precompute a set of valid semantic token names)
              KNOWN_SEMANTIC_TOKENS = {"LOG", "TRYLOG", "RETN", "RETF", "RAISE", "ATTR", "DGET", "DBEXEC", "DBFETCH1", "CHKEXIT", "CHKINIT", "PATHJOIN", "MKDIRS"}
              if name in KNOWN_SEMANTIC_TOKENS:
                  self._consume(len(name) + 1) # Consume NAME and '('
                  parsed_name, params, body_tokens_list = self._parse_semantic_token(name)
                  # Store the parsed structure, including params/body as raw token structures
                  return {'type': 'semantic_token', 'value': parsed_name, 'params': params, 'body': body_tokens_list, 'pos': start_pos}
              # else: Not a known semantic token, might be regular function call

         # 3. Check for Escape Hatch L'{...}'
         #    Use regex from start of current position
         hatch_match = RE_ESCAPE_HATCH.match(self.body, self.pos)
         if hatch_match:
             raw_code = hatch_match.group(1)
             # Unescape \\ -> \, \} -> }, \{ -> { within raw_code
             unescaped_code = raw_code.replace("\\}", "}").replace("\\{", "{").replace("\\\\", "\\")
             self._consume(len(hatch_match.group(0)))
             return {'type': 'escape_hatch', 'value': hatch_match.group(0), 'raw_code': unescaped_code, 'pos': start_pos}

         # 4. Check for Literals (Numbers, Strings, Bytes, t/f/n)
         # Number literal
         num_match = RE_NUMBER.match(self.body, self.pos)
         if num_match:
             num_str = num_match.group(0)
             self._consume(len(num_str))
             return {'type': 'number_literal', 'value': num_str, 'pos': start_pos}

         # Boolean/None literals (single char)
         if char == 't':
             self._consume(1)
             return {'type': 'boolean_literal', 'value': 't', 'pos': start_pos}
         if char == 'f':
             self._consume(1)
             return {'type': 'boolean_literal', 'value': 'f', 'pos': start_pos}
         if char == 'n':
             self._consume(1)
             return {'type': 'null_literal', 'value': 'n', 'pos': start_pos}

         # String/Bytes literals
         if char == "'":
             self._consume(1)
             str_val = self._parse_string_literal("'")
             return {'type': 'string_literal', 'value': str_val, 'pos': start_pos}
         if char == '"':
             self._consume(1)
             str_val = self._parse_string_literal('"')
             return {'type': 'string_literal', 'value': str_val, 'pos': start_pos}
         if char == 'b' and self._peek(2) in ["b'", 'b"']:
             quote = self._peek(2)[1]
             self._consume(2)
             bytes_val = self._parse_bytes_literal(quote)
             return {'type': 'bytes_literal', 'value': bytes_val, 'pos': start_pos}

         # 5. Check for Fixed Tokens (Keywords, Operators, Structure)
         # Prioritize longer potential tokens? No, spec implies single chars mostly.
         # Need to handle multi-char operators if they weren't mapped to single chars?
         # The reduced spec implies things like == are two tokens: = =
         if char in FIXED_TOKEN_MAP:
             self._consume(1)
             return {'type': 'fixed_token', 'value': char, 'pos': start_pos}

         # 6. Check for Decorator prefix
         if char == '@': # Spec implies '@' is just a prefix, next token is the decorator name/call
             self._consume(1)
             # We just return the '@', the next token parse will get the function/call
             return {'type': 'decorator_prefix', 'value': '@', 'pos': start_pos}


         # If nothing matched, it's an unknown token
         raise CodeQuiltDecodeError(f"Unknown or invalid token starting with '{self.body[self.pos]}' at position {self.pos}")

    def _process_token(self, token_struct):
        """Processes a single parsed token structure and writes output."""
        token_type = token_struct['type']
        token_value = token_struct['value']

        if token_type == 'corpus_ref':
            self._write_token(CORPUS_DICT.get(token_value, f"__UNKNOWN_CORPUS_{token_value}__"))
        elif token_type == 'dynamic_ref':
             self._write_token(self.dynamic_map.get(token_value, f"__UNKNOWN_DYNAMIC_{token_value}__"))
        elif token_type == 'literal_ref':
            lit = self.literal_map.get(token_value, f"__UNKNOWN_LITERAL_{token_value}__")
            # Handle comments vs other literals
            if self.keep_comments and lit.strip().startswith('#'):
                # Write comment, ensuring it's on its own line or appropriately placed
                # This heuristic might need refinement based on how comments are stored/intended
                if not self.output.getvalue().endswith('\n') and self.output.tell() > 0:
                     self._write('\n')
                     self.needs_indent = True
                self._write_token(lit, spacing='none') # Write comment content
                self._write('\n') # Assume comments occupy a full line
                self.needs_indent = True
            else:
                 # Use repr() for safe literal representation (handles quotes, escapes)
                 self._write_token(repr(lit), spacing='literal')

        elif token_type == 'fixed_token':
            py_val = FIXED_TOKEN_MAP.get(token_value)
            if py_val == '\n':
                self._write('\n')
                self.needs_indent = True
            elif py_val == '_INDENT_':
                self.indent_level += 1
                # Don't write anything, affects next line's indent calculation
            elif py_val == '_DEDENT_':
                if self.indent_level > 0:
                    self.indent_level -= 1
                else:
                     print(f"Warning: Attempted to dedent below level 0 at pos {token_struct['pos']}", file=sys.stderr)
                # Don't write anything
            else:
                 # Apply spacing heuristics (mostly handled by _write_token)
                 self._write_token(py_val) # Pass the Python equivalent

        elif token_type == 'semantic_token':
             self._expand_semantic_token(token_value, token_struct['params'], token_struct['body'])

        elif token_type == 'escape_hatch':
            # Write the raw, unescaped code directly
            self._write_token(token_struct['raw_code'], spacing='none')

        elif token_type == 'decorator_prefix':
            self._write_token('@', spacing='none') # Write @, no space before next token

        elif token_type in ['number_literal', 'string_literal', 'bytes_literal']:
             self._write_token(token_value, spacing='literal')
        elif token_type == 'boolean_literal':
             self._write_token("True" if token_value == 't' else "False", spacing='heuristic')
        elif token_type == 'null_literal':
            self._write_token("None", spacing='heuristic')

        else:
            # Should not happen if _parse_next_token is correct
             print(f"Warning: Unhandled token type '{token_type}' in _process_token. Ignoring.", file=sys.stderr)


    def decode(self):
        """Performs the decoding process."""
        if '|||' not in self.codequilt_string:
            raise CodeQuiltDecodeError("Invalid CodeQuilt format: Missing '|||' separator.")

        header_part, self.body = self.codequilt_string.split('|||', 1)

        self._parse_header(header_part)

        # --- Body Processing ---
        self.output = StringIO()
        self.indent_level = 0
        self.needs_indent = True # Assume start of file needs indent check (level 0)
        self.pos = 0

        while True:
            token = self._parse_next_token()
            if token is None:
                break # End of body
            self._process_token(token)

        reconstructed_code = self.output.getvalue()

        # Optionally format with black or other formatter
        return format_python_code(reconstructed_code) # Use external formatter


# --- Helper Functions (Mostly from original, adapted slightly) ---

def format_python_code(code_string):
    """Formats Python code using black, if available."""
    try:
        # Try finding black relative to the current Python executable first
        py_executable = sys.executable
        py_dir = os.path.dirname(py_executable)
        black_paths = [
            os.path.join(py_dir, 'black'),
            os.path.join(py_dir, 'Scripts', 'black.exe'), # Windows
            os.path.join(py_dir, 'bin', 'black'),       # Unix-like venv
            'black' # Fallback to PATH
        ]

        found_black = None
        for bp in black_paths:
            try:
                # Check if path exists and is executable
                 if os.path.isfile(bp) and os.access(bp, os.X_OK):
                     # Check if it runs
                     subprocess.run([bp, '--version'], capture_output=True, check=True, timeout=2)
                     found_black = bp
                     break
            except (FileNotFoundError, PermissionError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                continue # Try next path

        if found_black is None:
             # If not found relative, try generic command (might work if in PATH correctly)
            try:
                subprocess.run(['black', '--version'], capture_output=True, check=True, timeout=2)
                found_black = 'black'
            except (FileNotFoundError, PermissionError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
                 print("Warning: 'black' formatter not found or executable. Output may not be perfectly formatted.", file=sys.stderr)
                 return code_string


        process = subprocess.run(
            [found_black, '--quiet', '-'], # Use found path
            input=code_string.encode('utf-8'),
            capture_output=True,
            check=True,
            timeout=15 # Add timeout for safety
        )
        return process.stdout.decode('utf-8')
    except FileNotFoundError: # Should be caught above, but as fallback
        print("Warning: 'black' formatter not found. Output may not be perfectly formatted.", file=sys.stderr)
        return code_string
    except subprocess.TimeoutExpired:
         print("Warning: 'black' formatter timed out. Returning unformatted code.", file=sys.stderr)
         return code_string
    except subprocess.CalledProcessError as e:
        print(f"Warning: 'black' formatter failed:\n--- Formatter Stderr ---\n{e.stderr.decode()}\n--- End Stderr ---", file=sys.stderr)
        # Optionally return the original code OR the potentially broken formatted code
        # Returning original is safer if black fails badly
        return code_string # Return original on failure
    except Exception as e:
        print(f"Warning: Error running 'black': {e}", file=sys.stderr)
        return code_string

def python_to_codequilt(python_code):
    """
    Converts Python source code to a CodeQuilt string (v0.7.1).

    NOTE: This is a STUB function. A full implementation requires
    parsing Python code (e.g., using AST/tokenize), identifying patterns
    for semantic tokens, managing corpus/dynamic dictionaries, and formatting
    according to the CodeQuilt spec. This is a complex task beyond the scope
    of this initial tool rewrite.
    """
    print("Error: python_to_codequilt conversion (v0.7.1) is complex and not implemented.", file=sys.stderr)
    print("Requires full Python AST parsing and pattern matching for semantic tokens.", file=sys.stderr)
    # Placeholder structure:
    header_parts = [f"V:{SPEC_VERSION}"]
    # ... Logic to parse python_code ...
    # ... Identify identifiers -> build dynamic_dict D ...
    dynamic_dict_str = "D:[]" # Placeholder
    header_parts.append(dynamic_dict_str)
    # ... Identify long literals -> build literal_dict X ...
    literal_dict_str = "X:[]" # Placeholder
    header_parts.append(literal_dict_str)
    # ... Add other header fields like I:, O:, C: if needed ...
    header = f"[{';'.join(header_parts)}]"
    body = "# Python to CodeQuilt not implemented" # Placeholder body
    return header + "|||" + body
    # raise NotImplementedError("Python-to-CodeQuilt (v0.7.1) conversion requires a full Python parser.")

# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(
        description="Convert CodeQuilt (.cq) files to Python (.py) using CodeQuilt Spec v0.7.1.",
        epilog=f"Based on CodeQuilt Spec {SPEC_VERSION}. Note: .py -> .cq conversion is NOT IMPLEMENTED."
    )
    parser.add_argument("input_file", help="Path to the input CodeQuilt file (.cq)")
    parser.add_argument("-o", "--output", help="Path to the output Python file (.py). If omitted, derived from input name.")
    # Add verbosity or strictness flags if needed

    args = parser.parse_args()

    input_path = args.input_file
    if not os.path.exists(input_path):
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    base, ext = os.path.splitext(input_path)
    ext = ext.lower()

    if ext != '.cq':
        print(f"Error: Input file must have a .cq extension for decoding.", file=sys.stderr)
        sys.exit(1)

    output_path = args.output if args.output else base + ".py"
    result_content = None

    try:
        print(f"Converting CodeQuilt (.cq) to Python (.py)...")
        with open(input_path, 'r', encoding='utf-8') as f:
            input_content = f.read()

        decoder = CodeQuiltDecoder(input_content)
        result_content = decoder.decode()

        if output_path and result_content is not None:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(result_content)
            print(f"Successfully saved result to: {output_path}")
        elif result_content is not None:
             print("\n--- Decoded Python Code ---\n")
             print(result_content)
             print("\n--- End Decoded Code ---")


    except FileNotFoundError: # Should be caught earlier, but just in case
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)
    except CodeQuiltDecodeError as e:
        print(f"Error decoding {input_path}: {e}", file=sys.stderr)
        # Print context around error position if possible
        if hasattr(e, '__traceback__'):
            tb = e.__traceback__
            while tb.tb_next: tb = tb.tb_next # Get innermost frame info
            if hasattr(decoder, 'pos') and hasattr(decoder, 'body'):
                 context_start = max(0, decoder.pos - 30)
                 context_end = min(len(decoder.body), decoder.pos + 30)
                 print(f"  Context around position {decoder.pos}:")
                 print(f"  ...{decoder.body[context_start:decoder.pos]}[ERROR>>]{decoder.body[decoder.pos:context_end]}...")

        sys.exit(1)
    except NotImplementedError as e:
         print(f"Error: Feature not implemented: {e}", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        import traceback
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()