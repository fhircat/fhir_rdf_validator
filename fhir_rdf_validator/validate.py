import os
from argparse import ArgumentParser
from typing import Dict, Optional, List

import dirlistproc
from rdflib import Graph, Namespace, RDF
from rdflib.plugins.parsers.notation3 import BadSyntax
from pyshex.shex_evaluator import ShExEvaluator
from jsonasobj import as_json

from fhir_rdf_validator.compare_rdf import compare_rdf

FHIR = Namespace("http://hl7.org/fhir/")


def input_filter(fn: str, dir: str, opts: Namespace) -> bool:
    print(f"Testing {fn}", end='')
    input_fn = os.path.join(dir, fn)
    g = Graph()
    try:
        g.load(input_fn, format="turtle")
    except BadSyntax:
        print("   PARSE ERROR")
        return False

    node_role = list(g.subject_objects(FHIR.nodeRole))
    if not node_role:
        print(" NOT A FHIR Resource")
        return False
    focus = node_role[0][0]
    resource_type = g.value(focus, RDF.type)
    if not resource_type:
        print(" UNKNOW Resource type")
        return False
    print(f" Type: {resource_type}")
    opts.graph = g
    opts.resource_type = resource_type
    opts.focus = focus
    return True


class ShExCache:
    """ Cache for ShExJ for faster, localized parsing """
    def __init__(self, shex_dir: Optional[str], cache_dir: Optional[str]) -> None:
        self.evaluator_cache: Dict[str, ShExEvaluator] = dict()
        self.cache_dir = cache_dir
        self.shex_dir = shex_dir

    def _cache_name(self, name: str) -> Optional[str]:
        return os.path.join(self.cache_dir, name + '.shexj') if self.cache_dir else None

    def cache_add(self, name: str, evaluator: ShExEvaluator) -> ShExEvaluator:
        self.evaluator_cache[name] = evaluator
        return evaluator

    def add(self, name: str, evaluator: ShExEvaluator) -> ShExEvaluator:
        """
         Add ShExEvaluator to the cache
        :param name: Name of the shex file (sans suffix)
        :param evaluator: Evaluator that has the parsed file
        """
        if name not in self.evaluator_cache:
            self.evaluator_cache[name] = evaluator
        shex_path = self._cache_name(name)
        if shex_path and not os.path.exists(shex_path):
            with open(shex_path, 'w') as f:
                # TODO: Add the context in or create a function in the evaluator that emits the full JSON string
                f.write(as_json(evaluator._schema))
        return evaluator

    def get(self, dir: str, name: str) -> ShExEvaluator:
        """
        Retrieve name from whatever cache we've got
        :param name: Name of the shex file (sans suffix)
        :return: ShExEvaluator if shex can be found
        """
        if name in self.evaluator_cache:
            return self.evaluator_cache[name]
        shex_path = self._cache_name(name)
        if shex_path and os.path.exists(shex_path):
            return self.cache_add(name, ShExEvaluator(schema=shex_path))
        return self.add(name, ShExEvaluator(schema=os.path.join(self.shex_dir or dir, name + '.shex')))


def validate_rdf(input_fn: str, output_fn: str, opts: Namespace) -> bool:
    if opts.shex:
        shex_name = os.path.basename(opts.resource_type).lower()
        evaluator: ShExEvaluator = opts.shex_cache.get(os.path.dirname(input_fn), shex_name)
        result = evaluator.evaluate(rdf=opts.graph, focus=str(opts.focus))
        if not result[0].result:
            print (f"***** {result[0].reason}")
            return False
    if opts.outdir:
        output_ttl = output_fn + ".ttl"
        if os.path.exists(output_ttl):
            rslts = compare_rdf(output_ttl, opts.graph)
            if rslts:
                print("-" * 40)
                print(rslts)
                return False
        else:
            print(f"*****> Output file: {output_ttl} does not exist!")
            return False
    return True


def add_cache(opts: Namespace) -> None:
    """
    Tack on a localized copy of ShExCache for safety
    :param opts: parser arguments
    """
    if opts.cachedir:
        os.makedirs(opts.cachedir, exist_ok=True)
    opts.shex_cache = ShExCache(opts.shexdir, opts.cachedir)


def addargs(parser: ArgumentParser) -> None:
    parser.add_argument('--shex', help="Do ShEx validaton", action="store_true")
    parser.add_argument('-sd', '--shexdir', help="Base directory of ShEx definitions. Default: indir")
    parser.add_argument('-cd', '--cachedir', help="Cache directory for cached ShEx")


def main(argv: List[str] = None):
    """
    Process RDF files in indir, doing ShEx validation and/or comparing the RDF to the files in outdir
    :param argv: Argument list.  If None, use sys.argv
    :return: 0 if all RDF files that had valid FHIR in them were successful, 1 otherwise
    """
    dlp = dirlistproc.DirectoryListProcessor(argv, "Validate FHIR RDF", ".ttl", None, addargs=addargs,
                                             postparse=add_cache)
    if not (dlp.opts.infile or dlp.opts.indir):
        dirlistproc.DirectoryListProcessor(["--help"], "Validate FHIR RDF", ".ttl", None, addargs=addargs)
    nfiles, nsuccess = dlp.run(validate_rdf, file_filter_2=input_filter)
    print(f"Total={nfiles} Successful={nsuccess}")
    return 0 if nfiles == nsuccess else 1


if __name__ == '__main__':
    main(sys.argv[1:])
