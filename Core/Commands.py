import os
import subprocess

PIPE = subprocess.PIPE


class Command:
    def __init__(self, command, work_directory=os.getcwd(), split=True, decodeUtf8=True):
        if split:
            command = command.split(" ")
        process = subprocess.Popen(command, cwd=work_directory, stdout=PIPE, stderr=PIPE)
        self.stdoutput, self.stderroutput = process.communicate()
        if decodeUtf8:
            self.stdoutput, self.stderroutput = self.stdoutput.decode("utf8"), self.stderroutput.decode("utf8")
        self.returncode = process.returncode
