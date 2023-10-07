from dataclasses import dataclass, field
from typing import Literal

INLINETYPE = Literal[
    "inline",
    "noclose",
    "bold",
    "underline",
    "italic",
    "strikethrough",
    "code",
    "codeblock",
    "secret",
]


class b:
    def dict(self):
        return self.__dict__

    def __repr__(self) -> str:
        return str(self.dict())


class c(b):
    selftype: Literal[
        "header",
        "codeblock",
        "list",
        "blockquote",
        "image",
        "link",
    ] | INLINETYPE

    def dict(self):
        return {**self.__dict__, "type": self.selftype}


@dataclass
class c_HEADER(c):
    selftype = "header"
    content: str
    lv: int


@dataclass
class c_CODEBLOCK(c):
    selftype = "codeblock"
    lang: str | None
    content: str


@dataclass
class c_LISTITEM(b):
    lv: int
    content: str


@dataclass
class c_LIST(c):
    selftype = "list"
    content: list[c_LISTITEM] = field(default_factory=list)


@dataclass
class c_BLOCKQUOTEITEM(b):
    lv: int
    content: str


@dataclass
class c_BLOCKQUOTE(c):
    selftype = "blockquote"
    content: list[c_BLOCKQUOTEITEM]


@dataclass
class c_IMAGE(c):
    selftype = "image"
    content: str | None
    href: str


@dataclass
class c_LINKS(c):
    selftype = "link"
    content: str | None
    href: str


@dataclass
class c_INLINECONTENT(c):
    selftype: INLINETYPE
    content: list["c_INLINECONTENT" | c_LINKS | str] = field(default_factory=list)


@dataclass
class c_INLINE(c):
    selftype = "inline"
    content: list[c_INLINECONTENT | c_LINKS | str] = field(default_factory=list)


ALLTYPE = c_HEADER | c_CODEBLOCK | c_BLOCKQUOTE | c_LIST | c_IMAGE | c_INLINE
