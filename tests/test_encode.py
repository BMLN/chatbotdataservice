import unittest
from os import path
from tempfile import TemporaryDirectory
from typing import override




from src.processing import encode_dataset






class EncodingTest(unittest.TestCase):

    @override
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

        with open(path.join(self.tmpdir.name, "testdata.csv"), "w", encoding="utf-8") as f:
            f.write("""id,name,data\n1,name1,This is some random text data\n2,name2,this is some other random text data""")




    def test_w_csv(self):
        to_test = encode_dataset.encode

        #args
        args = {
            "input": path.join(self.tmpdir.name, "testdata.csv"),
            "output": path.join(self.tmpdir.name, "testoutput.jsonl"),
            "encoder_model": "Qwen/Qwen3-Embedding-4B",
            "text_column": "data",
            "batch_size": 10
        }

        #test
        to_test(**args)

        with open(path.join(self.tmpdir.name, "testoutput.jsonl"), "r") as f:
            rows = 0
            
            for x in f.readlines():
                if not x.strip():
                    break
                
                if not "embedding" in x:
                    raise self.failureException
                
                rows += 1
                
            self.assertEqual(rows, 2)