"""
Incremental JSON Parser with Automata

A stack-based JSON parser that can handle partial and incomplete JSON from LLM tokens.
This parser is designed for streaming scenarios where JSON arrives incrementally
and needs to be processed before being complete.

Key features:
- Stack-based parsing for efficient state management
- Handles partial/incomplete JSON structures
- Emits completed components as they're parsed
- Supports nested objects and arrays
- Recovers from common LLM output issues (trailing commas, etc.)
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Callable,
    Generator,
    AsyncGenerator,
    Union,
)
from dataclasses import dataclass, field
from enum import Enum
import re
import json
import logging

from .models import (
    ParsedComponent,
    PartialJSONResult,
    ParseState,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Token Types and Parser States
# ============================================================================


class JSONToken(str, Enum):
    """JSON token types"""
    
    OBJECT_START = "{"
    OBJECT_END = "}"
    ARRAY_START = "["
    ARRAY_END = "]"
    COLON = ":"
    COMMA = ","
    STRING = "string"
    NUMBER = "number"
    TRUE = "true"
    FALSE = "false"
    NULL = "null"
    WHITESPACE = "whitespace"
    EOF = "eof"
    ERROR = "error"


class JSONParseState(str, Enum):
    """Parser state machine states"""
    
    # Initial state
    START = "start"
    
    # Object states
    OBJECT_START = "object_start"
    OBJECT_KEY = "object_key"
    OBJECT_COLON = "object_colon"
    OBJECT_VALUE = "object_value"
    OBJECT_COMMA = "object_comma"
    
    # Array states
    ARRAY_START = "array_start"
    ARRAY_VALUE = "array_value"
    ARRAY_COMMA = "array_comma"
    
    # Value states
    VALUE = "value"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL_VALUE = "null"
    
    # Terminal states
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class ParseStackEntry:
    """Entry in the parse stack"""
    
    state: JSONParseState
    container: Any  # The dict or list being built
    key: Optional[str] = None  # Current key if in object
    expect_value: bool = False  # Expecting a value next
    

@dataclass
class ParseResult:
    """Result of parsing a token"""
    
    success: bool
    new_state: JSONParseState
    value: Optional[Any] = None
    error: Optional[str] = None
    component_complete: bool = False
    component: Optional[ParsedComponent] = None


# ============================================================================
# Incremental JSON Parser
# ============================================================================


class IncrementalJSONParser:
    """
    Stack-based incremental JSON parser.
    
    Parses JSON incrementally from a stream of characters or tokens,
    emitting completed objects/arrays as they finish parsing.
    """
    
    def __init__(
        self,
        auto_recover: bool = True,
        strict_mode: bool = False,
        max_depth: int = 100,
        max_string_length: int = 1000000,
    ):
        """
        Initialize the parser.
        
        Args:
            auto_recover: Enable automatic recovery from common errors
            strict_mode: Enforce strict JSON compliance
            max_depth: Maximum nesting depth
            max_string_length: Maximum string length
        """
        self.auto_recover = auto_recover
        self.strict_mode = strict_mode
        self.max_depth = max_depth
        self.max_string_length = max_string_length
        
        # Parser state
        self._buffer: str = ""
        self._position: int = 0
        self._state: JSONParseState = JSONParseState.START
        self._stack: List[ParseStackEntry] = []
        self._root: Optional[Any] = None
        self._current_container: Optional[Any] = None
        self._current_key: Optional[str] = None
        
        # Completed components queue
        self._completed_components: List[ParsedComponent] = []
        
        # Tracking
        self._depth: int = 0
        self._string_buffer: str = ""
        self._number_buffer: str = ""
        self._in_string: bool = False
        self._escape_next: bool = False
        self._token_start: int = 0
        
        # Callbacks
        self._on_component_complete: Optional[Callable[[ParsedComponent], None]] = None
        
    def reset(self) -> None:
        """Reset parser state for new input"""
        self._buffer = ""
        self._position = 0
        self._state = JSONParseState.START
        self._stack = []
        self._root = None
        self._current_container = None
        self._current_key = None
        self._completed_components = []
        self._depth = 0
        self._string_buffer = ""
        self._number_buffer = ""
        self._in_string = False
        self._escape_next = False
        self._token_start = 0
    
    # ========================================================================
    # Public API
    # ========================================================================
    
    def feed(self, chunk: str) -> PartialJSONResult:
        """
        Feed a chunk of characters to the parser.
        
        Args:
            chunk: String chunk to parse
            
        Returns:
            PartialJSONResult with current parse state
        """
        self._buffer += chunk
        self._parse_buffer()
        
        return self._build_result()
    
    async def feed_async(self, chunk: str) -> PartialJSONResult:
        """
        Async version of feed.
        
        Args:
            chunk: String chunk to parse
            
        Returns:
            PartialJSONResult with current parse state
        """
        return self.feed(chunk)
    
    def feed_token(self, token: str, token_type: JSONToken) -> PartialJSONResult:
        """
        Feed a pre-tokenized token to the parser.
        
        Args:
            token: The token string
            token_type: Type of the token
            
        Returns:
            PartialJSONResult with current parse state
        """
        # Handle pre-tokenized input
        if token_type == JSONToken.OBJECT_START:
            self._handle_object_start()
        elif token_type == JSONToken.OBJECT_END:
            self._handle_object_end()
        elif token_type == JSONToken.ARRAY_START:
            self._handle_array_start()
        elif token_type == JSONToken.ARRAY_END:
            self._handle_array_end()
        elif token_type == JSONToken.STRING:
            self._handle_string_value(token)
        elif token_type == JSONToken.NUMBER:
            self._handle_number_value(token)
        elif token_type == JSONToken.TRUE:
            self._handle_literal(True)
        elif token_type == JSONToken.FALSE:
            self._handle_literal(False)
        elif token_type == JSONToken.NULL:
            self._handle_literal(None)
        elif token_type == JSONToken.COLON:
            self._handle_colon()
        elif token_type == JSONToken.COMMA:
            self._handle_comma()
        
        return self._build_result()
    
    def get_completed_components(self) -> List[ParsedComponent]:
        """
        Get and clear completed components.
        
        Returns:
            List of completed components
        """
        components = self._completed_components.copy()
        self._completed_components = []
        return components
    
    def finalize(self) -> PartialJSONResult:
        """
        Finalize parsing and attempt to recover incomplete structures.
        
        Returns:
            Final PartialJSONResult
        """
        if self.auto_recover:
            self._attempt_recovery()
        
        return self._build_result()
    
    def set_component_callback(
        self, 
        callback: Callable[[ParsedComponent], None]
    ) -> None:
        """Set callback for completed components"""
        self._on_component_complete = callback
    
    @property
    def is_complete(self) -> bool:
        """Check if parsing is complete"""
        return self._state == JSONParseState.COMPLETE
    
    @property
    def is_valid(self) -> bool:
        """Check if current state is valid"""
        return self._state != JSONParseState.ERROR
    
    @property
    def depth(self) -> int:
        """Get current nesting depth"""
        return self._depth
    
    @property
    def current_state(self) -> JSONParseState:
        """Get current parser state"""
        return self._state
    
    @property
    def expects(self) -> List[str]:
        """Get list of expected tokens"""
        return self._get_expected_tokens()
    
    # ========================================================================
    # Parsing Engine
    # ========================================================================
    
    def _parse_buffer(self) -> None:
        """Parse the current buffer"""
        while self._position < len(self._buffer):
            char = self._buffer[self._position]
            
            # Handle string content specially
            if self._in_string:
                self._parse_string_char(char)
                self._position += 1
                continue
            
            # Skip whitespace outside strings
            if char in ' \t\n\r':
                self._position += 1
                continue
            
            # Parse structural characters
            if char == '{':
                self._handle_object_start()
            elif char == '}':
                self._handle_object_end()
            elif char == '[':
                self._handle_array_start()
            elif char == ']':
                self._handle_array_end()
            elif char == ':':
                self._handle_colon()
            elif char == ',':
                self._handle_comma()
            elif char == '"':
                self._start_string()
            elif char in '-0123456789':
                self._start_number()
                continue  # Don't increment, number parser will handle it
            elif char == 't':
                self._parse_literal("true", True)
            elif char == 'f':
                self._parse_literal("false", False)
            elif char == 'n':
                self._parse_literal("null", None)
            else:
                # Unexpected character
                if self.auto_recover:
                    logger.warning(f"Unexpected character '{char}' at position {self._position}")
                    self._position += 1
                    continue
                else:
                    self._state = JSONParseState.ERROR
                    return
            
            self._position += 1
    
    def _parse_string_char(self, char: str) -> None:
        """Parse a single character inside a string"""
        if self._escape_next:
            # Handle escape sequences
            escape_map = {
                '"': '"', '\\': '\\', '/': '/',
                'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t',
            }
            if char in escape_map:
                self._string_buffer += escape_map[char]
            elif char == 'u':
                # Unicode escape - need 4 hex digits
                if self._position + 4 < len(self._buffer):
                    hex_str = self._buffer[self._position+1:self._position+5]
                    try:
                        code_point = int(hex_str, 16)
                        self._string_buffer += chr(code_point)
                        self._position += 4
                    except ValueError:
                        self._string_buffer += '\\u' + hex_str
                        self._position += 4
            else:
                self._string_buffer += '\\' + char
            self._escape_next = False
        elif char == '\\':
            self._escape_next = True
        elif char == '"':
            # End of string
            self._end_string()
        else:
            self._string_buffer += char
    
    def _start_string(self) -> None:
        """Start parsing a string"""
        self._in_string = True
        self._string_buffer = ""
        self._escape_next = False
    
    def _end_string(self) -> None:
        """End parsing a string"""
        self._in_string = False
        value = self._string_buffer
        self._string_buffer = ""
        
        # Handle string based on current state
        if self._state in (JSONParseState.OBJECT_START, JSONParseState.OBJECT_COMMA):
            # This is a key
            self._current_key = value
            self._state = JSONParseState.OBJECT_COLON
        elif self._state in (JSONParseState.OBJECT_VALUE, JSONParseState.ARRAY_VALUE, JSONParseState.VALUE):
            # This is a string value
            self._handle_string_value(value)
        else:
            # Unexpected string
            self._handle_string_value(value)
    
    def _start_number(self) -> None:
        """Start parsing a number"""
        self._number_buffer = ""
        self._parse_number()
    
    def _parse_number(self) -> None:
        """Parse a complete number from buffer"""
        start = self._position
        has_dot = False
        has_exp = False
        
        while self._position < len(self._buffer):
            char = self._buffer[self._position]
            
            if char in '0123456789':
                self._number_buffer += char
                self._position += 1
            elif char == '-' and (self._position == start or self._buffer[self._position-1] in 'eE'):
                self._number_buffer += char
                self._position += 1
            elif char == '.' and not has_dot:
                has_dot = True
                self._number_buffer += char
                self._position += 1
            elif char in 'eE' and not has_exp:
                has_exp = True
                self._number_buffer += char
                self._position += 1
            elif char in '+-' and self._buffer[self._position-1] in 'eE':
                self._number_buffer += char
                self._position += 1
            else:
                break
        
        # Convert number
        if self._number_buffer:
            try:
                if has_dot or has_exp:
                    value = float(self._number_buffer)
                else:
                    value = int(self._number_buffer)
                self._handle_number_value(value)
            except ValueError:
                if self.auto_recover:
                    self._handle_string_value(self._number_buffer)
                else:
                    self._state = JSONParseState.ERROR
        
        # Position was already incremented in loop, need to adjust
        self._position -= 1
    
    def _parse_literal(self, literal: str, value: Any) -> None:
        """Parse a literal (true, false, null)"""
        end = self._position + len(literal)
        if end <= len(self._buffer):
            token = self._buffer[self._position:end]
            if token == literal:
                self._position = end - 1  # -1 because caller will +1
                self._handle_literal(value)
                return
        
        if self.auto_recover:
            # Skip the character
            pass
        else:
            self._state = JSONParseState.ERROR
    
    # ========================================================================
    # Structure Handlers
    # ========================================================================
    
    def _handle_object_start(self) -> None:
        """Handle '{' token"""
        if self._depth >= self.max_depth:
            self._state = JSONParseState.ERROR
            return
        
        new_obj: Dict[str, Any] = {}
        self._depth += 1
        
        if self._root is None:
            self._root = new_obj
            self._current_container = new_obj
        else:
            # Add to current container
            self._add_to_current(new_obj)
        
        # Push state
        self._stack.append(ParseStackEntry(
            state=self._state,
            container=self._current_container,
            key=self._current_key,
        ))
        
        self._current_container = new_obj
        self._current_key = None
        self._state = JSONParseState.OBJECT_START
    
    def _handle_object_end(self) -> None:
        """Handle '}' token"""
        if self._depth == 0:
            if self.auto_recover:
                return
            self._state = JSONParseState.ERROR
            return
        
        # Check if this object is a complete component
        self._check_component_complete()
        
        self._depth -= 1
        
        # Pop state
        if self._stack:
            entry = self._stack.pop()
            parent_container = entry.container
            self._current_key = entry.key
        else:
            parent_container = None
        
        self._current_container = parent_container
        
        if self._depth == 0:
            self._state = JSONParseState.COMPLETE
        elif self._current_container is not None and isinstance(self._current_container, dict):
            self._state = JSONParseState.OBJECT_COMMA
        elif self._current_container is not None and isinstance(self._current_container, list):
            self._state = JSONParseState.ARRAY_COMMA
    
    def _handle_array_start(self) -> None:
        """Handle '[' token"""
        if self._depth >= self.max_depth:
            self._state = JSONParseState.ERROR
            return
        
        new_arr: List[Any] = []
        self._depth += 1
        
        if self._root is None:
            self._root = new_arr
            self._current_container = new_arr
        else:
            self._add_to_current(new_arr)
        
        # Push state
        self._stack.append(ParseStackEntry(
            state=self._state,
            container=self._current_container,
            key=self._current_key,
        ))
        
        self._current_container = new_arr
        self._current_key = None
        self._state = JSONParseState.ARRAY_START
    
    def _handle_array_end(self) -> None:
        """Handle ']' token"""
        if self._depth == 0:
            if self.auto_recover:
                return
            self._state = JSONParseState.ERROR
            return
        
        self._depth -= 1
        
        # Pop state
        if self._stack:
            entry = self._stack.pop()
            parent_container = entry.container
            self._current_key = entry.key
        else:
            parent_container = None
        
        self._current_container = parent_container
        
        if self._depth == 0:
            self._state = JSONParseState.COMPLETE
        elif self._current_container is not None and isinstance(self._current_container, dict):
            self._state = JSONParseState.OBJECT_COMMA
        elif self._current_container is not None and isinstance(self._current_container, list):
            self._state = JSONParseState.ARRAY_COMMA
    
    def _handle_colon(self) -> None:
        """Handle ':' token"""
        if self._state == JSONParseState.OBJECT_COLON:
            self._state = JSONParseState.OBJECT_VALUE
    
    def _handle_comma(self) -> None:
        """Handle ',' token"""
        if self._state == JSONParseState.OBJECT_COMMA:
            self._state = JSONParseState.OBJECT_START
        elif self._state == JSONParseState.ARRAY_COMMA:
            self._state = JSONParseState.ARRAY_VALUE
        elif self.auto_recover:
            # Trailing comma, ignore
            pass
    
    def _handle_string_value(self, value: str) -> None:
        """Handle a string value"""
        self._add_to_current(value)
    
    def _handle_number_value(self, value: Union[int, float]) -> None:
        """Handle a number value"""
        self._add_to_current(value)
    
    def _handle_literal(self, value: Any) -> None:
        """Handle a literal value (true, false, null)"""
        self._add_to_current(value)
    
    def _add_to_current(self, value: Any) -> None:
        """Add a value to the current container"""
        if self._current_container is None:
            self._root = value
        elif isinstance(self._current_container, dict):
            if self._current_key is not None:
                self._current_container[self._current_key] = value
                self._current_key = None
            self._state = JSONParseState.OBJECT_COMMA
        elif isinstance(self._current_container, list):
            self._current_container.append(value)
            self._state = JSONParseState.ARRAY_COMMA
    
    # ========================================================================
    # Component Detection
    # ========================================================================
    
    def _check_component_complete(self) -> None:
        """Check if current object is a complete A2UI component"""
        if not isinstance(self._current_container, dict):
            return
        
        # Check for A2UI component markers
        if "id" in self._current_container and "component" in self._current_container:
            component = ParsedComponent(
                component_id=str(self._current_container.get("id", "")),
                component_type=str(self._current_container.get("component", "")),
                properties={
                    k: v for k, v in self._current_container.items()
                    if k not in ("id", "component", "children")
                },
                children=self._current_container.get("children", []),
                is_complete=True,
                parse_position=self._position,
            )
            
            self._completed_components.append(component)
            
            if self._on_component_complete:
                self._on_component_complete(component)
    
    def _attempt_recovery(self) -> None:
        """Attempt to recover from incomplete parsing"""
        # Close any unclosed structures
        while self._depth > 0:
            if isinstance(self._current_container, dict):
                self._handle_object_end()
            elif isinstance(self._current_container, list):
                self._handle_array_end()
        
        # If we have a partial string, try to close it
        if self._in_string and self._string_buffer:
            self._end_string()
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def _build_result(self) -> PartialJSONResult:
        """Build the result object"""
        return PartialJSONResult(
            is_complete=self.is_complete,
            is_valid=self.is_valid,
            value=self._root if self.is_complete else None,
            partial_value=self._root,
            parsed_components=self._completed_components.copy(),
            state=ParseState(self._state.value),
            position=self._position,
            depth=self._depth,
            error=None if self.is_valid else "Parse error",
            expects=self.expects,
        )
    
    def _get_expected_tokens(self) -> List[str]:
        """Get list of expected tokens for current state"""
        expected = {
            JSONParseState.START: ["{", "["],
            JSONParseState.OBJECT_START: ['"', "}"],
            JSONParseState.OBJECT_KEY: [":"],
            JSONParseState.OBJECT_COLON: [":"],
            JSONParseState.OBJECT_VALUE: ["value"],
            JSONParseState.OBJECT_COMMA: [",", "}"],
            JSONParseState.ARRAY_START: ["value", "]"],
            JSONParseState.ARRAY_VALUE: ["value"],
            JSONParseState.ARRAY_COMMA: [",", "]"],
            JSONParseState.VALUE: ["value"],
            JSONParseState.COMPLETE: [],
            JSONParseState.ERROR: [],
        }
        return expected.get(self._state, [])
    
    def get_partial_value(self) -> Optional[Any]:
        """Get the current partial value"""
        return self._root
    
    def get_remaining_buffer(self) -> str:
        """Get unprocessed buffer content"""
        return self._buffer[self._position:]


# ============================================================================
# Factory Function
# ============================================================================


def create_parser(
    auto_recover: bool = True,
    strict_mode: bool = False,
    **kwargs
) -> IncrementalJSONParser:
    """
    Factory function to create a parser instance.
    
    Args:
        auto_recover: Enable automatic recovery
        strict_mode: Enforce strict JSON
        **kwargs: Additional parser options
        
    Returns:
        Configured IncrementalJSONParser instance
    """
    return IncrementalJSONParser(
        auto_recover=auto_recover,
        strict_mode=strict_mode,
        **kwargs
    )


# ============================================================================
# Utility Functions
# ============================================================================


def parse_json_stream(
    stream: str,
    chunk_size: int = 1024,
) -> Generator[PartialJSONResult, None, None]:
    """
    Parse a JSON string in chunks.
    
    Args:
        stream: JSON string to parse
        chunk_size: Size of chunks to process
        
    Yields:
        PartialJSONResult for each chunk
    """
    parser = create_parser()
    
    for i in range(0, len(stream), chunk_size):
        chunk = stream[i:i + chunk_size]
        result = parser.feed(chunk)
        yield result
        
        if result.is_complete or not result.is_valid:
            break
    
    yield parser.finalize()


async def parse_json_stream_async(
    stream: AsyncGenerator[str, None],
) -> AsyncGenerator[PartialJSONResult, None]:
    """
    Async parse JSON from a stream.
    
    Args:
        stream: Async generator of string chunks
        
    Yields:
        PartialJSONResult for each chunk
    """
    parser = create_parser()
    
    async for chunk in stream:
        result = await parser.feed_async(chunk)
        yield result
        
        if result.is_complete or not result.is_valid:
            break
    
    yield parser.finalize()


def extract_components_from_partial(
    partial_json: str,
) -> Tuple[List[ParsedComponent], str]:
    """
    Extract complete components from partial JSON.
    
    Args:
        partial_json: Partially received JSON
        
    Returns:
        Tuple of (components, remaining_json)
    """
    parser = create_parser()
    result = parser.feed(partial_json)
    
    components = parser.get_completed_components()
    remaining = parser.get_remaining_buffer()
    
    return components, remaining
