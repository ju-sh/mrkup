"""
core mrkup module
"""

from typing import List, Optional, Union, TextIO
import abc


def _stringify(level: int,  # pylint: disable=too-many-branches
               indent: Optional[int],
               taginfo: dict,
               tag_start: str = "",
               tag_end: str = "/") -> str:
    """
    For use by the strinfigy() methods of Tag and PI objects

    level: indentation level
    indent: number of spaces per indentation level
    taginfo: attributes of the Tag object being stringified
    tag_start: starting of opening tag before tag name
    tag_end: ending of opening tag after tag name

    For example, in

        <?tst echo "hello" !>

    "?" is tag_start
    "!" is tag_end
    """
    # start opening tag
    if indent is None:
        space = ""
    else:
        space = "\n" + (level * (' ' * indent))
    tag_str = f"{space}<{tag_start}{taginfo['name']}"

    for key in taginfo['attrs']:
        if taginfo['attrs'][key] is None:
            tag_str += f" {key}"
        else:
            tag_str += f" {key}=\"{taginfo['attrs'][key]}\""

    # end opening tag
    if taginfo["close"] is None:
        # if self-closed tag
        tag_str += f" {tag_end}>"
        return tag_str

    tag_str += f"{tag_start}>"
    if taginfo["close"] is False:
        return tag_str

    # children
    if taginfo["children"]:
        for child in taginfo["children"]:
            if isinstance(child, Node):
                # handle non-strings
                tag_str += child.dumps(level+1, indent)
            else:
                # handle plain strings
                if indent is not None:
                    tag_str += space + " " * indent
                tag_str += str(child)
        if indent is not None:
            tag_str += "\n"

    # closing tag
    if indent is not None:
        tag_str += level * (' ' * indent)
    tag_str += f"<{tag_end}{taginfo['name']}>"

    return tag_str


class Node(abc.ABC):
    """
    Abstract class representing all supported nodes except plain strings.
    Including comments and tags
    """
    @abc.abstractmethod
    def dumps(self, level: int, indent: Optional[int]) -> str:
        """
        Abstract method that returns a stringified form of the node
        """

    @abc.abstractmethod
    def dump(self, fptr: TextIO, level: int, indent: Optional[int]) -> None:
        """
        Abstract method that writes a stringified form of the node to fptr
        """


class Comment(Node):
    """
    Represent a comment.

    Attributes:
      text: contents of the comment
    """
    def __init__(self, text: str):
        self.text = text

    def __repr__(self):
        return f"Comment({self.text!r})"

    def __str__(self):
        return f"<!--{self.text}-->"

    def dumps(self,
              level: int = 0,
              indent: Optional[int] = 2) -> str:
        """
        Format the comment to a string.

        Value of level is ignored if indent is None.

        Args:
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.

        Returns:
          A stringified form of the comment.
        """
        if indent is None:
            return str(self)
        space = "\n" + level * (' ' * indent)
        return f"{space}{self}"

    def dump(self,
             fptr: TextIO,
             level: int = 0,
             indent: Optional[int] = 2) -> None:
        """
        Write a string form of the comment to fptr.

        Value of level is ignored if indent is None.

        Args:
          fptr: A writable stream
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.
        """
        fptr.write(self.dumps(level, indent))


class NamedNode(Node):
    """
    Abstract method representing all nodes which has a name and can have
    attributes.
    """
    def __init__(self,
                 name: str,
                 attrs: Optional[dict]):
        self.name = name
        if attrs is None:
            self.attrs = {}
        else:
            self.attrs = attrs

    def __str__(self):
        return self.name


class Tag(NamedNode):
    """
    Represent a tag

    Attributes:
      name: name of tag
      attrs: attributes of tag as a dictionary. Attributes without
        value can have their value as None
      children: child tags, comments and text of the tag as a list
      close: determines if the tag is explicitly closed (True),
        self-closed (None) or not closed (False)

    Examples:
    >>> tag = Tag(name="input",
                  attrs={"type": "text", "required": None}, close=None)
    >>> tag.dumps()
    <input type="text" required />

    >>> tag = Tag(name="br", close=False)
    >>> tag.dumps()
    <br>

    >>> tag = Tag(name="p", children=["Hello"])
    >>> tag.dumps()
    <p>
      Hello
    </p>
    """
    def __init__(self,
                 name: str,
                 attrs: dict = None,
                 children: List[Union[Node, str]] = None,
                 close: Optional[bool] = True):
        super().__init__(name, attrs)
        if close is not True and children is not None:
            raise ValueError("Only closed tags can have children")
        if children is None:
            self.children = []
        else:
            self.children = children
        self.close = close

    def __repr__(self):
        return (f"Tag({self.name!r}, {self.attrs!r}, {self.children!r}, "
                f"{self.close!r})")

    def dumps(self,
              level: int = 0,
              indent: Optional[int] = 2) -> str:
        """
        Format the tag and its children to a string.

        Value of level is ignored if indent is None.

        Args:
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.

        Returns:
          A stringified form of the tag with all its children.
        """
        taginfo = {"name": self.name,
                   "attrs": self.attrs,
                   "children": self.children,
                   "close": self.close}
        return _stringify(level, indent, taginfo)

    def dump(self,
             fptr: TextIO,
             level: int = 0,
             indent: Optional[int] = 2) -> None:
        """
        Write a string form of the tag to fptr.

        Value of level is ignored if indent is None.

        Args:
          fptr: A writable stream
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.
        """
        fptr.write(self.dumps(level, indent))


class PI(NamedNode):
    """
    Represent a processing instruction

    Attributes:
      name: name of tag
      attrs: attributes of tag as a dictionary. Attributes without
        value can have their value as None
    """
    def __init__(self,
                 name: str,
                 attrs: dict = None):
        super().__init__(name, attrs)

    def __repr__(self):
        return f"PI({self.name!r}, {self.attrs!r})"

    def dumps(self,
              level: int = 0,
              indent: Optional[int] = 2) -> str:
        """
        Format the processing instruction to a string.

        Value of level is ignored if indent is None.

        Args:
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.

        Returns:
          A stringified form of the processing instruction.
        """
        taginfo = {"name": self.name,
                   "attrs": self.attrs,
                   "children": None,
                   "close": False}
        return _stringify(level, indent, taginfo, "?", "?")

    def dump(self,
             fptr: TextIO,
             level: int = 0,
             indent: Optional[int] = 2) -> None:
        """
        Write a string form of the processing instruction to fptr.

        Value of level is ignored if indent is None.

        Args:
          fptr: A writable stream
          level: indentation level
          indent: number of spaces per indentation level. None if
            not to be pretty printed.
        """
        fptr.write(self.dumps(level, indent))
