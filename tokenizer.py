import re
from enum import Enum, auto


def group(*choices): return '(' + '|'.join(choices) + ')'
def any(*choices): return group(*choices) + '*'
def maybe(*choices): return group(*choices) + '?'
esc = re.escape
def once(char):return rf"{esc(char)}(?!{esc(char)})"
def twice(char: str):return rf"{esc(char)}{esc(char)}(?!{esc(char)})"
def thrice(char: str):return rf"{esc(char)}{esc(char)}{esc(char)}(?!{esc(char)})"


class TokenType(Enum):
    KEYWORD = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()
    PUNCTUATION = auto()

LUA_KEYWORDS = [
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "goto", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "until", "while"
]

LUA_OPERATORS = [
    "+", "-", "*", "/", "%", "^", "#", "&", "~", "|", "<<", ">>", "//", 
    "==", "~=", "<=", ">=", "<", ">", "=",
    "::", ";", ":", ",", ".", "..", "..." 
]
LUA_LCONTAINERS = [ "(",  "{",  "["]
LUA_RCONTAINERS = [")", "}", "]"]

# Define Lua keywords
keywords = {
    "and", "break", "do", "else", "elseif", "end", "false", "for", "function", "if",
    "in", "local", "nil", "not", "or", "repeat", "return", "then", "true", "until", "while"
}


SingleHyphen = r"-(?!-)"
Whitespace = r'[ \f\t]*'
Hexnumber = r'0[xX](?:_?[0-9a-fA-F])+'
Binnumber = r'0[bB](?:_?[01])+'
Octnumber = r'0[oO](?:_?[0-7])+'
Decnumber = r'(?:0(?:_?0)*|[1-9](?:_?[0-9])*)'
Intnumber = group(Hexnumber, Binnumber, Octnumber, Decnumber)
Exponent = r'[eE][-+]?[0-9](?:_?[0-9])*'
Pointfloat = group(r'[0-9](?:_?[0-9])*\.(?:[0-9](?:_?[0-9])*)?', r'\.[0-9](?:_?[0-9])*') + maybe(Exponent)
Expfloat = r'[0-9](?:_?[0-9])*' + Exponent
Floatnumber = group(Pointfloat, Expfloat)
Imagnumber = group(r'[0-9](?:_?[0-9])*[jJ]', Floatnumber + r'[jJ]')
Ignore = Whitespace + any(r'\\\r?\n' + Whitespace)

KeywordPatterns = group("and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "goto", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "until", "while")
String = group(r"'[^\n'\\]*(?:\\.[^\n'\\]*)*'", r'"[^\n"\\]*(?:\\.[^\n"\\]*)*"')
ConString = group(r"'[^\n'\\]*(?:\\.[^\n'\\]*)*" + group("'", r'\\\r?\n'), 
                   r'"[^\n"\\]*(?:\\.[^\n"\\]*)*' +group('"', r'\\\r?\n'))
Number = group(Imagnumber, Floatnumber, Intnumber)
LeftContainers = group(r"\(",  r"\{",  r"\[")
RightContainers = group(r"\)", r"\}", r"\]")

String1 = r"\'.*\'"
String2 = r'\".*\"'
String = group(String1, String2)


Operators = group(
    once(r"+"), 
    once(r"-"), 
    once(r"*"), 
    once(r"/"), 
    once(r"%"), 
    once(r"^"), 
    once(r"#"), 
    once(r"&"), 
    once(r"~"), 
    once(r"|"), 
    twice(r"<"), 
    twice(r">"), 
    twice(r"/"), 
    twice(r"="),
    r"\~\=", 
    r"\<\=", 
    r"\>\=", 
    once(r"<"), 
    once(r">"), 
    once(r"="), 
    twice(r":"), 
    once(r";"), 
    once(r":"), 
    once(r","), 
    once(r"."),
    twice(r"."), 
    thrice(r".") 
)

token_specification = [
    ('COMMENT',     r'--.*\n'),                  # Single line comment
    ('STRING',      String),                     # String literals
    ('MLCOMMENT',   re.compile(r'--\[.*\]--', re.DOTALL)),          # Multi Line Comment
    ('NUMBER',      Number),                     # Integer or decimal number
    ('NAME',        r'\b[A-Za-z_][A-Za-z0-9_]*\b'),  # Identifiers
    ('OPERATOR',    Operators),                  # Lua operators
    ('LCONTAINER',  LeftContainers),             # Left Container
    ('RCONTAINER',  RightContainers),            # Right Container
]


class Token:
    def __init__(self, type, value, start, end):
        self.type = type
        self.value = value
        self.start = start
        self.end = end

    def __repr__(self):
        return f'''Token(
            type ={self.type}, 
            value={repr(self.value)}, 
            start={self.start}, 
            end  ={self.end}
            )'''
    
def tokenize_lua(code):
    tokenmap = {}
    codelen = len(code)
    # get all the possible tokens
    for tokspec in token_specification:
        for find in re.finditer(tokspec[1], code):
            start = find.start()
            end = find.end()
            string = code[start:end]
            ts = tokspec[0]
            if ts == "NAME" and string in LUA_KEYWORDS:
                ts = string.upper()

            tokenmap[start] = Token(ts, string, start, end)

    # Collect only the tokens that dwarf other ones
    count = -1
    current_token= None
    tokens = []
    indent_count = 0

    while True:
        count+=1
        if count>=codelen:
            break 
        try:
            current_token = tokenmap[count]
            diff = current_token.end - current_token.start
            if diff == 1:
                count+=1
            else:
                for i in range(0, diff-1):
                    count+=1
            tokens.append(current_token)
        except KeyError:
            current_token = code[count]
            if current_token == "\n":
                tokens.append(Token("NEWLINE", value="\n", start=count, end=count+1))
            elif current_token == " ":
                stack = [" "]
                for i in range(1, 4):
                    try:stack.append(code[count + i])
                    except:break
                print(stack)
                if stack.count(" ") == 4:
                    if tokens[-1].type == "NEWLINE":
                        tokens.append(Token("INDENT", value="    ", start=count, end=count+3))
                        indent_count = 1
                    elif tokens[-1].type == "INDENT":
                        tokens.append(Token("INDENT", value="    ", start=count, end=count+3))
                        indent_count+=1
                    
                    count+=3
            else:
                tokens.append(current_token)


    return tokens

# Test the tokenizer
lua_code = '''
-- This is a comment

--[
    this is a multiline
    comment
]--

local x = 42
local y = 13.37
local str = "Hello, World!"
x = x + y
if x == y then
    print("x equals y")
else
    print("x does not equal y")
end
function foo(a, b)
    return a + b
end
'''

tokens = tokenize_lua(lua_code)
from pprint import pprint
pprint(tokens)
