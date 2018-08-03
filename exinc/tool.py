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
from optimizer import CaidePreprocessor
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
parser.add_argument(
    "-i", "--input", metavar="in-file", help="provide input cpp file")
parser.add_argument(
    "-o",
    "--output",
    nargs="?",
    const=True,
    default=False,
    help="""provide output cpp file
                    if set to empty, ${input}.pre.cpp
                    will be generated
                    """)
parser.add_argument(
    "-p",
    "--path",
    nargs="*",
    default=[],
    help="provide include paths to expand (abs)")
parser.add_argument(
    "-c",
    "--compile",
    nargs='?',
    const="a.out",
    default=False,
    help="generate a compiled cpp executable (a.out)")
parser.add_argument(
    "--caide",
    default=False,
    action="store_true",
    help="use caide for preprocessing instead of default inliner")
parser.add_argument(
    "--flags",
    metavar='compiler-flags',
    default="",
    help="compiler flags to be appended to config flags")
args = parser.parse_args()

# NAMED TUPLES AND CLASSES
ExincResult = namedtuple('ExincResult', 'has_errors result')


class Exinc():
    def __init__(self,
                 input,
                 filename="root_file",
                 paths=[],
                 preprocessor="inliner"):
        assert preprocessor is not None
        self.in_text = input
        self.in_file = filename
        self.paths = [x for x in paths if os.path.isdir(x)]
        self.paths += cfg.DEFAULT_PATHS
        self.preprocessor = preprocessor

    def should_precompile(self):
        return self.preprocessor == "inliner"

    def has_filename(self):
        return self.in_file != "root_file"

    def get_preprocessor(self):
        if self.preprocessor == "inliner":
            return Preprocessor(self.paths)
        elif self.preprocessor == "caide":
            if not os.path.isfile(cfg.CMD_PATH):
                raise AssertionError("Caide cmd executable is not accessible")
            if not os.path.isdir(cfg.CLANG_INCLUDES):
                raise AssertionError("clang include dir is not accessible")
            return CaidePreprocessor(
                cfg.CMD_PATH,
                cfg.CLANG_INCLUDES,
                paths=self.paths,
                clang_options=cfg.DEFAULT_FLAGS,
                cwd=os.path.dirname(self.in_file)
                if self.has_filename() else None)
        else:
            raise NotImplementedError("no support for {} preprocessor".format(
                self.preprocessor))

    def run(self):
        prep = self.get_preprocessor()
        prep.expand(self.in_text, os.path.basename(self.in_file))
        return ExincResult(
            prep.has_errors(),
            prep.get_errors() if prep.has_errors() else prep.get_result())

    def compile(self, flags=cfg.DEFAULT_FLAGS, output_path=None,
                cwd=os.curdir):

        if isinstance(flags, basestring):
            flags = shlex.split(flags)

        if output_path is False:
            output_path = os.path.join(tempfile.gettempdir(), "exinc_out")

        params = cfg.DEFAULT_COMPILER + ["-"] + flags
        if self.should_precompile():
            # PRE-COMPILATION STEP
            pre_params = params
            for path in self.paths:
                pre_params += ['-I', path]

            p = subprocess.Popen(
                pre_params,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE)
            (_, perror) = p.communicate(self.in_text)

            if p.returncode != 0:
                return ExincResult(
                    True, "Errors in pre-compilation step.\n" + perror)

        prep = self.run()
        if prep.has_errors:
            return prep

        # COMPILATION STEP
        params += [] if output_path is None else ["-o", output_path]
        p = subprocess.Popen(
            params, cwd=cwd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
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

    if args.output is True and not args.input:
        sys.stderr.write("""An input file must be provided if
                        an empty output file is given.
                        """)
        sys.exit(1)

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

    exinc = Exinc(
        paths=paths,
        input=in_text,
        filename=in_file if args.input else "root_file",
        preprocessor="caide" if args.caide else "inliner")

    if (args.compile):
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
            if args.output is True:
                in_basename = os.path.basename(in_file)
                out_basename = in_basename.split(".")[:-1] + \
                    ['pre'] + in_basename.split(".")[-1:]
                out_basename = '.'.join(out_basename)
                out_file = os.path.join(os.path.dirname(in_file), out_basename)
            else:
                out_file = args.output
            out_file = os.path.abspath(out_file)

            if not os.path.isdir(os.path.dirname(out_file)):
                sys.stderr.write("Output directory was not found\n")
                sys.exit(1)
            else:
                try:
                    open(out_file, "w").write(res.result)
                except IOError:
                    sys.stderr.write("Output file could not be written\n")
                    sys.exit(1)

    sys.exit(0)
