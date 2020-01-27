import sys

from argparse import ArgumentParser, Namespace
from typing import List, Optional, Tuple

import dirlistproc
from rdflib import Graph
from rdflib.plugin import plugins as rdf_plugins, Parser as rdf_Parser, Serializer as rdf_Serializer


def convert_rdf(input_fn: str, output_fn: str, opts: Namespace) -> bool:
    g = Graph()
    g.load(input_fn, format=opts.informat)
    auto_compact = opts.outformat == 'json-ld'
    g.serialize(output_fn, format=opts.outformat, auto_compact=auto_compact)
    return True


def addargs(parser: ArgumentParser) -> None:
    parser.add_argument('-if', '--informat', help="Input RDF format and file suffix",
                        choices = sorted([x.name for x in rdf_plugins(None, rdf_Parser) if '/' not in str(x.name)]))
    parser.add_argument('-of', '--outformat', help="Output RDF format and file suffix",
                        choices = sorted([x.name for x in rdf_plugins(None, rdf_Serializer) if '/' not in str(x.name)]))


def file_filter(_: str) -> bool:
    """ Fix a bug in DirListProcessor where id doesn't allow a file name that starts with '.' """
    return True


def main(argv: List[str] = None):
    """
    Convert RDF files into JSON-LD format

    :param argv: Argument list.  If None, use sys.argv
    :return: 0 if all RDF files that had valid FHIR in them were successful, 1 otherwise
    """
    def dlp(args: List[str]) -> dirlistproc.DirectoryListProcessor:
        return dirlistproc.DirectoryListProcessor(args, "RDF Format Converter", '.ttl', 'jsonld', addargs=addargs)

    def set_suffix(fname: Optional[List[str]], fmt: Optional[str]) -> Optional[Tuple[str, str]]:
        """
        If a format isn't explicated, see whether it can be determined from the list of file names.  Also deal with the
        ".json" / ".json-ld" issue.
        :param fname: possible list of file names
        :param fmt: user specified format
        :return: File suffix / conversion format.  None if undeterminable
        """
        if fname and not fmt:
            if '.' in fname[0]:
                fmt = fname[0].rsplit('.', 1)[1]
        return \
            (".json", "json-ld") if fmt == 'json' else\
            (".xml", "pretty-xml") if fmt == "xml" else\
            (('' if fmt.startswith('.') else '.') + fmt, (fmt[1:] if fmt.startswith('.') else fmt)) if fmt else\
            (None, None)

    dlp = dlp(argv)
    if not (dlp.opts.infile or dlp.opts.indir):
        dirlistproc.DirectoryListProcessor(argv + ["--help"])
    dlp.infile_suffix, dlp.opts.informat = set_suffix(dlp.opts.infile, dlp.opts.informat)
    dlp.outfile_suffix, dlp.opts.outformat = set_suffix(dlp.opts.outfile, dlp.opts.outformat)
    if not dlp.opts.informat:
        print("Unable to determine input format", file=sys.stderr)
    if not dlp.opts.outformat:
        print("Unable to determine output format", file=sys.stderr)

    nfiles, nsuccess = dlp.run(convert_rdf, file_filter=file_filter) if dlp.opts.informat and dlp.opts.outformat else (0, 0)
    print(f"Total={nfiles} Successful={nsuccess}")
    return 0 if nfiles == nsuccess else 1


if __name__ == '__main__':
    main(sys.argv[1:])
