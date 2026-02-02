import unittest
from os import environ, path, remove
from typing import override
import requests




from src.processing import process_pdf







class PdfTest(unittest.TestCase):

    @override
    def setUp(self):
        self.testfile = "testdata.pdf"
        self.addCleanup(remove, self.testfile)

        # fetch a pdf
        if (response := requests.get("https://de.getsamplefiles.com/download/pdf/sample-1.pdf", timeout=60)).status_code != 200:
            raise self.failureException("couldnt fetch file")
        
        with open(self.testfile, "wb") as f:
            f.write(response.content)


    @unittest.skipIf(not environ.get("DEEPINFRA_API_TOKEN"), "no env var set")
    def test(self):
        to_test = process_pdf.process_pdf

        #args
        args = [
            self.testfile,
            path.join("output.csv"),
            environ.get("DEEPINFRA_API_TOKEN"),
            True,
            True,
            None
        ]

        #test
        to_test(*args)
        
        self.assertTrue(path.isfile(path.join("output.csv")))
        
        with open(path.join("output.csv"), encoding="utf-8") as f:
            header = f.readline()

            self.assertTrue(all( x in header for x in ["main_topic", "sub_topic", "detailed_topic", "data"] ))
            self.assertGreaterEqual(len(f.readlines()), 4)
