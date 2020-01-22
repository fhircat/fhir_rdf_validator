import os
import unittest
from argparse import ArgumentParser
from contextlib import redirect_stdout
from io import StringIO

from fhir_rdf_validator.shex_to_shexj import main

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


class ShExConvertTestCase(unittest.TestCase):
    def test_help(self):
        """ Test the help file """
        help_file = os.path.join(cwd, indir, "shexj_help")
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

    def test_gen_shex(self):
        """ Test the ShEx generate function """
        out_text = StringIO()
        with redirect_stdout(out_text):
            main(["-id", indir, "-od", compdir])
        self.assertEqual("""Total=2 Successful=2""", out_text.getvalue().strip())


if __name__ == '__main__':
    unittest.main()
