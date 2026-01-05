from flask import Flask, Response, request, abort, send_file, after_this_request

from importlib.util import find_spec
from os import environ, path
from tempfile import TemporaryDirectory
from shutil import rmtree






from logging import getLogger
logger = getLogger()




#conditional endpoints
active_endpoints = {
    "generate_ticketdata": environ.get("GENERATE_TICKETDATA", True),
    "generate_kbdata": environ.get("GENERATE_KBDATA", True),
    "load_kbdata": environ.get("LOAD_KBDATA", True)
}


if active_endpoints["generate_ticketdata"]:
    try:
        if not find_spec("inference"):
            raise ImportError("""["inference"] package(s) do not seem to be available""")

        if not environ["DEEPINFRA_KEY"]:
            raise ValueError("""unsuitable environment, missing: ['DEEPINFRA_KEY']""")

        from build_dataset import process_csv


    except Exception as e:
        active_endpoints["generate_ticketdata"] = False

        logger.error(f"/generate_ticketdata got disabled: {e}")



if active_endpoints["generate_kbdata"]:
    packages = ["accelerate", "data", "torch", "transformers", "jira_botter", "chatbot"]
    envars = ["ENCODER_MODEL"]

    try:
        if not all(checks := list(map(lambda x: find_spec(x) is not None, packages))):
            raise ImportError(f"{[x for x, check in zip(packages, checks) if not check]} package(s) do not seem to be available")

        if not all(checks := list(map(lambda x: environ.get(x, None) != None, envars))):
            raise ValueError(f"unsuitable environment, missing: {[x for x, check in zip(envars, checks) if not check]}")

        from jira_botter import __encode__


    except Exception as e:
        active_endpoints["generate_kbdata"] = False

        logger.error(f"/generate_kbdata got disabled: {e}")



if active_endpoints["load_kbdata"]:
    packages = ["data", "jira_botter", "chatbot", "weaviate"]
    envars = ["KB_HOST", "KB_PORT", "KB_COLLECTION"]

    try:
        if not all(checks := list(map(lambda x: find_spec(x) is not None, packages))):
            raise ImportError(f"{[x for x, check in zip(packages, checks) if not check]} package(s) do not seem to be available")
        
        if not all(checks := list(map(lambda x: environ.get(x, None) != None, envars))):
            raise ValueError(f"unsuitable environment, missing: {[x for x, check in zip(envars, checks) if not check]}")
        
        from jira_botter import __load__
        

    except Exception as e:
        active_endpoints["load_kbdata"] = False

        logger.error(f"/load_kbdata got disabled: {e}")






if not any(active_endpoints.values()):
    logger.error("no endpoints to serve")
    exit(1)











#service
app = Flask(__name__)


#routes
#generates the bot data
if not active_endpoints["generate_ticketdata"]:
    logger.warning("/generate_ticketdata is disabled")
    
else:
    @app.route("/generate_ticketdata", methods=["POST"])
    def process_csvdata():
        if not request.files:
            abort(400)
        
        if not (file_name := list(request.files.keys())[0]).endswith(".csv"):
            abort(415)
            
            
        with TemporaryDirectory(delete=False) as td:
            src, dest = path.join(td, "src.csv"), path.join(td, "dest.csv")

            try: 
                request.files[file_name].save(src)
                process_csv(src, dest)
                
                @after_this_request
                def cleanup(response):
                    rmtree(td, ignore_errors=True)
                    return response
                
                return send_file(dest)

            except Exception as e:
                logger.error(e)
                abort(500)



#generates the kb data
if not active_endpoints["generate_kbdata"]:
    logger.warning("/generate_kbdata is disabled")

else:
    @app.route("/generate_kbdata", methods=["POST"])
    def process_textdata():
        if not "text_column" in request.args:
            abort(400)
            
        if not "data_column" in request.args:
            abort(400)

        if not request.files:
            abort(400)
            
        if not (file_name := list(request.files.keys())[0]).endswith(".csv"):
            abort(415)
        

        with TemporaryDirectory(delete=False) as td:
            src, dest = path.join(td, "src.csv"), path.join(td, "dest.csv")

            try:
                request.files[file_name].save(src)
                __encode__.encode(
                    src,
                    dest,
                    environ.get("ENCODER_MODEL"),
                    request.args.get("text_column"), #use args instead
                    request.args.getlist("data_colum"),
                    environ.get("ENCODE_BATCHSIZE", 5)
                )
                

                @after_this_request
                def cleanup(response):
                    rmtree(td, ignore_errors=True)
                    return response            

                return Response(status=200)


            except Exception as e:
                logger.error(e)
                abort(500)



#loads the kb data
if not active_endpoints["load_kbdata"]:
    logger.warning("/load_kbdata is disabled")

else:
    @app.route("/load_kbdata", methods=["POST"])
    def process_kbdata():
        if not request.files:
            abort(400)

        if not (file_name := list(request.files.keys())[0]).endswith(".jsonl"):
            abort(415) # f"file doesn't seem to be a .jsonl: {file_name}"


        with TemporaryDirectory(delete=False) as td:
            file = path.join(td, "kbdata.jsonl")

            try: 
                request.files[file_name].save(file)                
                __load__.load(
                    file,
                    environ.get("KB_HOST"),
                    environ.get("KB_PORT"),
                    environ.get("KB_COLLECTION"),
                    environ.get("LOAD_BATCHSIZE", 50),
                    None,
                    None,
                    0.8
                )
                
                @after_this_request
                def cleanup(response):
                    rmtree(td, ignore_errors=True)
                    return response
                
                return Response(status=200)


            except Exception as e:
                logger.error(e)
                abort(500)