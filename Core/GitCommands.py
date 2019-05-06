import os

from Core.Commands import Command


class Git:
    path = os.getcwd()

    @classmethod
    def valid_repository(cls):
        if cls.path == "" or not os.path.isdir(cls.path):
            return False
        status = Command("git status", cls.path)

        return status.returncode == 0

    @classmethod
    def current_hash(cls):
        return Command("git rev-parse HEAD", cls.path).stdoutput.strip()

    @classmethod
    def parents(cls, commit):
        res = Command("git rev-list --parents -n 1 {}".format(commit), cls.path)
        return res.stdoutput.strip().split(" ")[1:]

    @classmethod
    def message(cls, commit):
        res = Command("git log -n 1 --pretty=format:%s {}".format(commit), cls.path)
        return res.stdoutput

    @classmethod
    def raw_diff(cls, commit):
        res = Command("git diff-tree -p {}".format(commit), cls.path, decodeUtf8=False)
        return res.stdoutput.split(b'\n')[1:-1]

    @classmethod
    def tag(cls, tag):
        res = Command("git tag {}".format(tag), cls.path)
        return res.stderroutput == ""

    @classmethod
    def stash(cls):
        res = Command("git stash -u", cls.path)
        return res.stderroutput == ""

    @classmethod
    def stash_pop(cls):
        res = Command("git stash pop", cls.path)
        return res.stderroutput == ""

    @classmethod
    def reset_to(cls, commit):
        res = Command("git reset --hard {}".format(commit), cls.path)
        return res.stderroutput == ""

    @classmethod
    def clean_patch(cls):
        os.remove(cls.path + "/commit")

    @classmethod
    def apply_and_stage(cls, patch):
        with open(cls.path + "/commit", 'wb') as file:
            file.write(patch)
        out = Command("git apply commit", cls.path)
        res = out.returncode == 0
        if not out.returncode == 0:
            print("git apply: {}".format(out.stderroutput))

        out = Command("git add .", cls.path)
        res = res and out.returncode == 0
        if not out.returncode == 0:
            print("git add: {}".format(out.stderroutput))
        out = Command("git reset -- commit", cls.path)
        res = res and out.returncode == 0
        if not out.returncode == 0:
            print("git reset: {}".format(out.stderroutput))
        return res

    @classmethod
    def commit(cls, message):
        command = ["git", "commit", "-m", "{}".format(message)]
        out = Command(command, cls.path, split=False)
        if not out.returncode == 0:
            print("git commit: {}".format(out.stderroutput))

        return out
