from pymdcord import parse
from pprint import pprint


def case(t: str):
    parsed = parse(t=t, debug=True)
    pprint(object=parsed, compact=False, indent=2)
    print("---------------")
    print("".join(map(lambda x: x.md(), parsed)))
    pprint(list(map(lambda x: x.md(), parsed)))
    print("\n\n\n")


case(
    """# Markdown Splitting Test
asdfasdfasdfasdfasdf asdfasdf...

* one
* two
* three
1. four
  2. five
  3. six

> blockquote?
> asdf
 
> asdf"""
)

case(
    """\
>asdf

>>>asdf
>>>asdf
"""
)
