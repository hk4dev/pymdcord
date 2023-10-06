import re
from pprint import pprint

test_string = """
# HEADER
 # HEADER
###### HEADER
 ###### HEADER
#WRONG HEADER
 ##WRONG HEADER

* LIST
  * LIST
*WRONGLIST

>BLOCKQUOTE
> BLOCKQUOTE
CONTINUED YAY
>> NEXT LEVEL

paragraph **effect** is __*here*__!
""".strip("\n")

t_HEADER = r"^\s*#{1,6}\s+[^\s]+.*\n?$"
t_LIST = r"^\s*([*\-+]|\d+\.\s)\s+[^\s]+.*\n?$"
t_BLOCKQUOTE = r"^\s*(?P<lv>>+)\s*[^\s]+.*\n?$"
t_BLOCK = r"^\s*(#{1,6}\s|[*\-+]\s|\d+\.\s|>+).*\n?$"

t_CODEBLOCK_START = r"^`{3}[^`\n]*\n$"
t_CODEBLOCK_END = r"^\s*`{3}\n?$"

HEADER = re.compile(t_HEADER)
LIST = re.compile(t_LIST)
BLOCKQUOTE = re.compile(t_BLOCKQUOTE)

CODEBLOCK_START = re.compile(t_CODEBLOCK_START)
CODEBLOCK_END = re.compile(t_CODEBLOCK_END)

def parse(t: str):
    ind = 0
    p = t.splitlines(keepends=True)
    res = []

    def paragraph_effect_parser(
        _line: str, 
        _res: list = [],
        insert_start_content: str = "",
        start_pos: int = 0, 
        triggered_by: str = None,
        type_as: str = "normal"):
        
        _ind = start_pos
        _res.append({"type": type_as, "content": insert_start_content})
        while _ind <= len(_line) - 1:
            if (curr_char := _line[_ind]) in ["*", "_"]:
                _ind, _res = paragraph_effect_parser(_line, _res, _line[_ind], _ind + 1, _line[_ind], "italic")
                continue
            elif _line[_ind:_ind+2] == "**":
                _ind, _res = paragraph_effect_parser(_line, _res, "**", _ind + 2, "**", "bold")
                continue
            elif _line[_ind:_ind+2] == "__":
                _ind, _res = paragraph_effect_parser(_line, _res, "__", _ind+2, "__", "underline")
                continue
            elif _line[_ind:_ind+2] == "~~":
                _ind, _res = paragraph_effect_parser(_line, _res, "~~", _ind+2, "~~", "strikethrough")
                continue
            elif _line[_ind:_ind+2] == "``":
                _ind, _res = paragraph_effect_parser(_line, _res, "``", _ind+2, "``", "code")
                continue
            elif _line[_ind:_ind+3] == "```":
                _ind, _res = paragraph_effect_parser(_line, _res, "```", _ind+3, "```", "incodeblock")
                continue

            if triggered_by is None:
                if len(_res) > 0 and _res[-1]["type"] == type_as:
                    _res[-1]["content"] += _line[_ind]
                else:
                    _res.append({"type": type_as, "content": _line[_ind]})
            else:
                if len(res) > 0 and _res[-1]["type"] == type_as:
                    _res[-1]["content"] += _line[_ind]
                else:
                    _res.append({"type": type_as, "content": _line[_ind]})
                if len(triggered_by) > 1 and _line[_ind+1-len(triggered_by):_ind+1] == triggered_by:
                    return _ind + 1, _res
                
            _ind += 1
        return _ind, _res

    while ind < len(p):
        line = p[ind]
        ind += 1
        if HEADER.fullmatch(line):
            print("HEADER " + line[:-1])
            res.append({"type": "header", "content": line})
        elif LIST.fullmatch(line):
            print("LISTSTART " + line[:-1])
            mem = [line]
            while ind < len(p):
                line = p[ind]
                if (flm := LIST.fullmatch(line)) or (line != "\n" and line.strip()[0] not in ['*', '-', '+']):
                    print("LISTITEM " + line[:-1])
                    if flm:
                        mem.append(line)
                    else:
                        print("CONTINUED")
                        mem[-1] += line
                elif line == "\n":
                    ind += 1
                    break
                ind += 1
            res.append({"type": "list", "content": mem})
        elif rlm := BLOCKQUOTE.fullmatch(line):
            print("BQUOTESTART " + line[:-1])
            mem = [{"lv": len(rlm.group("lv")), "content": line}]
            while ind < len(p):
                line = p[ind]
                if (flm := BLOCKQUOTE.fullmatch(line)) or (line != "\n" and line.strip()[0] != '>'):
                    print("BQUOTEITEM " + line[:-1], end="")
                    if flm:
                        lv = len(flm.group("lv"))
                        print(" LV " + str(lv))
                        mem.append({"lv": lv, "content": line})
                    else:
                        print(" CONTINUED")
                        mem[-1]["content"] += line
                elif line == "\n":
                    ind += 1
                    break
                ind += 1
            res.append({"type": "blockquote", "content": mem})
        else:
            print("IN PARAGRPAPH " + line[:-1])
            _, _res = paragraph_effect_parser(line)
            for p in _res:
                res.append(p)
    return res


pprint(parse(test_string))
