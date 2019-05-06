from typing import Optional, List, Dict

from Core.Diff import Line, FileDiff, LineType, Source, GitDiff


class MergeLine:
    def __init__(self, line: Line, source: Source, left_index: Optional[int], middle_index: Optional[int],
                 right_index: Optional[int]):
        self.conflicts = False
        self.line = Line(line.type, line.content, line.no_new_line)
        self.source = source
        self.left_index = left_index
        self.middle_index = middle_index
        self.right_index = right_index
        self.move = False

    def to_bytes(self):
        left = "_" if self.left_index is None else self.left_index
        right = "_" if self.right_index is None else self.right_index
        middle = "_" if self.middle_index is None else self.middle_index

        return "{} {} {} {} {}".format(str(self.source.name)[0], left, middle, right,
                                       self.line)

    def offset(self):
        if (self.source == Source.LEFT and self.line.type == LineType.ADDITION) \
                or (self.source == Source.RIGHT and self.line.type == LineType.DELETION):
            return -1

        if (self.source == Source.LEFT and self.line.type == LineType.DELETION) \
                or (self.source == Source.RIGHT and self.line.type == LineType.ADDITION):
            return 1

        return 0

    def is_add_del(self):
        return self.line.type == LineType.ADD_DEL

    def is_addition(self):
        return self.line.is_addition() or (self.is_add_del() and self.middle_index is not None)

    def is_deletion(self):
        return self.line.is_deletion() or (self.is_add_del() and self.middle_index is not None)

    def is_context(self):
        return self.line.type == LineType.CONTEXT or self.line.type == LineType.NO_ENDLINE_CONTEXT

    def present_on_left(self):
        return (self.left_index is not None) or (self.middle_index is not None)

    def present_on_right(self):
        return (self.middle_index is not None) or (self.right_index is not None)

    def dump_as_left(self):

        if self.left_index is None and self.middle_index is not None:
            type = LineType.ADDITION
        elif self.left_index is not None and self.middle_index is None:
            type = LineType.DELETION
        elif self.line.type == LineType.NO_ENDLINE_CONTEXT:
            type = LineType.NO_ENDLINE_CONTEXT
        else:
            type = LineType.CONTEXT

        if self.present_on_left():
            return self.left_index, self.middle_index, Line(type, self.line.content, self.line.no_new_line)
        else:
            return None, None, ""

    def dump_as_right(self):

        if self.middle_index is None and self.right_index is not None:
            type = LineType.ADDITION
        elif self.middle_index is not None and self.right_index is None:
            type = LineType.DELETION
        elif self.line.type == LineType.NO_ENDLINE_CONTEXT:
            type = LineType.NO_ENDLINE_CONTEXT
        else:
            type = LineType.CONTEXT
        if self.present_on_right():
            return self.middle_index, self.right_index, Line(type, self.line.content, self.line.no_new_line)
        else:
            return None, None, ""


def flatten(file_diff: FileDiff, source):
    merge_lines = []
    for hunk in file_diff.hunks:
        stats = hunk.stats
        left_index = stats.deletion_start_line
        right_index = stats.addition_start_line
        for line in hunk.lines:
            if source == Source.LEFT:
                if line.is_deletion():
                    left_index += 1
                    merge_lines.append(MergeLine(line, source, left_index - 1, None, None))
                elif line.is_addition():
                    right_index += 1
                    merge_lines.append(MergeLine(line, source, None, right_index - 1, None))
                else:
                    left_index += 1
                    right_index += 1
                    merge_lines.append(MergeLine(line, source, left_index - 1, right_index - 1, None))
            else:
                if line.is_deletion():
                    left_index += 1
                    merge_lines.append(MergeLine(line, source, None, left_index - 1, None))
                elif line.is_addition():
                    right_index += 1
                    merge_lines.append(MergeLine(line, source, None, None, right_index - 1))
                else:
                    left_index += 1
                    right_index += 1
                    merge_lines.append(MergeLine(line, source, None, left_index - 1, right_index - 1))
    return merge_lines


def compute_stats(array, stat_index, source):
    left_end = None
    right_end = None
    for i in range(len(array) - 1, stat_index, -1):
        if source == Source.LEFT:
            start, end = array[i].left_index, array[i].middle_index
        else:
            start, end = array[i].middle_index, array[i].right_index
        if left_end is None and start is not None:
            left_end = start
        if right_end is None and end is not None:
            right_end = end
        array[i] = array[i].print_back(source)

    left_start, right_start = array[stat_index]
    if left_end is None:
        left_end = left_start
    if right_end is None:
        right_end = right_start

    left_size = left_end - left_start + 1
    right_size = right_end - right_start + 1

    return "@@ -{},{} +{},{} @@\n".format(left_start, left_size, right_start, right_size)


class MergeFileDiff:
    def __init__(self, left_file_diff: FileDiff, right_file_diff: FileDiff):
        self.conflicts = False
        if left_file_diff is None:
            left_file_diff = FileDiff([], right_file_diff.metadata)
        if right_file_diff is None:
            right_file_diff = FileDiff([], left_file_diff.metadata)

        self.merge_lines: List[MergeLine] = []
        self.load(left_file_diff, right_file_diff)

    def load(self, left_file_diff: FileDiff, right_file_diff: FileDiff):
        """
        * Orders lines following the "middle_index" order.
        * If there is no middle_index (left deletion, right addition), insert left deletions first, then right
        additions.
        * If a line is present both in the left and the right files, keep only additions and deletions, unless they are
        both context, in which case keep only one.
        * If a line is both added in the left file and deleted in the right file, keep one and update its type to
        ADD_DEL.

        * right_index (for lines from left file) and left_index (for lines from right file) are computed using offsets
        keeping track of how many deletions/additions happened until now (to compute how far away left/right indexes are
        from middle_index).
        """
        left_lines = flatten(left_file_diff, Source.LEFT)
        right_lines = flatten(right_file_diff, Source.RIGHT)

        left_idx = 0
        right_idx = 0

        left_offset = 0
        right_offset = 0

        while True:
            if len(left_lines) == 0:
                left_idx = 1
            elif len(right_lines) == 0:
                right_idx = 1
            else:
                left: MergeLine = left_lines[left_idx]
                right: MergeLine = right_lines[right_idx]

                if left.middle_index is None:  # Left deletion
                    left_offset += left.offset()
                    self.merge_lines.append(left)
                    left_idx += 1
                elif right.middle_index is None:  # Right addition
                    right_offset += right.offset()
                    self.merge_lines.append(right)
                    right_idx += 1
                elif left.middle_index < right.middle_index:
                    left_offset += left.offset()
                    left.right_index = left.middle_index + right_offset
                    self.merge_lines.append(left)
                    left_idx += 1
                elif left.middle_index > right.middle_index:
                    right_offset += right.offset()
                    right.left_index = right.middle_index + left_offset
                    self.merge_lines.append(right)
                    right_idx += 1
                else:
                    left_idx += 1
                    right_idx += 1
                    self.conflicts = True
                    left.conflicts = True
                    right.conflicts = True
                    if not left.is_context():
                        left_offset += left.offset()
                        if not right.is_context():
                            # If both left and right are significant, we have a left addition and a right deletion
                            right_offset += right.offset()
                            left.line.type = LineType.ADD_DEL
                        else:
                            left.right_index = left.middle_index + right_offset
                        self.merge_lines.append(left)
                    elif not right.is_context():
                        right_offset += right.offset()
                        if left.is_context():
                            right.left_index = right.middle_index + left_offset
                        self.merge_lines.append(right)
                    else:
                        left.right_index = right.right_index
                        self.merge_lines.append(left)

            if left_idx >= len(left_lines):
                while right_idx < len(right_lines):
                    right = right_lines[right_idx]
                    if right.middle_index is not None:
                        right.left_index = right.middle_index + left_offset
                    self.merge_lines.append(right)
                    right_idx += 1
                break
            if right_idx >= len(right_lines):
                while left_idx < len(left_lines):
                    left = left_lines[left_idx]
                    if left.middle_index is not None:
                        left.right_index = left.middle_index + right_offset
                    self.merge_lines.append(left)
                    left_idx += 1
                break

    def reset(self):
        for i in range(0, len(self.merge_lines)):
            if self.merge_lines[i].move:
                self.move(i)

    def swap_all(self):
        for i in range(0, len(self.merge_lines)):
            self.move(i)

    def move_left(self):
        for i in range(0, len(self.merge_lines)):
            line = self.merge_lines[i]
            if line.is_add_del():
                if not line.move:
                    self.move(i)
            elif line.source == Source.LEFT and line.move or line.source == Source.RIGHT and not line.move:
                self.move(i)

    def move_right(self):
        for i in range(0, len(self.merge_lines)):
            line = self.merge_lines[i]
            if line.is_add_del():
                if not line.move:
                    self.move(i)
            elif line.source == Source.LEFT and not line.move or line.source == Source.RIGHT and line.move:
                self.move(i)

    def move(self, line_index):
        line: MergeLine = self.merge_lines[line_index]
        if line.is_context():
            return
        line.move = not line.move

        if line.middle_index is None:
            offset = 1
            for i in range(line_index, -1, -1):
                idx = self.merge_lines[i].middle_index
                if idx is not None:
                    line.middle_index = idx + 1
                    break
            else:
                line.middle_index = 1
        else:
            line.middle_index = None
            offset = -1

        for i in range(line_index + 1, len(self.merge_lines)):
            line = self.merge_lines[i]
            if line.middle_index is not None:
                line.middle_index += offset

    def make_stats(self, buffers):
        res = []
        for buffer in buffers:
            left_start = buffer[0][0]
            right_start = buffer[0][1]
            left_end = None
            right_end = None
            for i in range(len(buffer) - 1, 0, -1):
                left, right, line = buffer[i]
                if left_end is None and left is not None and line.type != LineType.NO_ENDLINE_CONTEXT:
                    left_end = left
                if right_end is None and right is not None and line.type != LineType.NO_ENDLINE_CONTEXT:
                    right_end = right
                if left_start is None and not (line.is_addition() or line.type == LineType.NO_ENDLINE_CONTEXT):
                    left_start = 1
                if right_start is None and not (line.is_deletion() or line.type == LineType.NO_ENDLINE_CONTEXT):
                    right_start = 1
            if left_start is None:  # Added file
                left_start = 0
                left_size = 0
            else:
                if left_end is None:
                    left_end = left_start
                left_size = left_end - left_start + 1
            if right_start is None:  # Deleted file
                right_start = 0
                right_size = 0
            else:
                if right_end is None:
                    right_end = right_start
                right_size = right_end - right_start + 1

            res.append("@@ -{},{} +{},{} @@".format(left_start, left_size, right_start, right_size).encode("utf8"))
            for elt in buffer:
                _, _, line = elt
                res.append(line.to_bytes())
        return res

    def process(self, buffer):
        res = []
        chunk = []
        prefix = []
        prefix_done = False
        postfix = []
        for elt in buffer:
            _, _, line = elt
            if line.is_context():
                if prefix_done:
                    postfix.append(elt)
                    if len(postfix) == 7:
                        chunk += postfix[:3]
                        res.append(chunk)

                        chunk = []
                        prefix = postfix[-3:]
                        prefix_done = False
                        postfix = []
                else:
                    prefix.append(elt)
                    if len(prefix) > 3:
                        prefix = prefix[1:]
            else:
                if not prefix_done:
                    chunk += prefix
                prefix_done = True
                chunk += postfix
                postfix = []
                chunk.append(elt)
        if prefix_done:
            chunk += postfix[:3]
            res.append(chunk)
        return res

    def clean_raw_res(self, res):
        buffers = []
        last_idx = None
        buffer = []
        for elt in res:
            left_idx, right_idx, line = elt

            if last_idx is not None:
                far_idx = (left_idx is not None and last_idx[0] is not None and left_idx > last_idx[0] + 1) or (
                        right_idx is not None and last_idx[1] is not None and right_idx > last_idx[1] + 1)
                if far_idx:
                    buffers += self.process(buffer)
                    buffer = []
            buffer.append(elt)
            last_left_available = left_idx is None and last_idx is not None
            left = last_idx[0] if last_left_available else left_idx
            last_right_available = right_idx is None and last_idx is not None
            right = last_idx[1] if last_right_available else right_idx
            last_idx = left, right
        buffers += self.process(buffer)

        return self.make_stats(buffers)

    def dump(self):
        left_res = []
        right_res = []
        for merge_line in self.merge_lines:
            merge_line: MergeLine = merge_line
            if merge_line.present_on_left():
                left_res.append(merge_line.dump_as_left())
            if merge_line.present_on_right():
                right_res.append(merge_line.dump_as_right())

        left_res = self.clean_raw_res(left_res)
        right_res = self.clean_raw_res(right_res)

        return b"\n".join(left_res), b"\n".join(right_res)
        # left = self.dump_left(left_res)
        # right = self.dump_right(left_res)

    def to_bytes(self):
        res = ""
        for line in self.merge_lines:
            res += line.to_bytes()
        return res


class CommitMerge:
    def __init__(self, left_git_diff: GitDiff, right_git_diff: GitDiff):
        self.conflicts = False
        self.left_git_diff = left_git_diff
        self.right_git_diff = right_git_diff
        self.files: Dict[bytes, MergeFileDiff] = {}
        self.load()

    def load(self):
        files = list(set(self.left_git_diff.file_diffs).union(set(self.right_git_diff.file_diffs)))
        files.sort()
        for file in files:
            left = None
            right = None
            if file in self.left_git_diff.file_diffs:
                left = self.left_git_diff.file_diffs[file]
            if file in self.right_git_diff.file_diffs:
                right = self.right_git_diff.file_diffs[file]
            self.files[file] = MergeFileDiff(left, right)
            if self.files[file].conflicts:
                self.conflicts = True

    def reset(self):
        for mergeFileDiff in self.files.values():
            mergeFileDiff.reset()

    def swap_all(self):
        for mergeFileDiff in self.files.values():
            mergeFileDiff.swap_all()

    def move_left(self):
        for mergeFileDiff in self.files.values():
            mergeFileDiff.move_left()

    def move_right(self):
        for mergeFileDiff in self.files.values():
            mergeFileDiff.move_right()

    def dump(self):
        left_res = b""
        right_res = b""
        for file in self.files.items():
            left_dump, right_dump = file[1].dump()

            if len(left_dump) > 0:
                if len(left_res) > 0 and not left_res.endswith(b"\n"):
                    left_res += b"\n"
                left_res += b"diff --git\n"
                left_res += b"--- a/" + file[0] + b"\n"
                left_res += b"+++ b/" + file[0] + b"\n"
                left_res += left_dump

            if len(right_dump) > 0:
                if len(right_res) > 0 and not right_res.endswith(b"\n"):
                    right_res += b"\n"
                right_res += b"diff --git\n"
                right_res += b"--- a/" + file[0] + b"\n"
                right_res += b"+++ b/" + file[0] + b"\n"
                right_res += right_dump
        return left_res, right_res
