import sys
from os import path, mkdir
from tempfile import TemporaryDirectory
from shutil import copy, rmtree

import pandas as pd
from data.load import estimate_chunks
from data.iter import BatchProcessor, PandasProcessor

from chatbot.instances.vectorizers import HFVectorizer




from argparse import ArgumentParser









def encode(input, output, encoder_model, text_column, batch_size=None, designated_load=0.25, designated_bytes=50000000):
    
    encoder = HFVectorizer(encoder_model)
    
    def process_df(df):
        if not text_column in df:
            raise ValueError(f"text_column ({text_column}) is invalid for inputdata {input} ({df.columns.tolist()})")
                
        if df.empty == True:
            return
        
        df["embedding"] = df[text_column].apply(str)
        df["embedding"] = encoder.vectorize(df["encoding"].tolist())

        df.to_json(output, mode="a", lines=True, orient="records")            

        del df



    if not path.isdir("./.processing"):
        mkdir("./.processing")

    if not path.isdir(proc_dir:= path.join("./.processing", path.basename(input).split(".")[0])):
        mkdir(proc_dir)


    with TemporaryDirectory(dir=proc_dir, delete=False) as td:
        copy(input, inp:= path.join(td, path.basename(input)))

        BatchProcessor.process(
            inp, 
            lambda file: 
                PandasProcessor.process(
                    file, 
                    process_df,
                    False
                ),
            batch_size= batch_size if batch_size else estimate_chunks(input, designated_bytes, load=designated_load)
        )
        
    rmtree(td)








if __name__ == "__main__":

    args = ArgumentParser("encode")
    args.add_argument("--encoder_model", action="store", type=str, default="Qwen/Qwen3-Embedding-4B")
    args.add_argument("--input", action="store", type=path.abspath, required=True)
    args.add_argument("--output", action="store", type=path.abspath, default="./data.json")
    args.add_argument("--text_column", action="store", type=str, required=True)
    args.add_argument("--batch_size", action="store", type=int, default=None)
    args.add_argument("--designated_load", action="store", type=float, default=0.25)
    args.add_argument("--designated_bytes", action="store", type=int, default=50000000)

    args = args.parse_args()


    if not path.isfile(args.input):
        print(f"{args.input} isnt a file")
        sys.exit(1)
    
    if path.isfile(args.output):
        print(f"{args.output}-file already exists")
        sys.exit(1)




    try:
        encode(
            args.input, 
            args.output, 
            args.encoder_model,
            args.text_column,
            args.batch_size,
            args.designated_load,
            args.designated_bytes
        )


    except Exception as e:
        print(f"Failed: {e}")

        sys.exit(1)