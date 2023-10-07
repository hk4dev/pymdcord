import re
from .classes import (
    ALLTYPE,
    INLINETYPE,
    c_HEADER,
    c_CODEBLOCK,
    c_BLOCKQUOTE,
    c_BLOCKQUOTEITEM,
    c_LIST,
    c_LISTITEM,
    c_IMAGE,
    c_INLINE,
    c_INLINECONTENT,
    c_LINKS,
)
from typing import TypeVar
from logging import getLogger, DEBUG, WARNING, StreamHandler

logger = getLogger("pymdcord")
logger.addHandler(StreamHandler())
logger.setLevel(WARNING)

t_HEADER = r"^\s*(?P<lv>#{1,3})\s(?P<content>\s*[^\s]+.*\n?)$"
t_LIST = r"^(?P<lv>\s*)(?P<sortof>[*\-+]\s|\d+\.\s)(?P<content>\s*[^\s]+.*\n?)$"
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

INLINE_TRIGGERS: dict[INLINETYPE, list[str]] = {
    "bold": ["**"],
    "underline": ["__"],
    "italic": ["*", "_"],
    "strikethrough": ["~~"],
    "code": ["`"],
    "codeblock": ["```"],
    "secret": ["||"],
}

INLINE_REGEXS = {
    "link": ILINK,
}

PARAGRAPH_EFFECT_PARSER_RETURN = TypeVar(
    "PARAGRAPH_EFFECT_PARSER_RETURN", bound=c_INLINE | c_INLINECONTENT
)


def parse(t: str, debug: bool = False) -> list[ALLTYPE]:
    if debug:
        logger.setLevel(DEBUG)
    ind = 0
    p = t.splitlines(keepends=True)
    res: list[ALLTYPE] = []

    def paragraph_effect_parser(
        _line: str,
        reserved: list[tuple[int, int, None | str, str]],
        # (span-start, span-end, content(None if non-mask link), href)
        start_pos: int = 0,
        triggered_by: str | None = None,
        type_as: INLINETYPE = "inline",
        root: PARAGRAPH_EFFECT_PARSER_RETURN = c_INLINE(),
    ) -> tuple[int, PARAGRAPH_EFFECT_PARSER_RETURN]:
        _res: PARAGRAPH_EFFECT_PARSER_RETURN = root
        _ind = start_pos
        while _ind <= len(_line) - 1:
            should_continue_without_bump = False
            if reserved:
                for reserve in reserved:
                    if _ind == reserve[0]:
                        _ind = reserve[1]
                        _res.content.append(
                            c_LINKS(content=reserve[2], href=reserve[3])
                        )
                        # TODO: link content inline parse later
                        should_continue_without_bump = True
            if should_continue_without_bump:
                continue
            for trigger_type, trigger in INLINE_TRIGGERS.items():
                if (triggered := _line[_ind : _ind + len(trigger[0])]) in trigger:
                    if triggered_by in trigger:
                        logger.debug(f"closed by {triggered} {_ind}")  # debug
                        logger.debug((" " if _ind - 1 < 0 else "") + line)  # debug
                        logger.debug(
                            " " * (_ind - 1 if _ind - 1 >= 0 else _ind) + "^^"
                        )  # debug
                        _res.selftype = type_as
                        return _ind + len(triggered), _res
                    logger.debug(f"opened by {triggered} {_ind}")  # debug
                    logger.debug((" " if _ind - 1 < 0 else "") + line)  # debug
                    logger.debug(
                        " " * (_ind - 1 if _ind - 1 >= 0 else _ind) + "^^"
                    )  # debug
                    _ind, _content_res = paragraph_effect_parser(
                        _line,
                        reserved,
                        _ind + len(triggered),
                        triggered,
                        trigger_type,
                        c_INLINECONTENT("noclose", []),
                    )
                    if _content_res.selftype == "noclose":
                        if len(_res.content) > 0 and type(_res.content[-1]) == str:
                            _res.content[-1] += triggered  # type: ignore
                        else:
                            _res.content.append(triggered)
                        logger.debug(f"unclosed, rolling back to ( {_ind} )")  # debug
                    else:
                        _res.content.append(_content_res)  # type: ignore
                        logger.debug(
                            f"by closing this, we're here now! ( {_ind} )"
                        )  # debug
                    logger.debug((" " if _ind - 1 < 0 else "") + line)  # debug
                    logger.debug(
                        " " * (_ind - 1 if _ind - 1 >= 0 else _ind) + "^^"
                    )  # debug
                    should_continue_without_bump = True
                    break
            if should_continue_without_bump:
                continue

            if len(_res.content) > 0 and type(_res.content[-1]) == str:
                _res.content[-1] += _line[_ind]  # type: ignore
            else:
                _res.content.append(_line[_ind])

            _ind += 1
        if triggered_by is None:
            logger.debug("PARAGRAPH FINISH")
        return start_pos, _res

    while ind < len(p):
        line = p[ind]
        ind += 1
        if codeblock_match := CODEBLOCK_START.fullmatch(line):
            logger.debug("CODEBLOCKSTART " + codeblock_match.group("lang"))
            mem = ""
            while ind < len(p):
                line = p[ind]
                if CODEBLOCK_END.fullmatch(line):
                    ind += 1
                    break
                mem += line
                ind += 1
            res.append(
                c_CODEBLOCK(
                    lang=codeblock_match.group("lang"),
                    content=mem,
                )
            )
        elif header_match := HEADER.fullmatch(line):
            logger.debug("HEADER " + line[:-1])
            res.append(
                c_HEADER(
                    content=header_match.group("content"),
                    lv=len(header_match.group("lv")),
                )
            )
        elif list_match := LIST.fullmatch(line):
            logger.debug("LISTSTART " + line[:-1])
            mem = [
                c_LISTITEM(
                    lv=len(list_match.group("lv")),
                    content=list_match.group("content"),
                    sortof=list_match.group("sortof"),
                )
            ]
            while ind < len(p):
                line = p[ind]
                if (flm := LIST.fullmatch(line)) or (line != "\n"):
                    if flm:
                        logger.debug(
                            "LISTITEM LV " + str(len(flm.group("lv"))) + " " + line[:-1]
                        )
                        mem.append(
                            c_LISTITEM(
                                lv=len(flm.group("lv")),
                                content=flm.group("content"),
                                sortof=flm.group("sortof"),
                            )
                        )
                    else:
                        logger.debug("CONTINUED LISTITEM " + line[:-1])
                        mem[-1].content += line
                elif line == "\n":
                    break
                ind += 1
            res.append(c_LIST(content=mem))
        elif rlm := BLOCKQUOTE.fullmatch(line):
            logger.debug("BQUOTESTART " + line[:-1])
            mem = [
                c_BLOCKQUOTEITEM(lv=len(rlm.group("lv")), content=rlm.group("content"))
            ]
            while ind < len(p):
                line = p[ind]
                if (flm := BLOCKQUOTE.fullmatch(line)) or (
                    line != "\n" and line.strip()[0] != ">"
                ):
                    if flm:
                        lv = len(flm.group("lv"))
                        logger.debug("BQUOTE LV " + str(lv) + " " + line[:-1])
                        mem.append(
                            c_BLOCKQUOTEITEM(lv=lv, content=flm.group("content"))
                        )
                    else:
                        logger.debug("CONTINUED BQUOTEITEM " + line[:-1])
                        mem[-1].content += line
                elif line == "\n":
                    break
                ind += 1
            res.append(c_BLOCKQUOTE(content=mem))
        elif image_match := MASKIMAGE.fullmatch(line):
            logger.debug("MASKEDIMAGE " + line[:-1])
            res.append(
                c_IMAGE(
                    content=image_match.group("content"),
                    href=image_match.group("href"),
                )
            )
        else:
            logger.debug("IN PARAGRPAPH " + line[:-1])
            reserves = []
            for rematch in ILINK.finditer(line):
                reserves.append(
                    (
                        rematch.start(),
                        rematch.end(),
                        rematch.groupdict().get("content", None),
                        rematch.group("href")
                        if rematch.group("href") is not None
                        else rematch.group("barehref"),
                    )
                )
            _, _res = paragraph_effect_parser(line, reserves, root=c_INLINE())
            res.append(_res)
    return res


if __name__ == "__main__":
    import sys
    from pprint import pprint

    sys.setrecursionlimit(50)

    logger.setLevel(DEBUG)

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
""".strip(
        "\n"
    )
    parsed = parse(t=test_string)
    pprint(object=parsed, compact=False, indent=2)
    print("---------------")
    print("".join(map(lambda x: x.md(), parsed)))
    pprint(list(map(lambda x: x.md(), parsed)))
