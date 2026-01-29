import unittest
from os import environ, path
from tempfile import TemporaryDirectory
from typing import override
import requests




from src.processing import process_pdf







class PdfTest(unittest.TestCase):

    @override
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        #fetch a pdf
        # if (response := requests.get("https://de.getsamplefiles.com/download/pdf/sample-1.pdf")).status_code != 200:
        #     raise self.failureException("couldnt fetch file")
        
        # with open(path.join(self.tmpdir.name, "testdata.pdf"), "wb") as f:
        #     f.write(response.content)


    @unittest.skipIf(not environ.get("PDF_PATH"), "no env var set")
    @unittest.skipIf(not environ.get("DEEPINFRA_API_TOKEN"), "no env var set")
    def test(self):
        to_test = process_pdf.process_pdf

        #args
        args = [
            environ.get("PDF_PATH"),
            path.join(self.tmpdir.name, "output.csv"),
            environ.get("DEEPINFRA_API_TOKEN"),
            True,
            True,
            None
        ]

        #test
        to_test(*args)
        
        self.assertTrue(path.isfile(path.join(self.tmpdir.name, "output.csv")))
        
        with open(path.join(self.tmpdir.name, "output.csv"), encoding="utf-8") as f:
            header = f.readline()

            self.assertTrue(all( x in header for x in ["Main Topic", "Sub Topic", "Detailed Topic", "data"] ))
