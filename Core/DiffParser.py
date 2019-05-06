from Core.Diff import *
from Core.MergeDiff import MergeFileDiff


class MyList(List):
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self.idx = 0

    def next(self):
        try:
            ret = self[self.idx]
            self.idx += 1
            return ret
        except IndexError:
            return None

    def back(self):
        self.idx -= 1


def check(line, code, throws=True):
    if line.startswith(code):
        return True
    elif throws:
        raise Exception("parseGitDiff:" + code)
    return False


def parse_stats(line):
    # https://stackoverflow.com/questions/2529441/how-to-read-the-output-from-git-diff
    left, right = [n[1:] for n in line.split(b" ")[1:3]]

    if b"," in left:
        deletion_start_line, deletion_size = [int(n) for n in left.split(b",")]
    else:
        deletion_start_line, deletion_size = int(left), -1
    if b"," in right:
        addition_start_line, addition_size = [int(n) for n in right.split(b",")]
    else:
        addition_start_line, addition_size = int(right), -1

    return Stats(deletion_start_line, deletion_size, addition_start_line, addition_size)


def parse_line_type(string):
    if string == b" ":
        return LineType.CONTEXT
    if string == b"\\":
        return LineType.NO_ENDLINE_CONTEXT
    if string == b"+":
        return LineType.ADDITION
    if string == b"-":
        return LineType.DELETION
    raise Exception("Unknown LineType")


def parse_file_diff(lines: MyList):
    hunks = []
    line = lines.next()
    while line is not None:
        stats = parse_stats(line)
        difflines = []
        line = lines.next()

        while line is not None:
            if line.startswith(b"@@") or line.startswith(b"diff --git"):
                lines.back()
                break
            last_added_line = Line(parse_line_type(chr(line[0]).encode("utf8")), line[1:], False)
            difflines.append(last_added_line)
            line = lines.next()
            if line is not None:
                if line.startswith(b"\\"):
                    last_added_line.no_new_line = True
                    line = lines.next()

        hunks.append(Hunk(difflines, stats))
        if line is None or line.startswith(b"diff --git"):
            break

        line = lines.next()
    return hunks


def _parse_git_diff(lines: MyList, git_hash, message):
    file_diffs = []

    line = lines.next()
    while line is not None:
        diff = None
        similarity = None
        deleted_file = None
        new_file = None
        index = None
        minus = None
        plus = None
        rename_from = None
        rename_to = None

        if check(line, b"diff --git"): # TODO +++ ---
            diff = line
            line = lines.next()
        if check(line, b"similarity index", throws=False):
            similarity = line
            line = lines.next()
        if check(line, b"deleted file", throws=False):
            deleted_file = line
            line = lines.next()
        if check(line, b"new file", throws=False):
            new_file = line
            line = lines.next()
        if check(line, b"old mode", throws=False):  # TODO
            new_file = line
            line = lines.next()
        if check(line, b"new mode", throws=False):  # TODO
            new_file = line
            line = lines.next()
        if check(line, b"index", throws=False):
            index = line
            line = lines.next()
        if check(line, b"Binary files", throws=False):
            index = line
            line = lines.next()
            continue
        if check(line, b"---", throws=False):
            minus = line
            line = lines.next()
        if check(line, b"+++", throws=False):
            plus = line
            line = lines.next()
        if check(line, b"rename from", throws=False):
            rename_from = line
            line = lines.next()
        if check(line, b"rename to", throws=False):
            rename_to = line
            line = lines.next()

        if not line.startswith(b"diff --git"):
            lines.back()
            file_diffs.append(FileDiff(parse_file_diff(lines),
                                       Metadata(diff, deleted_file, new_file, index, similarity,
                                                minus, plus, rename_from, rename_to)))
            line = lines.next()

    return GitDiff(file_diffs, git_hash, message)


def parse_git_diff(diff: List[bytes], git_hash, message):
    mydiff = MyList()
    mydiff.extend(diff)
    return _parse_git_diff(mydiff, git_hash, message)
