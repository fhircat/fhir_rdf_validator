import os
import unittest
from argparse import ArgumentParser
from contextlib import redirect_stdout
from io import StringIO

from fhir_rdf_validator.validate import main

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


class RDFCompareTestCase(unittest.TestCase):
    def test_help(self):
        """ Test the help file """
        help_file = os.path.join(cwd, indir, "help")
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

    def test_rdf_compare(self):
        """ Test the RDF comparison function """
        out_text = StringIO()
        with redirect_stdout(out_text):
            main(["-id", indir, "-od", compdir])
        self.assertEqual("""Testing visionprescription-example-1.ttl Type: http://hl7.org/fhir/VisionPrescription
Testing visionprescription-example.ttl Type: http://hl7.org/fhir/VisionPrescription
----------------------------------------
----- Missing Triples -----

<http://hl7.org/fhir/VisionPrescription/33123> ns1:extraNode 1 .


----- Added Triples -----

Testing verificationresult-example.ttl Type: http://hl7.org/fhir/VerificationResult
Total=3 Successful=2""", out_text.getvalue().strip())

    def test_shex(self):
        """ Test some sample RDF files against their ShEx definitions """
        out_text = StringIO()
        with redirect_stdout(out_text):
            main(["-id", indir, "--shex", "-sd", indir])
        self.assertEqual("""Testing visionprescription-example-1.ttl Type: http://hl7.org/fhir/VisionPrescription
Testing visionprescription-example.ttl Type: http://hl7.org/fhir/VisionPrescription
Testing verificationresult-example.ttl Type: http://hl7.org/fhir/VerificationResult
Total=3 Successful=3
""", out_text.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
