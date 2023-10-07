from dataclasses import dataclass, field
from typing import Literal, Union

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

    def md(self) -> str:
        return "#" * self.lv + " " + self.content


@dataclass
class c_CODEBLOCK(c):
    selftype = "codeblock"
    lang: str | None
    content: str

    def md(self) -> str:
        stripped = self.content.strip("\n")
        return f"```{self.lang}\n{stripped}\n```"


@dataclass
class c_LISTITEM(b):
    lv: int
    content: str
    sortof: str

    def md(self) -> str:
        newlist = ("\n" + (" " * (self.lv + 2))).join(
            self.content.strip("\n").split("\n")
        )
        return f"{' '*self.lv}{self.sortof}{newlist}"


@dataclass
class c_LIST(c):
    selftype = "list"
    content: list[c_LISTITEM] = field(default_factory=list)

    def md(self) -> str:
        return "\n".join(map(lambda x: x.md(), self.content)) + "\n"


@dataclass
class c_BLOCKQUOTEITEM(b):
    lv: int
    content: str

    def md(self) -> str:
        return ">" + ("\n> ".join(self.content.strip("\n").split("\n")))


@dataclass
class c_BLOCKQUOTE(c):
    selftype = "blockquote"
    content: list[c_BLOCKQUOTEITEM]

    def md(self) -> str:
        return "\n\n".join(list(map(lambda x: x.md(), self.content))) + "\n"


@dataclass
class c_IMAGE(c):
    selftype = "image"
    content: str | None
    href: str

    def md(self) -> str:
        return self.href


@dataclass
class c_LINKS(c):
    selftype = "link"
    content: str | None
    href: str

    def md(self) -> str:
        if self.content is None:
            return self.href
        else:
            return f"[{self.content}]({self.href})"

    ...


@dataclass
class c_INLINECONTENT(c):
    selftype: INLINETYPE
    content: list[Union["c_INLINECONTENT", c_LINKS, str]] = field(default_factory=list)

    def md(self) -> str:
        mded = []
        for item in self.content:
            if not isinstance(item, str):
                mded.append(item.md())
            else:
                mded.append(item)
        bald = "".join(mded)
        if self.selftype == "bold":
            return f"**{bald}**"
        elif self.selftype == "italic":
            return f"_{bald}_"
        elif self.selftype == "underline":
            return f"__{bald}__"
        elif self.selftype == "strikethrough":
            return f"~~{bald}~~"
        elif self.selftype == "code":
            return f"`{bald}`"
        elif self.selftype == "codeblock":
            return f"```{bald}```"
        elif self.selftype == "secret":
            return f"||{bald}||"
        else:
            return bald


@dataclass
class c_INLINE(c):
    selftype = "inline"
    content: list[c_INLINECONTENT | c_LINKS | str] = field(default_factory=list)

    def md(self) -> str:
        mded = []
        for item in self.content:
            if not isinstance(item, str):
                mded.append(item.md())
            else:
                mded.append(item)
        return "".join(mded)


ALLTYPE = c_HEADER | c_CODEBLOCK | c_BLOCKQUOTE | c_LIST | c_IMAGE | c_INLINE
