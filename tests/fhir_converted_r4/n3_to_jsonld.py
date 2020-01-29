import os

from fhir_rdf_validator.convert_rdf import main

cwd = os.path.dirname(__file__)
main(["-id", cwd, "-od", cwd, "-if", "n3", "-of", "json-ld"])
