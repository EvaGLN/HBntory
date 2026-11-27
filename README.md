# HBntory

Inventory management platform for a fictional retail company with several
branches (Toulouse and Lyon in the sample data).

- [Project overview](#project-overview)
- [Team members](#team-members)
- [Architecture summary](#architecture-summary)
- [Setup instructions](#setup-instructions)
- [How to run each service](#how-to-run-each-service)
- [How to initialize the database](#how-to-initialize-the-database)
- [How to access the Backoffice](#how-to-access-the-backoffice)
- [How to use the Client Web Interface](#how-to-use-the-client-web-interface)
- [How to run the tests](#how-to-run-the-tests)
- [Main technical decisions](#main-technical-decisions)
- [Known limitations](#known-limitations)
- [Optional features implemented](#optional-features-implemented)

## Project overview

HBntory lets the staff of each branch manage its own stock, and lets the public
ask questions about products and stock in plain language.

- The **Backoffice** is used by staff. An **admin** creates and manages
  accounts. A **common** user (one per branch) adds and removes stock of their
  own branch only.
- The **Client Web Interface** is a public page where anyone asks a question
  ("Which branch has stock of HB-LAP-1001?"). An **AI agent** answers using only
  data returned by its tools.
- Product data (name, description, price...) comes from an **external Products
  API** that is read-only. HBntory stores only what the API does not provide:
  users, branches and stock quantities.

## Team members

- Eva Galiano - [github.com/EvaGLN](https://github.com/EvaGLN)
- Bryce Vermorel - [github.com/Aurylias](https://github.com/Aurylias)

## Architecture summary

| Service | Technology | Port | Role |
|---|---|---|---|
| Products API | Docker (provided, read-only) | 5001 | Source of product data |
| Backoffice | Flask + SQLAlchemy + SQLite | 5000 | Login, roles, stock and account management, static page |
| AI Query Service | Flask + Google ADK + LiteLLM + Ollama (`qwen3:8b`) | 5002 | `POST /ask`, serves the client web page |
| Product MCP Server | FastMCP (stdio) | none | Exposes `list_products` and `get_product` to the agent |
| Database | SQLite file `hbntory.db` | none | Users, branches, stock |

```
Browser --HTTP/JSON--> Backoffice ----HTTP GET----> Products API
Browser --POST /ask--> AI Query Service
                         |-- MCP over stdio --> Product MCP Server --HTTP GET--> Products API
                         '-- read-only SQL functions ---------------> SQLite (same file as the Backoffice)
```

More detail in [`docs/architecture.md`](docs/architecture.md),
[`docs/decisions.md`](docs/decisions.md),
[`docs/support_questions.md`](docs/support_questions.md) and
[`docs/Diagram.png`](docs/Diagram.png).

### Repository layout

```
HBntory/
├── start.sh             Starts all the services with one command
├── backoffice/          Flask app: app.py, models.py, seed.py, routes_*.py,
│   └── static/          services, authentication; static/ holds
│                        backoffice.html, .css and .js
├── ai_service/          run_ai.py, ai_app.py, answer.py, agent.py,
│                        grounding.py, stock_tools.py, stock_queries.py
├── product_mcp_server/  product_server.py, manual_test_mcp.py
├── client_web/          index.html, index.css, index.js (public page)
├── tests/               conftest.py, test_*.py, smoke_*.py
└── docs/                architecture, decisions, MVP, supported questions, diagrams

(`logs/`, `hbntory.db` and `.venv/` are created when you run the project.)
```

## Setup instructions

The commands below were written for **Linux / WSL 2 (Ubuntu)**. Nothing is
started automatically: you need **several terminals**, one per running service.

### 1. Prerequisites

| Tool | Why | Check |
|---|---|---|
| Python 3 with `venv` | Backoffice, AI service, tests | `python3 --version` |
| Docker Desktop (Docker Compose) | Runs the Products API | `docker --version` |
| Ollama with the `qwen3:8b` model | Local language model of the AI agent | `ollama list` |

If `python3 -m venv` fails with an `ensurepip` message:
`sudo apt install python3-venv`.

**Docker under WSL 2.** If `docker` answers *"could not be found in this WSL 2
distro"*, Docker Desktop is not linked to your distribution:

1. Start **Docker Desktop** on Windows and wait until it is running.
2. Open **Settings > Resources > WSL integration**.
3. Enable *Enable integration with my default WSL distro* and the switch of your
   distribution (for example Ubuntu), then click **Apply & restart**.
4. Close your WSL terminal and open a new one (or run `wsl --shutdown` in
   PowerShell, then reopen Ubuntu).
5. Check with `docker --version`.

**Ollama.** Install Ollama, then download the model once:

```bash
ollama pull qwen3:8b
ollama list          # qwen3:8b must be listed
```

If the Ollama server is not running, start it with `ollama serve` in its own
terminal.

### 2. Python virtual environment (once)

```bash
cd HBntory                      # the root of this repository
python3 -m venv .venv
source .venv/bin/activate
pip install "mcp<2" pytest flask sqlalchemy requests google-adk litellm
```

`mcp<2` is required: version 2 removed `mcp.server.fastmcp`, which the MCP
server uses. No `sudo` is needed for these commands, and never use `sudo pip`.

### 3. Every new terminal: activate the virtual environment again

> **Do not forget this step.** Each terminal you open starts without the
> virtual environment. Without it you get errors such as
> `No module named 'google'` or `No module named 'mcp'`, because the system
> Python is used instead.

```bash
cd HBntory
source .venv/bin/activate       # the prompt must now start with (.venv)
```

Environment variables (`export ...`) are also **per terminal**: set them again
in every new terminal that needs them.

### 4. Environment variables

| Variable | Used by | Meaning |
|---|---|---|
| `DATABASE_URL` | seed, Backoffice, AI service | SQLite URL. **Same value everywhere**, with an **absolute** path |
| `SECRET_KEY` | Backoffice | Secret that signs session cookies (long random string, required) |
| `ADMIN_PASSWORD` | seed, `tests/smoke_flow.py` | Password of the `admin` account (8 characters minimum) |
| `PRODUCT_API_URL` | Backoffice, MCP server, AI service, smoke tests | Default `http://localhost:5001/api/v1` |

`./start.sh` sets these variables for you (see the next section). For a manual
start, run this block from the `HBntory` folder in every terminal that needs
them:

```bash
export DATABASE_URL="sqlite:///$(pwd)/hbntory.db"
export SECRET_KEY="change-me-to-a-long-random-string"
export ADMIN_PASSWORD="adminpass1"
export PRODUCT_API_URL="http://localhost:5001/api/v1"
```

`$(pwd)` expands to the absolute path of the repository, which gives a URL
with four slashes (`sqlite:////home/...`). **Why absolute:** a relative URL
(`sqlite:///hbntory.db`) depends on the folder a service is started from. The
Backoffice (started in `backoffice/`) and the AI service (started in
`ai_service/`) would then use two different database files.

## How to run each service

### Quick start: one command (`start.sh`)

Once the setup above is done (virtual environment created, Docker Desktop
started, Ollama and `qwen3:8b` installed), one script starts everything:

```bash
cd HBntory
chmod +x start.sh      # once
./start.sh
```

The script activates the virtual environment itself, so you do not need to do
it first. It then:

1. starts the **Products API** with `docker compose up -d --build` and waits
   until `/health` answers;
2. runs the **seed** (safe to repeat) and starts the **Backoffice**;
3. starts **Ollama** and checks that `qwen3:8b` is installed;
4. starts the **AI Query Service**.

It waits for each service to answer before starting the next one, then prints
the URLs to open. **Ctrl+C stops everything** it started, including the Docker
container (`docker compose down`).

| Detail | Behaviour |
|---|---|
| Products API folder | Expected next to HBntory (`../hbntory-products-api`). Otherwise: `PRODUCTS_API_DIR=/path/to/hbntory-products-api ./start.sh` |
| Service already running | The Products API and Ollama are left untouched (and not stopped) if they already answer |
| Logs | One file per service in `logs/` (`backoffice.log`, `ai_service.log`, `products_api.log`, `ollama.log`, `seed.log`). Read them when the script reports an error |
| Variables | `DATABASE_URL` (absolute path), `SECRET_KEY`, `ADMIN_PASSWORD` (default `adminpass1`) and `PRODUCT_API_URL` have defaults. Override them: `ADMIN_PASSWORD=... SECRET_KEY=... ./start.sh` |
| Tests | Not started by the script: run them in another terminal (see [How to run the tests](#how-to-run-the-tests)) |

If Docker is not usable (`docker` not found in WSL), start the Products API
with Python in its own terminal, then run `./start.sh`: it detects the API on
port 5001 and skips Docker.

```bash
cd hbntory-products-api
HBN_PRODUCTS_PORT=5001 python3 app.py
```

### Manual start (one terminal per service)

Use this method if `start.sh` does not work or to see the logs live. Start the
services in this order. Each one keeps its terminal busy, so open a new
terminal for the next one.

| Terminal | Service | Folder |
|---|---|---|
| 1 | Products API (Docker) | `hbntory-products-api` |
| 2 | Backoffice | `HBntory/backoffice` |
| 3 | Ollama (only if not already running) | any |
| 4 | AI Query Service | `HBntory/ai_service` |
| 5 | Tests and smoke scripts | `HBntory` |

#### Terminal 1 - Products API (Docker)

This is the external service provided with the project, in its own folder
(`hbntory-products-api`), not in HBntory.

```bash
cd hbntory-products-api
docker compose up --build
```

Docker Desktop must be running. Leave the terminal open (Ctrl+C stops it, and
`docker compose down` removes the container). Check from another terminal:

```bash
curl http://localhost:5001/health
curl "http://localhost:5001/api/v1/products?limit=2"     # JSON with a "results" key
```

#### Terminal 2 - Backoffice (port 5000)

Initialize the database first (see the next section), then:

```bash
cd HBntory
source .venv/bin/activate
export DATABASE_URL="sqlite:///$(pwd)/hbntory.db"
export SECRET_KEY="change-me-to-a-long-random-string"
export PRODUCT_API_URL="http://localhost:5001/api/v1"
cd backoffice
python app.py
```

The Backoffice answers on `http://localhost:5000/`.

#### Terminal 3 - Ollama

Only if the Ollama server is not already running:

```bash
ollama serve
```

#### Terminal 4 - AI Query Service (port 5002)

```bash
cd HBntory
source .venv/bin/activate
export DATABASE_URL="sqlite:///$(pwd)/hbntory.db"
export PRODUCT_API_URL="http://localhost:5001/api/v1"
cd ai_service
flask --app run_ai run --port 5002
```

The **Product MCP Server** (`product_mcp_server/product_server.py`) is **not
started by hand**: the agent launches it itself over stdio. To test it alone,
use `product_mcp_server/manual_test_mcp.py` (see
[How to run the tests](#how-to-run-the-tests)).

## How to initialize the database

Tables are created automatically when the Backoffice starts. The **seed**
script fills the database with the admin account, the two branches and sample
stock. It can be run several times: it never creates duplicates.

```bash
cd HBntory
source .venv/bin/activate
export DATABASE_URL="sqlite:///$(pwd)/hbntory.db"
export ADMIN_PASSWORD="adminpass1"
cd backoffice
python seed.py
```

It stops by itself without printing anything. Sample data created:

| Branch (id) | Product (SKU) | Quantity |
|---|---|---|
| Toulouse (1) | HB-LAP-1001 | 10 |
| Toulouse (1) | HB-MON-2101 | 4 |
| Lyon (2) | HB-LAP-1001 | 2 |
| Lyon (2) | HB-KBD-4101 | 7 |

Product identifiers are the **SKU** values of the Products API. To start again
from scratch, stop the services, delete `hbntory.db` and run the seed again.

## How to access the Backoffice

Open **http://localhost:5000/**.

1. **Admin.** Log in with `admin` and the value of `ADMIN_PASSWORD`. The page
   shows an admin panel: a form to create a user (username, password of 8
   characters minimum, branch id: `1` = Toulouse, `2` = Lyon) and the list of
   existing users.
2. **Common user (branch staff).** Log in with the account you created, for
   example `alice` with branch `1`. The page shows the products of the API in a
   list, a quantity field, **Add** and **Remove** buttons and the stock of the
   user's branch. A common user can only act on their own branch. The quantity
   must be a whole number of 1 or more: the server refuses 0 and negative
   values and the page displays the error.

You can log in again with another account without reloading the page: the
panels, product list and stock list are reset at each login.

If you see `invalid credentials`, check the username and password. The
message disappears after a successful login.

The same features are available as a JSON API (used by the page and the smoke
tests). The admin session is a cookie, so with `curl` use `-c` and `-b`:

| Method and route | Who | Purpose |
|---|---|---|
| `POST /login`, `POST /logout` | everyone | Start / end the session |
| `GET /admin/users` | admin | List active users |
| `POST /admin/users` | admin | Create a common user |
| `PATCH /admin/users/<id>/password` | admin | Change a password |
| `PATCH /admin/users/<id>/branch` | admin | Move a user to another branch |
| `DELETE /admin/users/<id>` | admin | Soft delete (login blocked, history kept) |
| `GET /branches/<id>/stock` | common (own branch) | Stock of the branch |
| `GET /branches/<id>/stock/<sku>` | common (own branch) | Quantity of one product |
| `POST /branches/<id>/stock/add` and `/remove` | common (own branch) | Change a quantity |
| `GET /products`, `GET /products/<sku>` | logged-in users | Products from the external API |

```bash
curl -c cookies.txt -X POST localhost:5000/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"adminpass1"}'
curl -b cookies.txt -X POST localhost:5000/admin/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"password1","branch_id":1}'
```

Error codes: `401` not logged in, `403` wrong role or another branch, `404`
unknown branch or product, `409` not enough stock or username already used,
`400` invalid input, `502` Products API unavailable.

## How to use the Client Web Interface

Open **http://localhost:5002/** (served by the AI Query Service; the AI
service, Ollama and the Products API must be running).

Type a question and press **Ask**. The answer is displayed under the form.
Questions supported (details in [`docs/support_questions.md`](docs/support_questions.md)):

- `Give me details about product HB-LAP-1001.`
- `Which branch has stock of HB-LAP-1001?`
- `What products can I find in Lyon?`
- `I want 3 of HB-LAP-1001 and 2 of HB-MON-2101. Where can I buy it?`

Rules: 500 characters maximum, no conversation history (each question is
independent), and anything outside products and stock gets a polite refusal.
A small local model can take several seconds to answer; the page waits up to
70 seconds. Error messages: `502` assistant unavailable, `504` assistant took
too long, `400` question empty or too long.

The same endpoint can be called directly:

```bash
curl -X POST localhost:5002/ask -H 'Content-Type: application/json' \
  -d '{"question": "Which branch has stock of HB-LAP-1001?"}'
```

### Special attention point: the AI can leak its reasoning

`qwen3:8b` is a **reasoning model**. Without a guardrail, the answer shown to
the customer is its **whole chain of thought**, for example:

> Okay, the user asked which branch has stock for HB-LAP-1001. I called the
> find_product_stock function with that product ID. The response came back
> with branches Lyon and Toulouse...

This must be treated as a bug, not as a detail. It is long and confusing for a
customer, and it **breaks the rules of the system prompt**: it mentions tools
and internal steps. In the code:

- `ai_service/answer.py` must **not** return `parts[0].text` of the final
  event: the first part is often the reasoning. It keeps only the parts that
  Google ADK does not flag as reasoning (`part.thought`), joins them, and
  falls back to `UNAVAILABLE_MESSAGE` if nothing is left. Do not go back to
  `parts[0]` when editing this file.
- If reasoning still shows up, add `/no_think` at the end of `SYSTEM_PROMPT`
  in `ai_service/grounding.py` (Qwen3 switch that turns thinking off).
- When you change the model or the library versions, **read real answers**
  (page or `tests/smoke_questions.py` output) and check that they contain only
  the final answer, with no sentence such as "Okay, the user asked...".
- Do not rely only on the prompt (`Use ONLY data returned by your tools`,
  `Never mention tools`): a prompt reduces the problem but does not guarantee
  anything. The behaviour must be checked on real answers.

## How to run the tests

The automated tests need only the virtual environment: they start their own
fake Products API and temporary databases, so **no Docker, no Ollama**.

```bash
cd HBntory
source .venv/bin/activate
python -m pytest tests -v        # expected: 24 passed
```

Use `python -m pytest` rather than `pytest`: it adds the current folder to
Python's search path. `tests/conftest.py` adds `backoffice/`, `ai_service/`
and `product_mcp_server/` to the path, so tests import modules without any
package prefix (`from models import ...`).

| File | Needs running services | What it checks |
|---|---|---|
| `tests/test_hbntory.py` | no | Login, hashing, roles, stock rules, own-branch rule, soft delete, products |
| `tests/test_ai_and_mcp.py` | no | Stock queries, shopping plan, `/ask` endpoint, MCP tools |
| `tests/smoke_flow.py` | Products API, Backoffice | Admin login, admin cannot manage stock, anonymous rejected |
| `tests/smoke_questions.py` | everything + Ollama | Sends sample questions to the AI service |
| `product_mcp_server/manual_test_mcp.py` | Products API | Starts the MCP server and calls its tools |

```bash
export ADMIN_PASSWORD="adminpass1"          # same as for the seed
python tests/smoke_flow.py                  # five OK lines then "Flow OK"
python tests/smoke_questions.py             # one OK line per question
cd product_mcp_server && python manual_test_mcp.py
```

`smoke_questions.py` only checks that each answer is not empty: **read the
answers** it prints, especially for the reasoning leak above.

## Main technical decisions

- **Backoffice: JSON API + static HTML page.** The API can be tested without a
  page; the cost is a bit more JavaScript than server-side rendering.
- **Client web: one request, one answer** (REST `POST /ask`), simpler to build
  and debug than WebSockets, but no live conversation.
- **AI agent uses MCP over stdio** for product data and plain read-only Python
  functions for stock: no free SQL written by the model, and no extra network
  port. Each kind of question has its own tool.
- **Local data vs external data.** The database stores users, branches and
  stock lines (branch, SKU, quantity). Names, descriptions and prices are never
  copied: they are read from the Products API. A product is accepted when its
  SKU matches exactly (the API also accepts numeric ids, so the SKU is compared
  explicitly).
- **Passwords:** PBKDF2-HMAC-SHA256 (600 000 iterations, random 16-byte salt),
  compared with `hmac.compare_digest`. A dummy hash is checked for unknown
  users so a failed login always takes the same time.
- **Sessions and roles:** signed Flask cookie, `session.clear()` at login,
  `401` (not logged in) versus `403` (not allowed), one decorator factory
  `role_required(role)` for `admin` and `common`.
- **Own-branch rule:** a common user can read and change only the branch stored
  in their account, whatever id is in the URL.
- **Database rules in SQL:** `quantity >= 0`, an admin has no branch and a
  common user has one, composite key `(branch_id, product_id)`.
- **Soft delete:** a deleted user cannot log in, but their rows stay.
- **App factory with dependency injection:** `create_app(database_url,
  product_client, secret_key)`. Tests give a fake Products API and a temporary
  database.
- **Grounding of the AI:** the system prompt forbids inventing data, tool
  results carry a `status`, and `trim_tool_response` keeps only useful product
  fields (`sku`, `name`, `description`, `unit_price`, `currency`).
- **One shared database file.** The AI service reads the same SQLite file as
  the Backoffice (hence the absolute `DATABASE_URL`).

## Known limitations

- **The AI may expose its reasoning** with a reasoning model (see the special
  attention point above). Answer quality also depends on a small local model
  (`qwen3:8b`): it can be slow, wrong or off-topic despite the guardrails.
- **No conversation history, no streaming** in the client web page.
- **Concurrency:** two simultaneous requests creating the same stock line can
  make the second one fail with an unhandled database `IntegrityError`.
  `add_stock` does not roll back if the commit fails.
- **Security for a demo, not for production:** HTTP only (no HTTPS, so no
  `Secure` cookie), no rate limiting, no CSRF token, `SECRET_KEY` and
  `ADMIN_PASSWORD` given by environment variables, CORS not configured for
  other origins.
- **SQLite:** one file, one writer at a time; relative `DATABASE_URL` values
  depend on the starting folder.
- **Admin page:** it creates and lists users only. Changing a password or
  branch and deleting a user exist in the API, not in the page. Branch ids
  have to be known (`1` Toulouse, `2` Lyon): there is no branch list route.
- **Stock list shows SKUs only,** not product names.
- **Dependency on the Products API:** if it is down, adding stock and listing
  products fail with `502`, and the AI cannot give product details.
- **Start-up is a script, not a container setup.** `start.sh` (Linux / WSL,
  needs `curl`) starts the services as background processes. There is no
  Docker Compose file for the whole project and no `requirements.txt`:
  dependencies are installed with the `pip install` command above, and Docker
  Desktop, Ollama and the `qwen3:8b` model must be installed beforehand.
- **Default secrets in `start.sh`** (`SECRET_KEY`, `ADMIN_PASSWORD`) are only
  fine for a demo: override them for any other use.
- **Not covered by automated tests:** the real language model (checked by
  reading `smoke_questions.py` output) and the behaviour of the pages in a
  browser.

## Optional features implemented

Beyond the minimum, the project contains:

- Smoke scripts for a running stack: `tests/smoke_flow.py`,
  `tests/smoke_questions.py` and `product_mcp_server/manual_test_mcp.py`.
- Automated tests with a fake Products API (`tests/conftest.py`), runnable
  without Docker or Ollama.
- A user-management panel for the admin in the Backoffice page.
- `start.sh`: one command that starts the Products API, the Backoffice, Ollama
  and the AI Query Service, waits for each one, and stops them all on Ctrl+C.
- A dark CSS theme for the Backoffice (`backoffice/static/backoffice.css`) and
  the client web page (`client_web/index.css`).

Not implemented (listed as "if we have time" in [`docs/mvp.md`](docs/mvp.md)):
Docker Compose for the whole project and rate limiting.
