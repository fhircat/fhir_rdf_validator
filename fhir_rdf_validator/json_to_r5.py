import os
import sys
from argparse import Namespace, ArgumentParser
from copy import deepcopy
from typing import Any, List, Optional, Set

import dirlistproc
import requests
from jsonasobj import JsonObj, loads, as_dict, as_json

# CONTEXT_SERVER = "https://raw.githubusercontent.com/fhircat/jsonld_context_files/master/contextFiles/"
CONTEXT_SERVER = "https://fhircat.org/fhir/contexts/r5/"

CODE_SYSTEM_MAP = {
    "http://snomed.info/sct": "sct",
    "http://loinc.org": "loinc"
}


class BNodeGenerator:
    """
    BNode generator -- generate BNode identifiers in the form "_bn{list number}_{inst_number}
    """
    _instance_num = 0

    def __init__(self):
        self._nxt_id = 0
        BNodeGenerator._instance_num += 1
        print(f"Constructing a BNODE generator instance {BNodeGenerator._instance_num}: {id(self)}")

    def next_node(self) -> str:
        print(f"Pre-inc: {self._instance_num}:{self._nxt_id}: {id(self)}")
        self._nxt_id += 1
        return f'_:bn{BNodeGenerator._instance_num}_{self._nxt_id}'

    @classmethod
    def reset(cls) -> None:
        print("resetting the BNODE generator")
        cls._instance_num = 0


def to_r5(o: JsonObj, server: Optional[str], add_context: bool) -> JsonObj:
    """
    Convert the FHIR Resource in "o" into the r5 value notation

    :param o: FHIR resource
    :param server: Server root - if absent, use the file location
    :param add_context: True means add @context
    :return: reference to "o" with changes applied.  Warning: object is NOT copied before change
    """
    underscore_nodes: Set[str] = set()
    BNodeGenerator.reset()

    def to_value(v: Any) -> JsonObj:
        """ THis is an identify function in R5 """
        return v

    def from_value(v: Any) -> Any:
        return v

    def add_type_arc(n: JsonObj) -> None:
        if hasattr(n, 'system') and hasattr(n, 'code'):
            # Note: This is another reason we hate the value work
            system = from_value(n.system)
            code = from_value(n.code)
            system_root = system[:-1] if system[-1] in '/#' else system
            if system_root in CODE_SYSTEM_MAP:
                base = CODE_SYSTEM_MAP[system_root] + ':'
            else:
                base = system + ('' if system[-1] in '/#' else '/')
            # TODO: Escape code
            n['@type'] = base + code

    def dict_processor(dobj: JsonObj, raw_resource_type: str, inside: Optional[bool] = False) -> None:
        """
        Process the elements in dictionary d:
        1) Ignore keys that begin with "@" - this is already JSON information
        2) Duplicate lists creating one ordered, one not
        3) Recursively process values of type 'object'
        5) Add a mapping to merge '_' elements

        :param dobj: dictionary to be processed
        :param raw_resource_type: unedited resource type
        :param inside: indicator of a recursive call
        """
        def gen_reference(rd: JsonObj) -> List[JsonObj]:
            """
            Return the object of a fhir:link based on the reference in d
            :param rd: object containing the reference
            :return: link and optional type element
            """
            # TODO: find the official regular expression for the type node.  For the moment we make the (incorrect)
            #       assumption that the type is everything that preceeds the first slash
            if "://" not in rd.reference and not rd.reference.startswith('/'):
                if hasattr(rd, 'type'):
                    typ = rd.type
                else:
                    typ = rd.reference.split('/', 1)[0]
                link = '../' + rd.reference
            else:
                link = rd.reference
                typ = getattr(rd, 'type', None)
            #   "subject": [{"@id": "../Patient/foo1",
            #             "@type": "fhir:Patient" },
            #             {"reference": "Patient/f001",
            #             "display": "P. van de Heuvel"}]
            ref = JsonObj(**{"@id": link})
            if typ:
                ref['@type'] = "fhir:" + typ
            return [ref, rd]

        # Normalize all the elements in d.
        #  We realize the keys as a list up front to prevent messing with our own updates
        for k in list(as_dict(dobj).keys()):
            v = dobj[k]
            if k.startswith('@'):               # Ignore JSON-LD components
                pass
            elif isinstance(v, JsonObj):        # Inner object -- process recursively
                dict_processor(v, raw_resource_type, True)
                if hasattr(v, 'reference'):
                    dobj[k] = gen_reference(v)
            elif isinstance(v, list):           # Add ordering to the list
                dobj[k] = list_processor(k, v)
            elif k == "id":                     # Internal ids are relative to the document
                dobj['@id'] = ('#' if inside and not v.startswith('#') else (raw_resource_type + '/')) + v
                dobj[k] = to_value(v)
            elif k == "resourceType" and not(v.startswith('fhir:')):
                dobj[k] = 'fhir:' + v
            elif k not in ["nodeRole", "index", "div"]:    # Convert most other nodes to value entries
                dobj[k] = to_value(v)
            if k == 'coding':
                [add_type_arc(n) for n in v]

        underscore_nodes.update([k for k in as_dict(dobj).keys() if k.startswith('_')])

    def list_processor(k: str, lst: List) -> Any:
        """
        Process a list, adding interior identifiers if its members are objects and then replicating it so that we
        end up with a SET and a LIST

        :param k: List key (for error reporting)
        :param lst: List to be processed
        """
        bnode_generator = BNodeGenerator()

        def list_element(e: Any) -> Any:
            """
            Add a list index to list element "e"

            :param e: Element in a list
            :return: adjusted object
            """
            if isinstance(e, JsonObj):
                dict_processor(e, resource_type, True)
                if not hasattr(e, '@id'):
                    e['@id'] = ('#' + e.id) if hasattr(e, 'id') else bnode_generator.next_node()
            elif isinstance(e, list):
                print(f"Problem: {k} has a list in a list", file=sys.stderr)
            else:
                e = to_value(e)
            return e

        adjusted_list = [list_element(le) for le in lst]
        return [adjusted_list,
                {"fhir:ordered":
                     [JsonObj(**{"@id": e['@id']}) if isinstance(e, JsonObj) else e for e in adjusted_list]}]

    resource_type = o.resourceType.rsplit(':')[1] if ':' in o.resourceType else o.resourceType
    dict_processor(o, resource_type)

    # Add nodeRole
    o['fhir:nodeRole'] = "fhir:treeRoot"

    # Add the "ontology header"
    hdr = JsonObj()
    hdr["@id"] = o['@id'] + ".ttl"
    hdr["owl:versionIRI"] = hdr["@id"]
    hdr["owl:imports"] = "fhir:fhir.ttl"
    # TODO: replace this with included once we get the bug fixed.
    o = JsonObj(**{"@graph": [deepcopy(o), hdr]})
    # o["@included"] = hdr

    # Fill out the rest of the context
    if add_context:
        o['@context'] = [f"{CONTEXT_SERVER}{resource_type.lower()}.context.jsonld"]
        o['@context'].append(f"{CONTEXT_SERVER}root.context.jsonld")
        local_context = JsonObj()
        local_context["nodeRole"] = JsonObj(**{"@type": "@id", "@id": "fhir:nodeRole"})
        if server:
            local_context["@base"] = server
        local_context['owl:imports'] = JsonObj(**{"@type": "@id"})
        local_context['owl:versionIRI'] = JsonObj(**{"@type": "@id"})
        local_context["fhir:ordered"] = JsonObj(**{"@type": "@id", "@container": "@list"})
        local_context["fhir:orderedp"] = JsonObj(**{"@container": "@list"})
        for u in sorted(underscore_nodes):
            local_context[u] = u[1:]
        o['@context'].append(local_context)
    return o


def convert_file(ifn: str, ofn: str, opts: Namespace) -> bool:
    """
    Convert ifn to ofn

    :param ifn: Name of file to convert
    :param ofn: Target file to convert to
    :param opts: Parameters
    :return: True if conversion is successful
    """
    if ifn not in opts.converted_files:
        out_json = to_r5(opts.in_json, opts.fhirserver, opts.addcontext)
        with open(ofn, "w") as outf:
            outf.write(as_json(out_json))
        opts.converted_files.append(ifn)
    return True


def check_json(ifn: str, ifdir: str, opts: Namespace) -> bool:
    """
    Check whether ifn is a valid FHIR file
    :param ifn: file name
    :param ifdir: file directory
    :param opts: options - we add in_json to it if the file passes
    :return: True if a valid FHIR resource
    """
    if '://' in ifn:
        infilename = ifn
        resp = requests.get(ifn)
        if not resp.ok:
            print(f"Error {resp.status_code}: {ifn} {resp.reason}")
            return False
        in_json = loads(resp.text)
    else:
        infilename = os.path.join(ifdir, ifn)
        with open(infilename) as infile:
            in_json = loads(infile.read())
    if not (hasattr(in_json, 'resourceType') or hasattr(in_json, 'id')):
        print(f"{infilename} is not a FHIR resource - processing skipped", file=sys.stderr)
        return False
    opts.in_json = in_json
    return True


def addargs(parser: ArgumentParser) -> None:
    parser.add_argument("-c", "--addcontext", help="Add JSON-LD context reference", action="store_true")
    parser.add_argument("-fs", "--fhirserver", help="FHIR server base")


def main(argv: List[str] = None) -> object:
    """
    Apply R5 edits to FHIR JSON files

    :param argv: Argument list.  If None, use sys.argv
    :return: 0 if all RDF files that had valid FHIR in them were successful, 1 otherwise
    """
    def gen_dlp(args: List[str]) -> dirlistproc.DirectoryListProcessor:
        return dirlistproc.DirectoryListProcessor(args, "Add FHIR r5 edits to JSON file", '.json', '.json',
                                                  addargs=addargs)

    dlp = gen_dlp(argv)
    if not (dlp.opts.infile or dlp.opts.indir):
        gen_dlp(argv if argv is not None else sys.argv[1:] + ["--help"])  # Does not exit

    dlp.opts.converted_files = []           # If converting inline
    nfiles, nsuccess = dlp.run(convert_file, file_filter_2=check_json)
    print(f"Total={nfiles} Successful={nsuccess}")
    return 0 if nfiles == nsuccess else 1


if __name__ == '__main__':
    main()
