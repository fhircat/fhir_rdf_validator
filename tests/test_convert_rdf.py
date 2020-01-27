import os
import unittest
from argparse import ArgumentParser
from contextlib import redirect_stdout
from io import StringIO

from fhir_rdf_validator.convert_rdf import main

cwd = os.path.dirname(__file__)
indir = os.path.join(cwd, 'data_in')
compdir = os.path.join(cwd, 'data_compare')


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
        help_file = os.path.join(cwd, indir, "rdfc_help")
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

    def test_convert(self):
        """ Test the jsonld conversion function """
        out_text = StringIO()
        with redirect_stdout(out_text):
            main(["-id", indir, "-od", compdir, "-if", "ttl", "-of", "json-ld"])
        self.assertEqual("""Total=3 Successful=3""", out_text.getvalue().strip())

    def test_tutorial(self):
        # main(["-i", "../tutorial/demo1.ttl", "-o", "../tutorial/demo1.json"])
        # main(["-i", "../tutorial/demo3.json", "-o", "../tutorial/demo3.ttl"])
        # main(["-i", "../tutorial/demo3.json", "-o", "../tutorial/demo3.ttl"])
        # main(["-i", "../tutorial/account-example.ttl", "-o", "../tutorial/account-example.json"])
        # main(["-i", "../tutorial/mini.ttl", "-o", "../tutorial/mini.json"])
        # main(["-i", "../tutorial/mini.ttl", "-o", "../tutorial/mini.xml"])
        # main(["-i", "../tutorial/mini.ttl", "-o", "../tutorial/mini.ntriples"])
        # main(["-i", "../tutorial/mini.ttl", "-o", "../tutorial/mini.trig"])
        # main(["-i", "../tutorial/tweaked_patient_output.ttl", "-o", "../tutorial/tweaked_patient_output_pretty.ttl"])
        main(["-i", "../tutorial/patient_example_dicom.ttl", "-o", "../tutorial/patient_example_dicom_out.ttl"])


if __name__ == '__main__':
    unittest.main()
