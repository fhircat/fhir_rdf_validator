import os
import unittest
from argparse import ArgumentParser
from contextlib import redirect_stdout
from io import StringIO

from fhir_rdf_validator.json_to_r4 import main

cwd = os.path.dirname(__file__)
indir = os.path.join(cwd, 'data_in')
json_indir = os.path.join(cwd, 'vanilla_json')
json_r4dir = os.path.join(cwd, 'r4_json')

class HelpPrinted(Exception):
    pass


# Override the exit method
def exit(self, status=0, message=None):
    if message:
        self._print_message(message)
    raise HelpPrinted()


ArgumentParser.exit = exit


class ConvertRDFTestCase(unittest.TestCase):
    def test_help(self):
        """ Test the help file """
        help_file = os.path.join(cwd, indir, "r4json_help")
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

    def test_single_file(self):
        main(["-i", "http://build.fhir.org/patient-example-d.json",
              "-o", os.path.join(json_r4dir, "patient-example-d.json"),
              "-c", "-fs", "http://build.fhir.org/"])

    def test_examples(self):
        main(["-id", json_indir, '-od', json_r4dir, "-c", "-fs", "http://build.fhir.org/"])

    def test_coding(self):
        main(["-i", "http://build.fhir.org/medicationadministration0301.json",
              "-o", os.path.join(json_r4dir, "medicationadministration0301.json"),
              "-c", "-fs", "http://build.fhir.org/"])

if __name__ == '__main__':
    unittest.main()
