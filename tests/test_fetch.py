import unittest
from os import environ, path
from tempfile import TemporaryDirectory
from typing import override




from src.processing import fetch_dataset
from datetime import datetime, timedelta




class FetchTest(unittest.TestCase):

    @override
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)



    @unittest.skipIf(not environ.get("JIRA_BASEURL"), "no env var set")
    @unittest.skipIf(not environ.get("JIRA_AUTH_EMAIL"), "no env var set")
    @unittest.skipIf(not environ.get("JIRA_AUTH_TOKEN"), "no env var set")
    @unittest.skipIf(not environ.get("JIRA_PROJECT"), "no env var set")
    def test1(self):
        to_test = fetch_dataset.fetch_dataset


        #args
        args = [
            path.join(self.tmpdir.name, "output.csv"),
            environ.get("JIRA_BASEURL"),
            environ.get("JIRA_AUTH_EMAIL"),
            environ.get("JIRA_AUTH_TOKEN"),
            environ.get("JIRA_PROJECT"),
            (datetime.today() - timedelta(days=30)).date()
        ]

        #test
        to_test(*args)
        
        self.assertTrue(path.isfile(path.join(self.tmpdir.name, "output.csv")))
        self.assertGreater(path.getsize(path.join(self.tmpdir.name, "output.csv")), 0)