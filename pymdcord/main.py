import re

t_HEADER = r"^\s*#{1,6}\s(?P<content>\s*[^\s]+.*\n?)$"
t_LIST = r"^\s*([*\-+]\s|\d+\.\s)(?P<content>\s*[^\s]+.*\n?)$"
t_BLOCKQUOTE = r"^\s*(?P<lv>>+)(?P<content>\s*[^\s]+.*\n?)$"

t_CODEBLOCK_START = r"^`{3}(?P<lang>[^`\n]*)\n$"
t_CODEBLOCK_END = r"^\s*`{3}\n?$"

i_LINK = r"https?:\/\/[^\s\n]*"
i_MASKLINK = r"\[(?P<content>.*)\]\((?P<href>https?:\/\/[^s\n]*)\)"
i_MASKIMAGE = r"\[(?P<content>.*)\]\(!(?P<href>https?:\/\/[^s\n]*)\)"

HEADER = re.compile(t_HEADER)
LIST = re.compile(t_LIST)
BLOCKQUOTE = re.compile(t_BLOCKQUOTE)

CODEBLOCK_START = re.compile(t_CODEBLOCK_START)
CODEBLOCK_END = re.compile(t_CODEBLOCK_END)

ILINK = re.compile(i_LINK)
IMASKLINK = re.compile(i_MASKLINK)
IMASKIMAGE = re.compile(i_MASKIMAGE)

INLINE_TRIGGERS = {
    "bold": ["**"],
    "underline": ["__"],
    "italic": ['*', '_'],
    "strikethrough": ["~~"],
    "code": ["`"],
    "codeblock": ["```"],
    "secret": ["||"],
}

INLINE_REGEXS = {
    "link": ILINK,
    "masklink": IMASKLINK,
    "maskimage": IMASKIMAGE,
}

def parse(t: str):
    ind = 0
    p = t.splitlines(keepends=True)
    res = []

    def paragraph_effect_parser(
        _line: str,
        start_pos: int = 0, 
        triggered_by: str = None,
        type_as: str = "inline",
        root: bool = True):
        
        _res = {"type": type_as, "content": []}
        _ind = start_pos
        while _ind <= len(_line) - 1:
            should_continue_without_bump = False
            for trigger_type, trigger in INLINE_TRIGGERS.items():
                if (triggered := _line[_ind:_ind+len(trigger[0])]) in trigger:
                    if triggered_by in trigger:
                        # print('closed by', triggered, _ind)  # debug
                        # print((' ' if _ind - 1 < 0 else '') + line)  # debug
                        # print(' '*(_ind - 1 if _ind - 1 >= 0 else _ind) + '^^')  # debug
                        return _ind + len(triggered), _res
                    # print('opened by', triggered, _ind)  # debug
                    # print((' ' if _ind - 1 < 0 else '') + line)  # debug
                    # print(' '*(_ind - 1 if _ind - 1 >= 0 else _ind) + '^^')  # debug
                    _ind, _content_res = paragraph_effect_parser(_line, _ind + len(triggered), triggered, trigger_type, False)
                    if _content_res["type"] == "noclose":
                        if len(_res["content"]) > 0 and type(_res["content"][-1]) == str:
                            _res["content"][-1] += triggered
                        else:
                            _res["content"].append(triggered)
                    else:
                        _res["content"].append(_content_res)
                    # print('by closing this, we\'re here now! (', _ind, ')')  # debug
                    # print((' ' if _ind - 1 < 0 else '') + line)  # debug
                    # print(' '*(_ind - 1 if _ind - 1 >= 0 else _ind) + '^^')  # debug
                    should_continue_without_bump = True
                    break
            if should_continue_without_bump:
                continue

            if len(_res["content"]) > 0 and type(_res["content"][-1]) == str:
                _res["content"][-1] += _line[_ind]
            else:
                _res["content"].append(_line[_ind])
                
            _ind += 1
        return start_pos, _res if root else {"type": "noclose", "content": []}

    while ind < len(p):
        line = p[ind]
        ind += 1
        if codeblock_match := CODEBLOCK_START.fullmatch(line):
            # print("CODEBLOCKSTART " + codeblock_match.group("lang"))
            mem = ""
            while ind < len(p):
                line = p[ind]
                if CODEBLOCK_END.fullmatch(line):
                    ind += 1
                    break
                mem += line
                ind += 1
            res.append({"type": "codeblock", "lang": codeblock_match.group("lang"), "content": mem})
        elif header_match := HEADER.fullmatch(line):
            # print("HEADER " + line[:-1])
            res.append({"type": "header", "content": header_match.group("content")})
        elif list_match := LIST.fullmatch(line):
            # print("LISTSTART " + line[:-1])
            mem = [list_match.group("content")]
            while ind < len(p):
                line = p[ind]
                if (flm := LIST.fullmatch(line)) or (line != "\n" and line.strip()[0] not in ['*', '-', '+']):
                    # print("LISTITEM " + line[:-1])
                    if flm:
                        mem.append(flm.group("content"))
                    else:
                        # print("CONTINUED")
                        mem[-1] += line
                elif line == "\n":
                    ind += 1
                    break
                ind += 1
            res.append({"type": "list", "content": mem})
        elif rlm := BLOCKQUOTE.fullmatch(line):
            # print("BQUOTESTART " + line[:-1])
            mem = [{"lv": len(rlm.group("lv")), "content": rlm.group("content")}]
            while ind < len(p):
                line = p[ind]
                if (flm := BLOCKQUOTE.fullmatch(line)) or (line != "\n" and line.strip()[0] != '>'):
                    # print("BQUOTEITEM " + line[:-1], end="")
                    if flm:
                        lv = len(flm.group("lv"))
                        # print(" LV " + str(lv))
                        mem.append({"lv": lv, "content": flm.group("content")})
                    else:
                        # print(" CONTINUED")
                        mem[-1]["content"] += line
                elif line == "\n":
                    ind += 1
                    break
                ind += 1
            res.append({"type": "blockquote", "content": mem})
        else:
            # print("IN PARAGRPAPH " + line[:-1])
            _, _res = paragraph_effect_parser(line)
            res.append(_res)
    return res

if __name__ == "__main__":
    import sys
    from pprint import pprint
    sys.setrecursionlimit(50)

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

paragraph ||**effect** is|| __*here__!
`hello ~~world~~ lol..

```py
asdf
asdfasdf
```
""".strip("\n")
    pprint(parse(test_string), compact=False, indent=2)
