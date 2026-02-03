FROM ghcr.io/astral-sh/uv:bookworm-slim AS env


RUN apt update
RUN apt upgrade --yes
RUN apt install --yes git
RUN apt-get install --yes curl && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml /opt/dataservice/pyproject.toml
WORKDIR /opt/dataservice
RUN uv sync --all-groups
RUN uv pip install --no-deps git+https://github.com/bmln/chatterbot.git





FROM env AS env-slim


ARG TEXT_FETCH=true
ARG TEXT_GENERATE=true
ARG KB_GENERATE=true
ARG KB_LOAD=true
ARG PDF_PROCESS=false

RUN touch deps_active
RUN touch deps_removable

RUN for x in "TEXT_FETCH" "TEXT-GENERATE" "KB-GENERATE" "KB-LOAD" "PDF-PROCESS"; do \
    lowered=$(echo "$x" | tr '[:upper:]' '[:lower:]'); \
    if [ "$(eval echo \$$(echo "$x" | tr '-' '_'))" = "true" ] ; then \
        uv tree -d 1 --group "$lowered" | grep "(group: $lowered)" | awk '{print $2}' >> deps_active; \
    else \
        uv tree -d 1 --group "$lowered" | grep "(group: $lowered)" | awk '{print $2}' >> deps_removable; \
    fi; \
done
RUN grep -Fvx -f deps_active deps_removable > deps_removed || true
RUN cat deps_removed | while read line; do uv pip uninstall "$line"; done








FROM env-slim AS runtime

COPY src/ /opt/dataservice

ENTRYPOINT ["uv", "run", "gunicorn", "app:app", "--preload"]
