import argparse
import sys
import os
from preprocessor import Preprocessor

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

args = parser.parse_args()

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
            except Exception:
                sys.stderr.write("Input file could not be read [IO issue]\n")
                sys.exit(1)
        else:
            sys.stderr.write("Input file could not be found\n")
            sys.exit(1)
    else:
        in_text = sys.stdin.read()

    prep = Preprocessor(paths)
    prep.expand(in_text,
     os.path.basename(in_file) if args.input else "root_file")

    if prep.has_errors():
        for line in prep.get_errors():
            sys.stderr.write("%s\n" % line)
            sys.exit(1)
    else:
        if not args.output:
            sys.stdout.write(prep.get_result())
        else:
            out_file = os.path.abspath(args.output)
            if not os.path.isdir(os.path.dirname(out_file)):
                sys.stderr.write("Output file was not found\n")
                sys.exit(1)
            else:
                try:
                    open(out_file, "w").write(prep.get_result())
                except Exception:
                    sys.stderr.write("Output file could not be written [IO issue]\n")
                    sys.exit(1)

    sys.exit(0)
