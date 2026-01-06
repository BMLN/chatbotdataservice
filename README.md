## dataservice for jira_bot

!! needs additional !!

    uv sync

    uv pip install --no-deps git+https://github.com/BMLN/botter
    uv pip install --no-deps git+https://github.com/BMLN/chatterbotter


for some of the features of those packages since uv doesnt support --no-deps yet



#### contains:
- fetching tickets
- generating data from tickets
- encoding into kb-data format
- loading kb-data into kb



#### TODOS:
- should move all ov processing scripts into repository (bot imports from here not the other way around)