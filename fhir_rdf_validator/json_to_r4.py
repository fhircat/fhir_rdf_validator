import os
import urllib
from argparse import Namespace, ArgumentParser
from copy import deepcopy
from typing import Any, List, Optional, Union, Set

import dirlistproc
import requests
import sys
from jsonasobj import JsonObj, loads, as_dict, as_json

# CONTEXT_SERVER = "https://raw.githubusercontent.com/fhircat/jsonld_context_files/master/contextFiles/"
CONTEXT_SERVER = "https://fhircat.org/fhir/contexts/r5/"

CODE_SYSTEM_MAP = {
    "http://snomed.info/sct": "sct",
    "http://loinc.org": "loinc"
}

VALUE_TAG = "value"


def to_r4(o: JsonObj, server: Optional[str], add_context: bool) -> JsonObj:
    """
    Convert the FHIR Resource in "o" into the R4 value notation

    :param o: FHIR resource
    :param server: Server root - if absent, use the file location
    :param add_context: True means add @context
    :return: reference to "o" with changes applied.  Warning: object is NOT copied before change
    """
    def to_value(v: Any) -> JsonObj:
        return JsonObj(**{VALUE_TAG: v})

    def parse_resource_type(rt: str) -> str:
        """ Parse rt returning just the resource type """
        return rt.rsplit(':')[1] if ':' in rt else rt

    def from_value(v: Any) -> Any:
        return v[VALUE_TAG] if isinstance(v, JsonObj) and VALUE_TAG in as_dict(v) else v

    def add_type_arc(n: JsonObj) -> None:
        if hasattr(n, 'system') and hasattr(n, 'code'):
            # Note: This is another reason we hate the value work
            system = from_value(n.system)
            code = urllib.parse.quote(from_value(n.code), safe='')
            system_root = system[:-1] if system[-1] in '/#' else system
            if system_root in CODE_SYSTEM_MAP:
                base = CODE_SYSTEM_MAP[system_root] + ':'
            else:
                base = system + ('' if system[-1] in '/#' else '/')
            # TODO: Escape code
            n['@type'] = base + code

    def dict_processor(d: JsonObj, resource_type: str, resource_type_set: Set[str], inside: Optional[bool] = False) \
            -> None:
        """
        Process the elements in dictionary d:
        1) Ignore keys that begin with "@" - this is already JSON information
        2) Add index numbers to lists
        3) Recursively process values of type object
        4) Convert any elements that are not one of "nodeRole", "index", "id" and "div" to objects
        5) Merge

        :param d: dictionary to be processed
        :param resource_type: unedited resource type
        :param resource_type_set: set of all resource types in the model
        :param inside: indicator of a recursive call
        :return: List of resourceTypes referenced by the resource
        """
        def gen_reference(do: JsonObj) -> JsonObj:
            """
            Return the object of a fhir:link based on the reference in d
            :param do: object containing the reference
            :return: link and optional type element
            """
            # TODO: find the official regular expression for the type node.  For the moment we make the (incorrect)
            #       assumption that the type is everything that preceeds the first slash
            if "://" not in do.reference and not do.reference.startswith('/'):
                if hasattr(do, 'type'):
                    typ = do.type
                else:
                    typ = do.reference.split('/', 1)[0]
                link = '../' + do.reference
            else:
                link = do.reference
                typ = getattr(do, 'type', None)
            rval = JsonObj(**{"@id": link})
            if typ:
                rval['@type'] = "fhir:" + typ
            return rval

        # Normalize all the elements in d.
        #  We realize the keys as a list up front to prevent messing with our own updates
        for k in list(as_dict(d).keys()):
            v = d[k]
            if k.startswith('@'):               # Ignore JSON-LD components
                pass
            elif isinstance(v, JsonObj):        # Inner object -- process recursively
                dict_processor(v, resource_type, resource_type_set, True)
            elif isinstance(v, list):           # Add ordering to the list
                d[k] = list_processor(k, v, resource_type_set)
            elif k == "id":                     # Internal ids are relative to the document
                d['@id'] = ('#' if inside and not v.startswith('#') else (resource_type + '/')) + v
                d[k] = to_value(v)
            elif k == "reference":              # Link to another document
                if not hasattr(d, 'link'):
                    d["fhir:link"] = gen_reference(d)
                d[k] = to_value(v)
            elif k == "resourceType" and not(v.startswith('fhir:')):
                resource_type_set.add(v)
                d[k] = 'fhir:' + v
            elif k not in ["nodeRole", "index", "div"]:    # Convert most other nodes to value entries
                d[k] = to_value(v)
            if k == 'coding':
                [add_type_arc(n) for n in v]

        # Merge any extensions (keys that start with '_') into the base
        for k in [k for k in as_dict(d).keys() if k.startswith('_')]:
            base_k = k[1:]
            if not hasattr(d, base_k) or not isinstance(d[base_k], JsonObj):
                d[base_k] = JsonObj()
            else:
                for kp, vp in as_dict(d[k]).items():
                    if kp in d[base_k]:
                        print(f"Extension element {kp} is already in the base for {k}")
                    else:
                        d[base_k][kp] = vp
            del(d[k])

    def list_processor(k: str, lo: List, rts: Set[str]) -> List[Any]:
        """
        Process the elements in the supplied list adding indices and converting the interior nodes

        :param k: List key (for error reporting)
        :param lo: List to be processed
        :param rts: Set of referenced resource types.  May be updated
        :return: Ordered list of entries
        """

        def list_element(e: Any, pos: int) -> Any:
            """
            Add a list index to list element "e"

            :param e: Element in a list
            :param pos: position of element
            :return: adjusted object
            """
            if isinstance(e, JsonObj):
                dict_processor(e, resource_type, rts, True)
                if getattr(e, 'index', None) is not None:
                    print(f'Problem: "{k}" element {pos} already has an index')
                else:
                    e.index = pos               # Add positioning
            elif isinstance(e, list):
                print(f"Problem: {k} has a list in a list", file=sys.stderr)
            else:
                e = to_value(e)
                e.index = pos
            return e

        return [list_element(le, p) for p, le in enumerate(lo)]

    resource_type = parse_resource_type(o.resourceType)
    resource_type_set = {resource_type}
    dict_processor(o, resource_type, resource_type_set)

    # Add nodeRole
    o['nodeRole'] = "fhir:treeRoot"

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
        o['@context'] = [f"{CONTEXT_SERVER}{rt.lower()}.context.jsonld" for rt in sorted(resource_type_set)]
        o['@context'].append(f"{CONTEXT_SERVER}root.context.jsonld")
        local_context = JsonObj()
        local_context["nodeRole"] = JsonObj(**{"@type": "@id", "@id": "fhir:nodeRole"})
        if server:
            local_context["@base"] = server
        local_context['owl:imports'] = JsonObj(**{"@type": "@id"})
        local_context['owl:versionIRI'] = JsonObj(**{"@type": "@id"})
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
        out_json = to_r4(opts.in_json, opts.fhirserver, opts.addcontext)
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


def main(argv: Optional[Union[str, List[str]]] = None) -> object:
    """
    Apply R4 edits to FHIR JSON files

    :param argv: Argument list.  Can be an unparsed string, a list of strings or nothing.  If nothing, we use sys.argv
    :return: 0 if all RDF files that had valid FHIR in them were successful, 1 otherwise
    """
    def gen_dlp(args: List[str]) -> dirlistproc.DirectoryListProcessor:
        return dirlistproc.DirectoryListProcessor(args, "Add FHIR R4 edits to JSON file", '.json', '.json',
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
