## dataservice for jira_bot

!! needs additional !!

    uv sync --all-groups

    uv pip install --no-deps git+https://github.com/BMLN/botter
    uv pip install --no-deps git+https://github.com/BMLN/chatterbot


for some of the features of those packages since uv doesnt support --no-deps yet


!! .env !! shouldn't contain <"> in file when passed to gunicorn



#### contains:
- fetching tickets
- generating data from tickets
- encoding into kb-data format
- loading kb-data into kb



#### TODOS:
- locks for concurrency
