import os

from fhir_rdf_validator.compare_rdf import compare_rdf

fromdir = os.path.dirname(__file__)
todir = os.path.join(fromdir, '..', 'fhir_converted_r4')

for dirname, _, files in os.walk(fromdir):
    for file in files:
        if file.endswith(".ttl"):
            fname = os.path.join(dirname, file)
            frompath = os.path.relpath(fname, fromdir)
            topath = os.path.join(todir, frompath)
            if os.path.exists(topath):
                print(f"Comparing {frompath} to {topath}")
                rslt = compare_rdf(frompath, topath)
                print("Matches" if not rslt else rslt)
            else:
                print(f"No target file for {frompath}")