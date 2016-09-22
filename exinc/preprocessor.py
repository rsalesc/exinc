"""preprocessor class."""
import re
import os


class Preprocessor():
    def __init__(self, paths):
        self.paths = paths
        self.pattern = re.compile(r"^\s*#include\s*\"(.+)\"\s*")
        self.ok = True
        self.errors = []
        self.result = ""
        self.seen = {}
        self.recursion = {}

    def expand(self, text, parent="root_file"):
        for (n, line) in enumerate(text.splitlines()):
            result = self.pattern.match(line)
            if result is not None:
                next_file = result.group(1)
                found = False
                for path in self.paths:
                    next_path = os.path.join(path, next_file)
                    if os.path.isfile(next_path):
                        found = True
                        abs_next = os.path.abspath(next_path)
                        if abs_next in self.recursion:
                            self.ok = False
                            self.errors.append((
                                "Found back-edge to file %s "
                                "(on line %d of file %s)\n"
                            ) % (next_file, n+1, parent))
                        elif abs_next not in self.seen:
                            try:
                                next_text = open(abs_next, "r").read()
                                self.seen[abs_next] = 1
                                self.recursion[abs_next] = 1
                                self.paths.append(os.path.dirname(abs_next))
                                self.expand(next_text, next_file)
                                self.recursion.pop(abs_next)
                            except IOError:
                                self.ok = False
                                self.errors.append((
                                    "File %s could not be read [IO issue] "
                                    "(on line %d of file %s)\n"
                                ) % (next_file, n+1, parent))
                        break

                if not found:
                    self.ok = False
                    self.errors.append((
                            "File %s could not be found "
                            "(on line %d of file %s)\n"
                        ) % (next_file, n+1, parent))
            else:
                self.result += "%s\n" % line

    def has_errors(self):
        return not self.ok

    def get_errors(self):
        return '\n'.join(self.errors)

    def get_result(self):
        return self.result
