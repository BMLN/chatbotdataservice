from os import environ, path
import requests

from datetime import date


from tempfile import TemporaryDirectory
from shutil import rmtree






ticketdata_serviceurl = environ.get("DATASERVICE_SERVICEURL")

timestamp = environ.get("DATASERVICE_TIMESTAMP")
timestamp = timestamp if timestamp else date.today().strftime(r"%Y-%m-%d")


assert ticketdata_serviceurl
assert timestamp




try:
    with TemporaryDirectory(delete=False) as td:
        #pretty ugly sofar tbh
        textdata = path.join(td, "tickets.csv")
        generationdata = path.join(td, "generations.csv")
        encodingdata = path.join(td, "encodings.jsonl")


        #fetch ticketdata
        if (response := requests.get(
            ticketdata_serviceurl + "/fetch_ticketdata",
            params={
                "updated": timestamp
            }
        )).status_code != 200:
            raise Exception(f"/fetch_ticketdata: {response.status_code}")
        
        with open(textdata, "wb") as f:
            f.write(response.content)


        #generate ticketdata
        if (response := requests.get(
            ticketdata_serviceurl + "/generate_ticketdata",
            files={ textdata: open(textdata, "rb") }
        )).status_code != 200:
            raise Exception(f"/generate_ticketdata: {response.status_code}")
        
        with open(generationdata, "wb") as f:
            f.write(response.content)


        #generate kbdata
        if (response := requests.get(
            ticketdata_serviceurl + "/generate_kbdata",
            files={ generationdata: open(generationdata, "rb") },
            params={"text_column": "problem", "data_column": ["issue_key", "problem", "solution"]}
        )).status_code != 200:
            raise Exception(f"/generate_kbdata: {response.status_code}")
        
        with open(encodingdata, "wb") as f:
            f.write(response.content)

        
        #load kbdata
        if (response := requests.post(
            ticketdata_serviceurl + "/load_kbdata",
            files={ encodingdata: open(encodingdata, "rb") }
        )).status_code != 200:
            raise Exception(f"/load_kbdata: {response.status_code}")
    
        environ["TICKETDATA_SERVICEURL"] = timestamp

except Exception as e:
    print(e)
    
finally:
    rmtree(td, ignore_errors=True)

