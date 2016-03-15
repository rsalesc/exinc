import argparse
import sys
import os
import shlex
import subprocess
import tempfile
from collections import namedtuple
from preprocessor import Preprocessor

# CONSTANTS
DEFAULT_COMPILER = 'g++ -xc++'
DEFAULT_FLAGS = ['-std=c++11']
DEFAULT_PATHS = [
    "/home/rsalesc/ownCloud/Programming Training/Library/PlugAndPlay"
]

# PARSER CONFIG
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input",
                    metavar="in-file",
                    help="provide input cpp file")
parser.add_argument("-o", "--output",
                    metavar="out-file",
                    help="provide output cpp file")
parser.add_argument("-p", "--path",
                    nargs="*",
                    help="provide include paths to expand (abs)")
parser.add_argument("-c", "--compile",
                    action="store_true",
                    help="generate a compiled cpp executable")
args = parser.parse_args()

# NAMED TUPLES AND CLASSES
ExincResult = namedtuple('ExincResult', 'has_errors result')


class Exinc():
    def __init__(self, **kwargs):
        opts = kwargs
        self.in_text = opts["input"]
        self.in_file = opts["filename"] if "filename" in opts else "root_file"
        if "paths" not in opts:
            opts["paths"] = []
        self.paths = [x for x in opts["paths"] if os.path.isdir(x)]
        self.paths += DEFAULT_PATHS

    def run(self):
        prep = Preprocessor(self.paths)
        prep.expand(self.in_text, os.path.basename(self.in_file))
        return ExincResult(prep.has_errors(),
                           prep.get_errors() if prep.has_errors()
                           else prep.get_result())

    def compile(self, flags=DEFAULT_FLAGS, output_path=None, cwd=os.curdir):
        if isinstance(flags, basestring):
            flags = shlex.split(flags)

        if output_path is False:
            output_path = os.path.join(tempfile.gettempdir(), "exinc_out")

        # PRE-COMPILATION STEP
        params = shlex.split(DEFAULT_COMPILER) + ["-"] + flags
        params += [] if output_path is None else ["-o", output_path]
        pre_params = params
        for path in self.paths:
            pre_params += ['-I', path]

        p = subprocess.Popen(pre_params, cwd=cwd, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (_, perror) = p.communicate(self.in_text)

        if p.returncode != 0:
            return ExincResult(True,
                               "Errors in pre-compilation step.\n" + perror)

        prep = self.run()
        if prep.has_errors:
            return prep

        # COMPILATION STEP
        p = subprocess.Popen(params, cwd=cwd, stdin=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        (_, perror) = p.communicate(prep.result)

        if p.returncode != 0:
            return ExincResult(True,
                               "Error in expanded compilation step\n" + perror)

        return prep

# MAIN APPLICATION


def entry_point():
    paths = [] if not args.path else args.path
    in_text = ""
    in_file = ""
    if args.input:
        in_file = args.input
        if os.path.isfile(in_file):
            try:
                in_text = open(in_file, "r").read()
                paths.append(os.path.abspath(os.path.dirname(in_file)))
            except IOError:
                sys.stderr.write("Input file could not be read [IO issue]\n")
                sys.exit(1)
        else:
            sys.stderr.write("Input file could not be found\n")
            sys.exit(1)
    else:
        try:
            in_text = sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(0)

    exinc = Exinc(paths=paths, input=in_text,
                  filename=in_file if args.input else "root_file")

    if(args.compile):
        res = exinc.compile()
    else:
        res = exinc.run()

    if res.has_errors:
        for line in res.result:
            sys.stderr.write("%s\n" % line)
            sys.exit(1)
    else:
        if not args.output:
            sys.stdout.write(res.result)
        else:
            out_file = os.path.abspath(args.output)
            if not os.path.isdir(os.path.dirname(out_file)):
                sys.stderr.write("Output file was not found\n")
                sys.exit(1)
            else:
                try:
                    open(out_file, "w").write(res.result)
                except IOError:
                    sys.stderr.write("Output file could not be written\n")
                    sys.exit(1)

    sys.exit(0)
