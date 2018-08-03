from backports import tempfile
import os
import subprocess
import shlex

FLAGS = "-I{cwd} -isystem{include} -fcolor-diagnostics -fparse-all-comments -- -l {lines} -d {dir} -o {output}"
INPUT_NAME = "input.cpp"
OUTPUT_NAME = "output.cpp"


class OptimizerError(Exception):
    pass


class CodeOptimizer:
    def __init__(self,
                 cmd_path,
                 clang_includes,
                 clang_options="",
                 verbose=False,
                 lines=1,
                 cwd=None,
                 paths=[]):
        if isinstance(clang_options, list):
            clang_options = " ".join(clang_options)
        self._cmd_path = cmd_path
        self._includes = clang_includes
        self._verbose = verbose
        self._lines = 1
        self._cwd = cwd or "."
        self._clang_options = clang_options
        self._paths = list(paths)

    def run(self, code):
        with tempfile.TemporaryDirectory() as d:
            input_path = os.path.join(d, INPUT_NAME)
            output_path = os.path.join(d, OUTPUT_NAME)
            with open(input_path, "w") as f:
                f.write(code)
            extra_includes = " ".join(
                map(lambda x: "-I{}".format(x), self._paths))
            args = shlex.split("{} {} {} {} {}".format(
                self._cmd_path, self._clang_options, extra_includes,
                FLAGS.format(
                    cwd=self._cwd,
                    include=self._includes,
                    dir=d,
                    output=output_path,
                    lines=self._lines), input_path))
            with open(os.devnull, "w") as FNULL:
                p = subprocess.Popen(
                    args, stdout=FNULL, stderr=subprocess.PIPE)
                (_, perror) = p.communicate()
                if p.returncode != 0:
                    raise OptimizerError(perror)
            return open(output_path, "r").read()


class CaidePreprocessor:
    def __init__(self, *args, **kwargs):
        self._optimizer = CodeOptimizer(*args, **kwargs)
        self.result = None

    def expand(self, text, parent="root_file"):
        self.result = None
        self.error = None
        try:
            self.result = self._optimizer.run(text)
        except OptimizerError as e:
            self.error = str(e)

    def has_errors(self):
        return self.error is not None

    def get_errors(self):
        return "Errors in Caide optimizer.\n" + self.error

    def get_result(self):
        return self.result
