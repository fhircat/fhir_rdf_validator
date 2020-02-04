import os
import unittest
from argparse import ArgumentParser
from contextlib import redirect_stdout
from io import StringIO
from typing import Optional

import requests

from fhir_rdf_validator.json_to_r5 import main

cwd = os.path.dirname(__file__)
indir = os.path.join(cwd, 'data_in')
json_indir = os.path.join(cwd, 'vanilla_json')
json_r5dir = os.path.join(cwd, 'r5_json')

class HelpPrinted(Exception):
    pass


# Override the exit method
def exit(self, status=0, message=None):
    if message:
        self._print_message(message)
    raise HelpPrinted()


ArgumentParser.exit = exit

FHIR_SERVER = "http://build.fhir.org/"

class ConvertRDFTestCase(unittest.TestCase):
    def test_help(self):
        """ Test the help file """
        help_file = os.path.join(cwd, indir, "r5json_help")
        help_text = StringIO()
        with redirect_stdout(help_text):
            with self.assertRaises(HelpPrinted):
                main(["--help"])
        if os.path.exists(help_file):
            with open(help_file) as f:
                expected = f.read()
            self.assertEqual(expected.strip(), help_text.getvalue().strip())
        else:
            with open(help_file, 'w') as f:
                f.write(help_text.getvalue())
            self.fail(f"{help_file} created - rerun test")

    def from_web(self, fname: str, typ: str, target_directory: str) -> str:
        """
        Download fname from the FHIR server and save it in target_directory if necessary.
        If it already exists, just use it

        :param fname: file to download
        :param typ: Resource type for the file
        :param target_directory: where to put it
        :return: where to get it
        """
        target = os.path.join(target_directory, fname)
        if not os.path.exists(target):
            # f_url = FHIR_SERVER + typ + '/' + fname
            f_url = FHIR_SERVER + fname
            resp = requests.get(f_url)
            if resp.ok:
                with open (target, 'w') as f:
                    f.write(resp.text)
            else:
                self.fail(f"{f_url}: {resp.reason}")
        return target

    def convert_file(self, fname: str, typ: str, indir: Optional[str] = json_indir, outdir: Optional[str] = json_r5dir):
        main(["-i", self.from_web(fname, typ, indir),
              "-o", os.path.join(outdir, fname),
              "-c", "-fs", FHIR_SERVER])

    def test_single_files(self):
        self.convert_file("patient-example-d.json", "Patient")
        self.convert_file("medicationadministration0301.json", "MedicationAdministration")
        self.convert_file("patient-example.json", "Patient")
        self.convert_file("observation-example-bmd.json", "Observation")
        self.convert_file("library-zika-virus-intervention-logic.json", "Library")

    def test_batch_convert(self):
        main(["-id", json_indir, "-od", json_r5dir, "-c", "-fs", FHIR_SERVER ])

    def do_r5(self, fn: str) -> None:
        main(f"-i vanilla_json/{fn}.json -o r5_json/{fn}.json -c -fs {FHIR_SERVER}".split())

    def test_r5_document(self):
        self.do_r5('resource_subject_1')
        self.do_r5('primitive_example_1')
        self.do_r5('object_list_example_1')


if __name__ == '__main__':
    unittest.main()
