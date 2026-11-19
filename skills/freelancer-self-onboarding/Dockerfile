FROM node:22-bookworm-slim
ARG CODEX_VERSION=0.169.0
ARG CLAUDE_VERSION=2.1.325
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git python3 ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global "@openai/codex@${CODEX_VERSION}" \
       "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
    && npm cache clean --force \
    && codex --version && claude --version
COPY . /opt/freelancer-self-onboarding
ENV HOME=/home/operator \
    CODEX_HOME=/home/operator/.codex \
    CLAUDE_CONFIG_DIR=/home/operator/.claude \
    ENABLE_CLAUDEAI_MCP_SERVERS=false \
    PYTHONDONTWRITEBYTECODE=1
USER node
WORKDIR /work
ENTRYPOINT ["python3", "/opt/freelancer-self-onboarding/scripts/guest.py"]
