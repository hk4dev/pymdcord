import re

t_HEADER = r"^\s*(?P<lv>#{1,3})\s(?P<content>\s*[^\s]+.*\n?)$"
t_LIST = r"^(?P<lv>\s*)([*\-+]\s|\d+\.\s)(?P<content>\s*[^\s]+.*\n?)$"
t_BLOCKQUOTE = r"^\s*(?P<lv>>+)(?P<content>\s*[^\s]+.*\n?)$"

t_CODEBLOCK_START = r"^`{3}(?P<lang>[^`\n]*)\n$"
t_CODEBLOCK_END = r"^\s*`{3}\n?$"

i_LINK = r"\[(?P<content>[^\n\]]*)\]\((?P<href>https?:\/\/[^\s\n\(\)]*)\)|(?P<barehref>https?:\/\/[^\s\n\(\)]*)"
i_MASKIMAGE = r"^\[(?P<content>.*)\]\(!(?P<href>https?:\/\/[^\s\n\(\)]*)\)\n?$"

HEADER = re.compile(t_HEADER)
LIST = re.compile(t_LIST)
BLOCKQUOTE = re.compile(t_BLOCKQUOTE)

CODEBLOCK_START = re.compile(t_CODEBLOCK_START)
CODEBLOCK_END = re.compile(t_CODEBLOCK_END)

ILINK = re.compile(i_LINK)

MASKIMAGE = re.compile(i_MASKIMAGE)

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
}

def parse(t: str):
    ind = 0
    p = t.splitlines(keepends=True)
    res = []

    def paragraph_effect_parser(
        _line: str,
        reserved: list[tuple[int, int, str, None | str, str]],  
        # (span-start, span-end, type, content(None if non-mask link), href)
        start_pos: int = 0, 
        triggered_by: str = None,
        type_as: str = "inline",
        root: bool = True):
        
        _res = {"type": type_as, "content": []}
        _ind = start_pos
        while _ind <= len(_line) - 1:
            should_continue_without_bump = False
            if reserved:
                for reserve in reserved:
                    if _ind == reserve[0]:
                        _ind = reserve[1]
                        _res["content"].append({"type": reserve[2], "content": reserve[3], "href": reserve[4]})
                        # TODO: link content inline parse later
                        should_continue_without_bump = True
            if should_continue_without_bump:
                continue
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
                    _ind, _content_res = paragraph_effect_parser(_line, reserved, _ind + len(triggered), triggered, trigger_type, False)
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
            res.append({"type": "header", "content": header_match.group("content"), "lv": len(header_match.group("lv"))})
        elif list_match := LIST.fullmatch(line):
            # print("LISTSTART " + line[:-1])
            mem = [{"content": list_match.group("content"), "lv": len(list_match.group("lv"))}]
            while ind < len(p):
                line = p[ind]
                if (flm := LIST.fullmatch(line)) or (line != "\n" and line.strip()[0] not in ['*', '-', '+']):
                    # print("LISTITEM " + line[:-1])
                    if flm:
                        mem.append({"content": flm.group("content"), "lv": len(flm.group("lv"))})
                    else:
                        # print("CONTINUED")
                        mem[-1]["content"] += line
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
        elif image_match := MASKIMAGE.fullmatch(line):
            res.append({"type": "image", "content": image_match.group("content"), "href": image_match.group("href")})
        else:
            # print("IN PARAGRPAPH " + line[:-1])
            reserves = []
            for rematch in ILINK.finditer(line):
                reserves.append(
                    (
                        rematch.start(), 
                        rematch.end(), 
                        'link' if 'barehref' in rematch.groupdict() else 'masklink', 
                        rematch.groupdict().get('content', None), 
                        rematch.group("href") if rematch.group("href") is not None else rematch.group("barehref")
                    )
                )
            _, _res = paragraph_effect_parser(line, reserves)
            res.append(_res)
    return res

if __name__ == "__main__":
    import sys
    from pprint import pprint
    sys.setrecursionlimit(50)

    test_string = """
# HEADER
# HEADER
### HEADER
### HEADER
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

here:https://psw.kr is my link!
or you want some [masked link](https://psw.kr)??

[this is image..](!https://test.image)
""".strip("\n")
    pprint(parse(test_string), compact=False, indent=2)
