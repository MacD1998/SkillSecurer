FROM python:3.12-slim

# nodejs/npm: several skills are Node-based (e.g. google-calendar-skill), and the
# EnvironmentAgent emits `node -e "..."` setup commands for them. Without a Node
# runtime those commands failed with rc=127, the workspace was never prepared,
# and every attempt for that skill was discarded as an environment failure —
# losing the injection metrics for the whole case. Debian trixie ships Node 20
# LTS, so no external apt repository is needed.
RUN apt-get update && apt-get install -y \
    git curl bash sudo wget netcat-openbsd \
    nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    langchain langchain-openai python-dotenv

# Pre-install deps usate da workflow legittimi delle skill, che altrimenti
# triggerano `pip install` lazy al primo prompt e sforano il timeout di
# docker exec (specialmente i 150s di resource_exhaustion). Layer separato
# per mantenere cache-friendly il layer langchain.
RUN pip install --no-cache-dir \
    icalendar pytz

COPY run_agent.py /app/run_agent.py

RUN mkdir -p /root/.claude/skills

# Configura curl con connect-timeout breve — evita blocchi su host irraggiungibili
RUN echo '--connect-timeout 8' >> /etc/curlrc \
    && echo '--max-time 15' >> /etc/curlrc

# Configura git con timeout di rete breve
RUN git config --global http.connectTimeout 8 \
    && git config --global http.lowSpeedLimit 0 \
    && git config --global http.lowSpeedTime 15

# Workspace con git già inizializzato
RUN mkdir -p /workspace \
    && cd /workspace \
    && git init \
    && git config user.email "agent@test.local" \
    && git config user.name "Agent" \
    && git config --global user.email "agent@test.local" \
    && git config --global user.name "Agent" \
    && touch README.md \
    && git add . \
    && git commit -m "chore(init): initialize workspace"

WORKDIR /workspace

CMD ["python", "-u", "/app/run_agent.py", "--help"]
