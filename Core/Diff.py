from collections import OrderedDict
from enum import Enum
from typing import List, Iterator, Generator


class Source(Enum):
    LEFT = "left"
    RIGHT = "right"


class LineType(Enum):
    CONTEXT = b" "
    NO_ENDLINE_CONTEXT = b"\\"
    ADDITION = b"+"
    DELETION = b"-"
    ADD_DEL = b"+-"


def join(enumerable):
    res = b""
    for e in enumerable:
        res += e.to_bytes()
    return res


def nformat(elt):
    if elt is None:
        return b""
    else:
        return elt + b"\n"


def to_string(bytes_array):
    return bytes_array.decode("utf8", "replace")


class Line:
    def __init__(self, line_type: LineType, content: bytes, no_new_line):
        self.type = line_type
        self.content = content.rstrip(b"\n").rstrip(b"\r")
        self.no_new_line = no_new_line

    def to_bytes(self):
        if self.no_new_line:
            return self.type.value + self.content + b"\n" + b"\\ No newline at end of file"
        else:
            return self.type.value + self.content

    def __str__(self):
        return to_string(self.to_bytes())

    def is_addition(self):
        return self.type == LineType.ADDITION

    def is_deletion(self):
        return self.type == LineType.DELETION

    def is_context(self):
        return self.type == LineType.CONTEXT or self.type == LineType.NO_ENDLINE_CONTEXT


class Stats:
    def __init__(self, deletion_start_line: int, deletion_size: int, addition_start_line: int, addition_size: int):
        self.deletion_start_line = deletion_start_line
        self.deletionSize = deletion_size
        self.addition_start_line = addition_start_line
        self.additionSize = addition_size

    def to_bytes(self):
        ret = b"@@ -" + str(self.deletion_start_line).encode("utf8")
        if self.deletionSize != -1:
            ret += b"," + str(self.deletionSize).encode("utf8")
        ret += b" +" + str(self.addition_start_line).encode("utf8")
        if self.additionSize != -1:
            ret += b"," + str(self.additionSize).encode("utf8")
        return ret + b" @@\n"

    def __str__(self):
        return to_string(self.to_bytes())


class Hunk:
    def __init__(self, lines: List[Line], stats: Stats):
        self.lines = lines
        self.stats = stats

    def to_bytes(self):
        return self.stats.to_bytes() + b"\n".join(l.to_bytes() for l in self.lines) + b"\n"

    def __str__(self):
        return to_string(self.to_bytes())


class Metadata:
    def __init__(self, diff, deleted_file, new_file, index, similarity, minus, plus, rename_from, rename_to):
        self.diff = diff
        self.deleted_file = deleted_file
        self.new_file = new_file
        self.index = index
        self.similarity = similarity
        self.minus = minus
        self.plus = plus
        self.rename_from = rename_from
        self.rename_to = rename_to

    def is_trivial(self):  # returns False if there are elements which wont be dealt with in v0.1
        return self.deleted_file is None \
               and self.new_file is None \
               and self.index is None \
               and self.similarity is None \
               and self.rename_from is None \
               and self.rename_to is None

    def to_bytes(self):
        ret = self.diff + b"\n"
        ret += nformat(self.deleted_file)
        ret += nformat(self.new_file)
        ret += nformat(self.index)
        ret += nformat(self.similarity)
        ret += nformat(self.minus)
        ret += nformat(self.plus)
        ret += nformat(self.rename_from)
        ret += nformat(self.rename_to)

        return ret

    def __str__(self):
        return to_string(self.to_bytes())


class FileDiff:
    def __init__(self, hunks: List[Hunk], metadata: Metadata):
        self.hunks = hunks
        self.metadata = metadata

    def to_bytes(self):
        if len(self.hunks) == 1:
            if self.hunks[0].stats.addition_start_line == 0 and self.hunks[0].stats.additionSize == 0:
                self.metadata.plus = b"+++ /dev/null"
            if self.hunks[0].stats.deletion_start_line == 0 and self.hunks[0].stats.deletionSize == 0:
                self.metadata.minus = b"--- /dev/null"
        return self.metadata.to_bytes() + join(self.hunks)

    def __str__(self):
        return to_string(self.to_bytes())


class GitDiff:
    def __init__(self, file_diffs: List[FileDiff], git_hash, message):
        self.hash = git_hash
        self.message = message
        self.file_diffs: OrderedDict[str, FileDiff] = OrderedDict()
        for file_diff in file_diffs:
            if file_diff.metadata.plus != b"+++ /dev/null":
                self.file_diffs[file_diff.metadata.plus.lstrip(b"+++ b/")] = file_diff
            else:
                self.file_diffs[file_diff.metadata.minus.lstrip(b"--- a/")] = file_diff

    def to_bytes(self):
        return join(self.file_diffs.values())

    def __str__(self):
        return to_string(self.to_bytes())
