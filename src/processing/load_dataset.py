import sys
from os import path, mkdir
from tempfile import TemporaryDirectory
from shutil import copy, rmtree

from data.load import estimate_chunks
from data.iter import BatchProcessor, PandasProcessor
from ast import literal_eval

from chatbot.instances.knowledgebases import WeaviateKB
import pandas as pd






from argparse import ArgumentParser


from logging import getLogger, basicConfig, INFO, ERROR
basicConfig(level=ERROR)
logger = getLogger()











def preproc(x):
    if x is None:
        return None
    
    if isinstance(x, str):
        return literal_eval(x)
    
    return x



def processor(data, kb):
    __data = data[data.columns.difference(["id", "embedding"])]
    __data = __data.to_dict(orient="records") or [ {} ] * len(data)
    __id = data["id"].apply(preproc) if "id" in data else None
    __id = __id if not id and __id.any() else None #bandaid #TODO: other impl
    __embedding = data["embedding"].apply(preproc) if "embedding" in data else None
    
  
    kb.create(
        id=__id,
        embedding=__embedding,
        data=__data
    )
    del data






def load(files, host, port, collection, batch_size, designated_load, designated_bytes, error_threshold):
    
    #connection
    try:
        conn = WeaviateKB(host, port, collection)
        logger.info(f"initializing {collection}...")
    except:
        logger.error(f"couldn't connect to knowledgebase[{WeaviateKB.__name__}]")
        sys.exit(1)



    #read/write
    succesful_reads = []



    for x in files:

        if not path.isdir("./.processing"):
            mkdir("./.processing")

        if not path.isdir(proc_dir:= path.join("./.processing", path.basename(x).split(".")[0])):
            mkdir(proc_dir)


        if True:
            logger.info(f"initializing from {x}...")

            with TemporaryDirectory(dir=proc_dir, delete=False) as td:
                copy(x, inp:= path.join(td, path.basename(x)))

                BatchProcessor.process(
                    inp,
                    lambda file:
                        PandasProcessor.process(
                            file, 
                            processor,
                            False,
                            batch_size=batch_size,
                            kb=conn
                        ),
                    batch_size= batch_size if batch_size else estimate_chunks(x, designated_bytes, load=designated_load)
                )
            
            rmtree(td)
            succesful_reads.append(True)


        # except Exception as e:
        #     logger.error(f"could't read {x}: {str(e)}")
        #     succesful_reads.append(False)



    #cli exection code
    if succesful_reads and sum(succesful_reads) / len(succesful_reads) < error_threshold:
        logger.error(f"too many reads failed! ({sum(succesful_reads)}/{len(succesful_reads)})")
        sys.exit(1)









if __name__ == "__main__":
    
    #configuration
    args = ArgumentParser("load")
    args.add_argument("files", action="store", nargs="+", type=str)
    args.add_argument("--host", action="store", type=str, required=True)
    args.add_argument("--port", action="store", type=str, required=True)
    args.add_argument("--collection", action="store", type=str, required=True)

    args.add_argument("--batch_size", action="store", type=int, default=None)
    args.add_argument("--designated_load", action="store", type=float, default=0.25)
    args.add_argument("--designated_bytes", action="store", type=int, default=500000000)
    args.add_argument("--error_threshold", action="store", type=float, default=0.8)
    
    args = args.parse_args()


    load(
        args.files,
        args.host,
        args.port,
        args.collection,
        args.batch_size,
        args.designated_load,
        args.designated_bytes,
        args.error_threshold
    )




    