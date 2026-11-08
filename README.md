# Python API Automation Testing

[![API tests](https://github.com/alwih/automation-api-py-behave/actions/workflows/api-tests.yml/badge.svg)](https://github.com/alwih/automation-api-py-behave/actions/workflows/api-tests.yml)
[![Lint](https://github.com/alwih/automation-api-py-behave/actions/workflows/lint.yml/badge.svg)](https://github.com/alwih/automation-api-py-behave/actions/workflows/lint.yml)

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

It tests two public APIs with positive, negative and edge-case scenarios: posts and users on [JSONPlaceholder](https://jsonplaceholder.typicode.com/), and the product catalogue and JWT authentication on [DummyJSON](https://dummyjson.com/docs) (lookup, pagination, sorting, search, simulated writes, login, protected routes, token refresh). Responses are also checked against JSON Schema contracts, and the helper code has its own pytest unit tests. Known API bugs, including three security issues, are recorded as scenarios that are skipped by default. Runs can produce an Allure report, with the request and response attached to every failed step, and JUnit XML. GitHub Actions runs everything on each pull request, on pushes to `main` and every night. The code is linted and formatted with ruff and type-checked with mypy, through pre-commit hooks that run before each commit and again in CI.

## Project Structure

```
automation_py_api/
├── .github/workflows/
│   ├── api-tests.yml              # CI: unit tests, smoke, regression; nightly and manual runs
│   └── lint.yml                   # CI: the pre-commit hooks (file checks, ruff, mypy) on pushes and pull requests
├── api/
│   ├── client.py                  # ApiClient + cookie-free session: base URL, timeout, headers, UTF-8 JSON
│   ├── assertions.py              # Response checks with dotted-path field access
│   ├── auth.py                    # DummyJSON credentials and login
│   ├── tokens.py                  # JWT decoding (no signature check) and tampering for negative tests
│   ├── schema.py                  # JSON Schema validation (Draft 2020-12, formats, $ref between files)
│   ├── step_data.py               # "{name}" placeholders and data-table bodies
│   ├── redaction.py               # Hides the configured password in failure output
│   └── report.py                  # Request/response text for the Allure report, credentials masked
├── config/
│   └── settings.py                # Base URLs, timeout and credentials from -D / env / .env / defaults
├── features/
│   ├── dummyjson/
│   │   ├── auth.feature           # Login, token lifetime, protected routes, refresh, security issues
│   │   └── products.feature       # Product lookup, paging, sorting, search, writes
│   ├── jsonplaceholder/
│   │   ├── posts_read.feature     # GET scenarios for posts and comments
│   │   ├── posts_write.feature    # POST, PUT, PATCH, DELETE scenarios
│   │   └── users.feature          # Nested user fields (address, company)
│   ├── environment.py             # Hooks: settings, one client per API, @authenticated login, failure log and attachments
│   └── steps/
│       ├── api_steps.py           # Request and response steps (thin wrappers over api/)
│       └── auth_steps.py          # Login, token and JWT steps
├── schemas/
│   ├── dummyjson/                 # product, product_list, auth_login, error
│   └── jsonplaceholder/           # post, comment, user
├── scripts/
│   └── junit_summary.py           # Turns the JUnit XML into the summary table on the CI run page
├── tests/
│   ├── conftest.py
│   └── unit/                      # pytest: paths, sorting, JWTs, schemas, settings, data tables, reports
├── reports/                       # Created by the make targets (git-ignored): Allure results and HTML, JUnit XML
├── .env.example                   # Template for a local .env (copy and edit)
├── .pre-commit-config.yaml        # Hooks run before each commit: file checks, ruff, mypy
├── .git-blame-ignore-revs         # Formatting-only commits for git blame to skip
├── Makefile                       # Shortcuts: lint, unit, smoke, regression, known-issues, tagged, report, clean
├── behave.ini                     # Behave defaults (paths, format, default tag filter, report formatter)
├── pytest.ini                     # pytest defaults (tests/ folder, imports from the repo root)
├── pyproject.toml                 # ruff and mypy settings
├── environment.yml                # Conda environment (Python 3.11 + requirements-dev.txt)
├── requirements.txt               # Python dependencies for running the tests (pinned)
├── requirements-dev.txt           # requirements.txt plus ruff, mypy, pre-commit and type stubs (pinned)
├── .gitignore                     # Files kept out of version control
└── README.md                      # This file
```

Settings are read once in `before_all`. Every scenario then gets its own `requests.Session` (closed in `after_scenario`) with an `Accept: application/json` header and no cookie storage, and one `ApiClient` per API on top of it: JSONPlaceholder and DummyJSON. Each client adds its base URL and an explicit timeout, so a slow API fails the test instead of hanging the run. A feature picks its API in the `Background`, e.g. `Given the JSONPlaceholder API is available`.

The session keeps no cookies on purpose: DummyJSON's login also sets `accessToken` cookies, which would quietly authenticate later requests and make "no token" or "new token works" checks pass for the wrong reason. Authentication only ever comes from the `Authorization` header a scenario sets.

A feature or scenario tagged `@authenticated` logs in **once** through a behave fixture (`before_tag` + `use_fixture`), which keeps the run well under DummyJSON's rate limit. `Given I am logged in` then sets the bearer token and saves `{access_token}`, `{refresh_token}` and `{user_id}` for later steps.

Step definitions stay small: one step sends any method (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, matched by a custom `HttpMethod` type), and the `Then` steps call functions in `api/assertions.py`. Field names in those steps are dotted paths, so `address.geo.lat` reaches into nested objects and `products.0.id` indexes a list.

List steps work on either shape of list response. JSONPlaceholder returns a bare list (`every item in the response ...`), while DummyJSON wraps it in an object with paging fields (`every item in the "products" list ...`). A step can also save a value for later steps, which is how boundaries that change over time are derived at runtime instead of hard-coded:

```gherkin
Given I send a GET request to "/products?limit=1&select=id"
And I save the response field "total" plus 1 as "next_id"
When I send a GET request to "/products/{next_id}"
Then the response status code should be 404
```

## Prerequisites

- **Python 3.10+** (via miniconda or anaconda; `environment.yml` uses 3.11)
- **Git** (to clone the repository)
- **Internet connection** (to call the public API)
- **make** (optional, for the shortcuts below; preinstalled on macOS and most Linux systems)
- **Allure Report 2** (optional, only to view the HTML report): `brew install allure` on macOS; it needs Java 8 or later

## Setup Instructions

### 1. Install Miniconda (if not already installed)

Download and install from: https://docs.conda.io/en/latest/miniconda.html

Or on macOS with Homebrew:
```bash
brew install --cask miniconda
```

### 2. Create a Conda Environment

```bash
# Clone the repository and move into it
git clone https://github.com/alwih/automation-api-py-behave.git
cd automation-api-py-behave

# Create the 'api_automation' environment (Python 3.11 + requirements-dev.txt)
conda env create -f environment.yml

# Activate the environment
conda activate api_automation
```

### 3. Install Dependencies

`environment.yml` already installs everything in `requirements-dev.txt`: the test dependencies from `requirements.txt` plus the lint and type-check tools. When the pinned versions change, update the existing environment instead of recreating it:

```bash
conda env update -f environment.yml --prune
```

Not using conda? Any Python 3.10+ virtual environment works:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt  # or requirements.txt, to only run the tests
```

Then create your local settings file. The DummyJSON login scenarios need the credentials in it:

```bash
cp .env.example .env
```

Optionally, install the git hooks, so the lint and type checks run on the staged files before each commit:

```bash
pre-commit install
```

## Running the Tests

### Run All Tests with Behave

```bash
# Make sure your environment is active
conda activate api_automation

# Run all scenarios
behave

# Run with verbose output
behave -v

# Run with detailed step output
behave --no-capture
```

Run from the repository root. `behave.ini` points behave at `features/` and uses the `pretty` formatter, so plain `behave` needs no extra arguments.

### Run by Tag

| Tag | Meaning |
|---|---|
| `@smoke` | Fast health check of each API |
| `@regression` | Full coverage of an area |
| `@positive` / `@negative` / `@edge` | Scenario intent: happy path, expected errors, boundaries |
| `@known_issue` | Asserts the correct behavior for a known API bug, so it fails today |
| `@wip` | Work in progress |
| `@security` | A known issue with security impact |
| `@jsonplaceholder` / `@dummyjson` / `@auth` | Which API or area a scenario covers |
| `@authenticated` | Not a filter: logs in once for the tagged feature or scenario |

Plain `behave` skips `@known_issue` and `@wip` (set by `default_tags` in `behave.ini`). A `--tags` option on the command line **replaces** that default instead of adding to it, so add `{config.tags}` to keep the known issues out:

```bash
# Quick health check
behave --tags=@smoke

# Full regression, still skipping known issues and work in progress
behave --tags="@regression and {config.tags}"

# Run only the known issues; they fail with the actual behavior described in each scenario
behave --tags=@known_issue

# Only the error cases
behave --tags=@negative

# Everything except edge cases
behave --tags="not @edge and {config.tags}"

# A single feature file
behave features/jsonplaceholder/posts_write.feature

# Show scenarios skipped by a tag filter (hidden by default in behave.ini)
behave --tags=@smoke --show-skipped
```

### Run the Unit Tests

The helper code under `api/` and `config/` has pytest unit tests. They need no network and finish in well under a second:

```bash
pytest
```

### Lint and Type Checks

ruff lints and formats every Python file, and mypy type-checks `api/` and `config/` in strict mode. Both are configured in `pyproject.toml` and run as pre-commit hooks, together with checks for trailing whitespace, missing final newlines, JSON/YAML/TOML syntax (including the schema files), merge-conflict markers and large files:

```bash
# Every hook on every file (same as make lint)
pre-commit run --all-files

# The tools on their own
ruff check .
ruff format .
mypy
```

The ruff and mypy hooks run the versions installed from `requirements-dev.txt`, so the editor, the hooks and CI use the same ones. When a hook fixes something itself (whitespace, import order, formatting), the commit stops: review the change, `git add` it and commit again.

Formatting-only commits are listed in `.git-blame-ignore-revs`, which GitHub's blame view skips. To skip them in a local `git blame` too, run `git config blame.ignoreRevsFile .git-blame-ignore-revs` once.

### Make Shortcuts and Reports

The `Makefile` wraps the common runs. Its behave targets also write Allure results and JUnit XML under `reports/`, after clearing the files from the previous run:

| Command | What it does |
|---|---|
| `make lint` | Runs every pre-commit hook on every file: file checks, ruff, mypy |
| `make unit` | Runs `pytest` |
| `make smoke` | Runs the `@smoke` scenarios |
| `make regression` | Runs every `@regression` scenario except known issues and work in progress |
| `make known-issues` | Runs only `@known_issue`; it exits with an error for as long as the bugs exist |
| `make tagged TAGS="@dummyjson and {config.tags}"` | Runs any tag expression |
| `make report` | Builds `reports/allure-report` from the last run and opens it in the browser (Ctrl+C stops it) |
| `make clean` | Deletes `reports/` |

```bash
make regression
make report
```

Run `make report` as a separate command: when a scenario fails, `make regression report` stops before building the report.

The Allure report shows each scenario with its steps and tags. A failed step also has the full request and response attached, pretty-printed, with the password, the `Authorization` token and cookies masked. The JUnit XML (one file per feature in `reports/junit/`) is the format CI servers read.

The same reports without make. behave pairs each `-o` with the `-f` in the same position, so put `allure` first:

```bash
behave -f allure -o reports/allure-results -f pretty --junit
```

### Continuous Integration

[.github/workflows/api-tests.yml](.github/workflows/api-tests.yml) runs on every pull request, on each push to `main`, every night at 02:30 UTC, and on demand. It is a single job, so only one set of scenarios at a time counts against DummyJSON's rate limit:

1. Install the pinned requirements on Python 3.11 (pip downloads are cached)
2. `make unit`
3. Check that the DummyJSON credentials are set
4. `make smoke`, a quick check that both APIs answer
5. `make tagged` with `@regression and {config.tags}`, unless a manual run picks other tags
6. Even when a step failed: write a summary table to the run page (scenarios per feature, and each failure with its file and line), and upload the `junit` and `allure-results` folders as artifacts, kept for 14 days

The nightly run catches changes in the public APIs between commits. To start a run by hand, open **Actions → API tests → Run workflow** and enter a tag expression, e.g. `@known_issue` to see whether the documented bugs are still there. A new push to a pull request cancels its run that is still in progress.

The auth scenarios need two repository secrets, set under **Settings → Secrets and variables → Actions**: `DUMMYJSON_USERNAME` and `DUMMYJSON_PASSWORD`. The public demo account from `.env.example` works. GitHub hides secret values in the logs.

To browse a CI run in Allure, download its `allure-results` artifact, unzip it and run `allure serve <folder>`.

A second workflow, [.github/workflows/lint.yml](.github/workflows/lint.yml), runs `pre-commit run --all-files` on every pull request and push to `main`. It makes no API calls, so it runs next to the API tests; the hook environments are cached between runs.

## What Gets Tested

**Reading posts** ([posts_read.feature](features/jsonplaceholder/posts_read.feature)) - 16 scenarios, counting each Examples row:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /posts/1` | 200, JSON content type, `id` is 1, matches the `post` schema |
| Positive | `GET /posts` | 100 posts, each matching the `post` schema |
| Positive | `GET /posts?userId=1`, `5`, `10` | 10 posts, all from that user |
| Positive | `GET /posts/1/comments` | 5 comments, all for post 1, every email contains `@`, each matches the `comment` schema |
| Positive | `/posts/1/comments` vs `/comments?postId=1` | Both routes return the same body |
| Negative | `GET /posts/0`, `101`, `9999`, `abc` | 404 with an empty object |
| Edge | `GET /posts/1`, `/posts/100` | First and last ids return 200 |
| Edge | `GET /posts?userId=999` | 200 with an empty list, not a 404 |
| Edge | `GET /posts?_page=2&_limit=5` | Ids 6-10 and header `X-Total-Count: 100` |
| Edge | `GET /posts?_page=999&_limit=10` | 200 with an empty list |

**Writing posts** ([posts_write.feature](features/jsonplaceholder/posts_write.feature)) - 8 scenarios. JSONPlaceholder fakes writes, so the checks cover what the response says, not what is stored:

| Type | Request | Checks |
|---|---|---|
| Positive | `POST /posts` | 201, echoes every field sent, new `id` is an integer above 100 |
| Positive | `PUT /posts/1` with every field | 200, echoes every field sent |
| Positive | `GET /posts/1`, then `PATCH /posts/1` with a new title | 200, title changed, `id`, `userId`, `body` unchanged from the GET |
| Positive | `DELETE /posts/1` | 200 with an empty object |
| Edge | `POST /posts` with title `Café ☕ 日本語` | Text sent as raw UTF-8 comes back unchanged |
| Edge | `PUT /posts/1` with only a title | `body` and `userId` are gone (PUT replaces, PATCH merges) |
| Known issue | `PUT` / `PATCH /posts/9999` | Should be 404. Actual: PUT returns 500 with an HTML stack trace, PATCH returns 200 |

**Reading users** ([users.feature](features/jsonplaceholder/users.feature)) - 3 scenarios:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /users/1` | `address.city`, `address.geo.lat` (`"-37.3159"`), `address.geo.lng`; matches the `user` schema |
| Positive | `GET /users` | 10 users, each matching the `user` schema |
| Negative | `GET /users/11` | 404 with an empty object |

**Products** ([products.feature](features/dummyjson/products.feature)) - 23 scenarios. DummyJSON fakes writes too, so add, update and delete are checked by their responses:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /products/1` | 200, `id` is 1, matches the `product` schema (which also requires `price` above 0) |
| Positive | `GET /products?limit=5&skip=10` | Ids 11-15; `skip` 10, `limit` 5, `total` above 0 |
| Positive | `GET /products?sortBy=price&order=asc` / `desc` | Prices in that order (ties allowed) |
| Positive | `GET /products?select=title,price` | Every product has exactly `id`, `title`, `price` |
| Positive | `GET /products/search?q=phone` | Every result mentions "phone" in its title or description, ignoring case |
| Positive | `GET /products/category/smartphones` | Every product is in `smartphones` |
| Positive | `POST /products/add` | 201, echoes the fields sent, `id` is an integer |
| Positive | `GET`, then `PUT /products/1` with a new price | Price changed; `id`, `title`, `category` unchanged |
| Positive | `DELETE /products/1` | `isDeleted` is true, `deletedOn` is an ISO 8601 timestamp |
| Negative | `GET /products/0`, `abc`, and one past the last id | 404, `Product with id '<id>' not found`; the last id comes from `total` at runtime |
| Negative | `GET /products?limit=-1` / `abc` | 400, `Invalid 'limit' - should be a positive number` |
| Negative | `GET /products?sortBy=price&order=sideways` | 400, `Invalid 'order' - should be either 'asc' or 'desc'` |
| Negative | `PUT` / `DELETE /products/99999` | 404 with the not-found message |
| Edge | `GET /products?limit=0` | Returns every product: `limit` equals `total` and the list has `total` items |
| Edge | `GET /products?skip=1000` | 200 with an empty `products` list and `limit` 0 |
| Edge | `search?q=PHONE` vs `search?q=phone` | Identical responses |
| Edge | `search?q=zzqqxx` | Empty `products`, `total` 0 |
| Edge | `GET /products/category/flying-cars` | 200 with an empty list, not a 404 |

**Authentication** ([auth.feature](features/dummyjson/auth.feature)) - 19 scenarios, 3 of them known issues. They log in as the account in `DUMMYJSON_USERNAME` / `DUMMYJSON_PASSWORD`:

| Type | Request | Checks |
|---|---|---|
| Positive | `POST /auth/login` | 200; `accessToken` and `refreshToken` are JWTs; `username` matches the configured user; no `password` field; matches the `auth_login` schema |
| Positive | Login with `expiresInMins` 1 / 30 | The access token's `exp - iat` is 60 / 1800 seconds |
| Positive | `GET /auth/me` with the bearer token | 200, same `id` as the login |
| Positive | `GET /auth/products/1` with the bearer token | 200 |
| Positive | `POST /auth/refresh`, then `/auth/me` with the new access token | New JWTs that work |
| Negative | Login with a wrong password, and with an unknown user | Both 400 `Invalid credentials`, so the API doesn't reveal which usernames exist |
| Negative | Login without a password, and with an empty body | 400 `Username and password required` |
| Negative | `/auth/me` and `/auth/products/1` without a token | 401 `Access Token is required` |
| Negative | `/auth/me` with `Authorization: Basic abc` | 401 `Invalid/Expired Token!` |
| Negative | `/auth/refresh` with no token / with `abc` | 401 `Refresh token required` / 403 `Invalid refresh token` |
| Edge | Login with the username in upper case | 200: usernames are case-insensitive |
| Known issue | `/auth/me` with `Bearer not.a.jwt` | Should be 401. Actual: 500 `invalid token` |
| Known issue | `/auth/me` with a tampered signature | Should be 401. Actual: 500 `invalid signature` |
| Known issue | `/auth/me` response | Must not contain `password`. Actual: it returns the password in plain text |

Each feature's `Background` picks its API client (`Given the JSONPlaceholder API is available` or `Given the DummyJSON API is available`).

**Contracts** ([schemas/](schemas)). Scenarios check response shapes against JSON Schema (Draft 2020-12), including formats such as `date-time`, `email` and `uri`:

| API | Schemas | Strictness |
|---|---|---|
| JSONPlaceholder | `post`, `comment`, `user` | No extra keys allowed: the data set never changes |
| DummyJSON | `product`, `product_list`, `auth_login`, `error` | Extra keys allowed, since the API keeps evolving; listed keys keep their types, ranges and enums |

`product_list` reuses `product.json` through `$ref`, `auth_login` states that a login must never return a password, and every DummyJSON 4xx scenario checks the `error` shape. Each schema was validated against every record the API returns (100 posts, 500 comments, 10 users, 194 products).

**Unit tests** ([tests/unit/](tests/unit)) - pytest cases for the dotted-path getter, the sort check, JWT decoding, schema loading and its error messages, settings precedence, placeholders and data tables, secret redaction, the request/response text attached to the Allure report, and the CI summary table. One test also checks that the `date-time`, `uri` and `email` formats are really enforced: `jsonschema` silently skips a format whose helper library is missing.

## Modifying Test Data

Settings live in [config/settings.py](config/settings.py). Each one is taken from the first place that sets it:

1. `behave -D NAME=value` on the command line
2. An environment variable
3. A `.env` file in the repository root
4. The default below

| Setting | Default | Used for |
|---|---|---|
| `JSONPLACEHOLDER_BASE_URL` | `https://jsonplaceholder.typicode.com` | JSONPlaceholder client |
| `DUMMYJSON_BASE_URL` | `https://dummyjson.com` | DummyJSON client |
| `REQUEST_TIMEOUT` | `10` | Seconds to wait for each request before failing |
| `DUMMYJSON_USERNAME` | none | DummyJSON login (auth scenarios) |
| `DUMMYJSON_PASSWORD` | none | DummyJSON login (auth scenarios); hidden as `***` in failure output |

The credentials have no default on purpose; CI reads them from repository secrets (see Continuous Integration). To use the public DummyJSON demo account locally, copy the template; `.env` is git-ignored:

```bash
cp .env.example .env
```

One-off overrides don't need a file:

```bash
# Give a slow network more time
behave -D REQUEST_TIMEOUT=30

# Same thing with an environment variable
REQUEST_TIMEOUT=30 behave
```

There are no separate dev or staging environments: both APIs are public, so the defaults point at the real endpoints.

Request bodies live next to the scenario that sends them, as a data table. The same step works for `POST`, `PUT` and `PATCH`:

```gherkin
When I send a POST request to "/posts" with:
  | field  | value                |
  | title  | Weekly release notes |
  | userId | 1                    |
```

Values are read as JSON when they parse, so `1` is sent as a number and `true` as a boolean; anything else, like `Weekly release notes`, is sent as a string. Wrap a value in double quotes (`"1"`) to send it as a string.

Response contracts live in `schemas/<api>/<name>.json`. The API comes from the feature's `Background`, so a scenario only names the schema:

```gherkin
Then the response should match the "product_list" schema
And every item in the "products" list should match the "product" schema
```

A schema can reuse another file in the same folder with `{"$ref": "product.json"}`.

The read scenarios keep their inputs in the feature file too. To try another id or user, add a row to the matching `Examples:` table in [posts_read.feature](features/jsonplaceholder/posts_read.feature); the `note` column says why the row is there and shows up in the scenario name.

## Troubleshooting

**Environment not found?**
```bash
conda env list  # Check if api_automation exists
```

**Import errors, e.g. `No module named 'allure'` after pulling new changes?**
```bash
conda activate api_automation
conda env update -f environment.yml --prune
```

**`make: behave: No such file or directory` (or `pytest`)?**
- The environment isn't active in that terminal. Run `conda activate api_automation` first.

**``Executable `ruff` not found`` (or `mypy`) when committing?**
- The hooks use the tools from the active environment. Run `conda activate api_automation`, or `pip install -r requirements-dev.txt` in your virtual environment, and commit again.

**A commit stops with `files were modified by this hook`?**
- A hook fixed whitespace, import order or formatting. Check the change with `git diff`, then `git add` the files and commit again.

**`ModuleNotFoundError: No module named 'config'` (or `'api'`)?**
- Run `behave` from the repository root, not from inside `features/`

**Editor says `parse` or `register_type` can't be resolved?**
- The editor is using a different Python. Point it at the `api_automation` environment (VS Code: *Python: Select Interpreter*). `parse` is installed with behave.

**`HOOK-ERROR in before_tag(tag=authenticated): RuntimeError: DummyJSON credentials are not set`?**
- Create `.env` with `cp .env.example .env`, or set `DUMMYJSON_USERNAME` and `DUMMYJSON_PASSWORD`. The other features still run without it.

**`FileNotFoundError: No schema file at .../schemas/<api>/<name>.json`?**
- The schema name in the step doesn't match a file for the API picked in the `Background`. Check the spelling, or that the right API is selected.

**A schema check fails after an API change?**
- The message lists up to five problems with their JSON paths, e.g. `$.products[3].price: -1 is less than or equal to the minimum of 0`. Decide whether the API broke its contract (keep the test failing, or record it as `@known_issue`) or the contract really changed (update the schema).

**Reading a failure**
- When a step fails, the log line above the error shows the last request and response, e.g. `LOG_ERROR:api: PUT https://jsonplaceholder.typicode.com/posts/9999 -> 500`, followed by the first 500 characters of the body.
- For the whole exchange, run through a make target and open `make report`: the failed step has `Request` and `Response` attachments with headers and the full body.

**`make: allure: No such file or directory`?**
- The Allure command-line tool isn't installed: `brew install allure` (see Prerequisites). The tests and the files in `reports/` don't need it, only the HTML report does.

**`TypeError: expected str, bytes or os.PathLike object, not NoneType` with `-f allure`?**
- The Allure formatter needs a results folder: `-f allure -o reports/allure-results`.

**The Allure report is empty, or `reports/allure-report/index.html` won't load when opened directly?**
- `make report` reads the last make run, so run `make smoke` or `make regression` first. The HTML report has to be served by a web server, so open it with `make report` or `allure open reports/allure-report`, not by double-clicking the file.

**CI fails at "Check DummyJSON credentials"?**
- The repository secrets `DUMMYJSON_USERNAME` and `DUMMYJSON_PASSWORD` are missing; add them as described in Continuous Integration. Pull requests from forks never receive secrets, so their runs stop here too.

**The CI summary shows scenarios as "not run"?**
- A hook stopped them before they started, usually the `@authenticated` login (for example, a wrong password in the secrets). The `HOOK-ERROR` line in the job log has the reason.

**The nightly run stopped?**
- GitHub disables scheduled workflows in a public repository after 60 days without activity. Enable it again on the **Actions** tab (API tests → Enable workflow). Scheduled runs can also start late when GitHub Actions is busy.

**Dependency install fails on an older environment?**
- `requests` 2.34 needs Python 3.10+. Recreate the environment:
```bash
conda env remove -n api_automation
conda env create -f environment.yml
```

**Tests failing?**
- Verify internet connection
- Check if https://jsonplaceholder.typicode.com/ is accessible in your browser
- `ConnectTimeout` / `ReadTimeout` errors mean the API didn't answer within `REQUEST_TIMEOUT`; raise it on a slow network, e.g. `behave -D REQUEST_TIMEOUT=30`

**`HOOK-ERROR in before_all: ValueError: REQUEST_TIMEOUT ...`?**
- The timeout must be a number of seconds greater than 0. Check the `-D` option, your environment variables and `.env`, in that order.

**DummyJSON scenarios start failing when re-run in a tight loop?**
- DummyJSON rate-limits clients: responses carry `x-ratelimit-limit: 100` and a reset time a few seconds ahead. A normal run stays well under it; wait a few seconds and run again.

**`behave --tags=@regression` fails on `/posts/9999`?**
- Those are `@known_issue` scenarios. Command-line tags replace the default filter, so use `behave --tags="@regression and {config.tags}"`.

**`Expected a non-empty list but got: []`?**
- "Every item in the response..." steps refuse to pass on an empty list, so a filter that matches nothing is reported instead of passing silently. Check the query string in the scenario.

## Next Steps

- Publish the Allure report, with its history, to GitHub Pages from the nightly run
- Retry idempotent requests (GET, PUT, DELETE) on 429 and 5xx responses, with backoff
- Run scenarios in parallel with behavex
- Add a response-time check that runs outside the pull request checks

## Learning Resources

- [Behave Documentation](https://behave.readthedocs.io/)
- [Behave Configuration Files](https://behave.readthedocs.io/en/latest/behave/#configuration-files)
- [Behave Tag Expressions](https://behave.readthedocs.io/en/latest/tag_expressions/)
- [Behave Gherkin: Background, Scenario Outlines, Tags](https://behave.readthedocs.io/en/latest/gherkin/)
- [Behave Step Data (tables)](https://behave.readthedocs.io/en/latest/gherkin/#step-data)
- [Behave `register_type` (custom step parameter types)](https://behave.readthedocs.io/en/latest/api/#behave.register_type)
- [MDN: PUT](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PUT) and [PATCH](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/PATCH)
- [Requests Sessions and Timeouts](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [Requests Library](https://requests.readthedocs.io/)
- [python-dotenv](https://saurabh-kumar.com/python-dotenv/)
- [Behave userdata (`-D NAME=value`)](https://behave.readthedocs.io/en/latest/new_and_noteworthy_v1.2.5/#userdata)
- [JSONPlaceholder API Guide](https://jsonplaceholder.typicode.com/guide/)
- [DummyJSON Products API](https://dummyjson.com/docs/products) and [Auth API](https://dummyjson.com/docs/auth)
- [Behave fixtures (`@fixture`, `use_fixture`)](https://behave.readthedocs.io/en/latest/fixtures/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [jsonschema: validating formats](https://python-jsonschema.readthedocs.io/en/stable/validate/#validating-formats)
- [pytest documentation](https://docs.pytest.org/en/stable/)
- [Allure Report for behave](https://allurereport.org/docs/behave/) and [installing Allure Report 2](https://allurereport.org/docs/v2/install/)
- [Behave formatters and reporters](https://behave.readthedocs.io/en/latest/appendix.formatters/) and the [`--junit` option](https://behave.readthedocs.io/en/latest/behave/#cmdoption-junit)
- [GNU make manual](https://www.gnu.org/software/make/manual/make.html)
- [Ruff](https://docs.astral.sh/ruff/): [rules](https://docs.astral.sh/ruff/rules/) and [formatter](https://docs.astral.sh/ruff/formatter/)
- [mypy `--strict`](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict) and the [type hints cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [pre-commit](https://pre-commit.com/) and [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks)
- [Ignoring commits in GitHub's blame view](https://docs.github.com/en/repositories/working-with-files/using-files/viewing-and-understanding-files#ignore-commits-in-the-blame-view)
- [GitHub Actions workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax) and [events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Using secrets in GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) and [manually running a workflow](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow)
- [Storing workflow data as artifacts](https://docs.github.com/en/actions/tutorials/store-and-share-data) and [job summaries](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands#adding-a-job-summary)
