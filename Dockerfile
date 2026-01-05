FROM ghcr.io/astral-sh/uv:bookworm-slim AS env


COPY pyproject.toml /opt/dataservice/pyproject.toml
WORKDIR /opt/dataservice

RUN apt update
RUN apt upgrade
RUN apt install --yes git
RUN uv sync --group text-generate --group kb-generate --group kb-load
RUN uv pip install --no-deps git+https://github.com/bmln/botter.git
RUN uv pip install --no-deps git+https://github.com/bmln/chatterbot.git





FROM env AS env-slim


ARG TEXT_GENERATE=true
ARG KB_GENERATE=true
ARG KB_LOAD=true

RUN touch deps_active
RUN touch deps_removable

RUN for x in "TEXT-GENERATE" "KB-GENERATE" "KB-LOAD"; do \
    lowered=$(echo "$x" | tr '[:upper:]' '[:lower:]'); \
    if [ "$(eval echo \$$(echo "$x" | tr '-' '_'))" = "true" ] ; then \
        uv tree -d 1 --group "$lowered" | grep "(group: $lowered)" | awk '{print $2}' >> deps_active; \
    else \
        uv tree -d 1 --group "$lowered" | grep "(group: $lowered)" | awk '{print $2}' >> deps_removable; \
    fi; \
done
RUN grep -Fvx -f deps_active deps_removable > deps_removed || true
RUN cat deps_removed | while read line; do uv pip uninstall $line; done








FROM env-slim AS runtime

COPY src/ /opt/dataservice
ENTRYPOINT ["uv", "run", "flask", "run"]