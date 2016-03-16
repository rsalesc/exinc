"""exinc main file."""
import argparse
import sys
import os
import shlex
import subprocess
import tempfile
import imp
import default_config
from collections import namedtuple
from preprocessor import Preprocessor
from pkg_resources import resource_string

# APPLICATION CONFIG
CFG_PATH = os.path.join(os.path.expanduser("~"), ".exinc")
if not os.path.isfile(CFG_PATH):
    sys.stderr.write("""Your configuration file was not found.
                        A new one will be created at %s
                        """ % CFG_PATH)
    try:
        open(CFG_PATH, "w") \
            .write(resource_string(__name__, "default_config.py"))
    except IOError:
        sys.stderr.write("Your new configuration file could not be created.\n")
        sys.exit(1)

try:
    _m = imp.load_source("cfg", CFG_PATH)
except RuntimeError, ImportError:
    sys.stderr.write("Your config file could not be loaded (~/.exinc)\n")
    raise
    sys.exit(1)

import cfg
if cfg.RELEASE != default_config.RELEASE:
    sys.stderr.write("""Your configuration file is out-to-date.
                Rename it and re-run exinc. An updated config will be created.
                Then you can merge your old configs with the new one.
                """)
    sys.exit(1)


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
                    default=[],
                    help="provide include paths to expand (abs)")
parser.add_argument("-c", "--compile",
                    nargs='?',
                    const="a.out",
                    default=False,
                    help="generate a compiled cpp executable (a.out)")
parser.add_argument("--flags",
                    metavar='compiler-flags',
                    default="",
                    help="compiler flags to be appended to config flags")
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
        self.paths += cfg.DEFAULT_PATHS

    def run(self):
        prep = Preprocessor(self.paths)
        prep.expand(self.in_text, os.path.basename(self.in_file))
        return ExincResult(prep.has_errors(),
                           prep.get_errors() if prep.has_errors()
                           else prep.get_result())

    def compile(self, flags=cfg.DEFAULT_FLAGS,
                output_path=None, cwd=os.curdir):

        if isinstance(flags, basestring):
            flags = shlex.split(flags)

        if output_path is False:
            output_path = os.path.join(tempfile.gettempdir(), "exinc_out")

        # PRE-COMPILATION STEP
        params = cfg.DEFAULT_COMPILER + ["-"] + flags
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
        res = exinc.compile(cfg.DEFAULT_FLAGS + shlex.split(args.flags),
                            args.compile)
    else:
        res = exinc.run()

    if res.has_errors:
        sys.stderr.write(res.result)
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
