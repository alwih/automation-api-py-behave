# Python API Automation Testing

A simple, beginner-friendly API automation project using **Behave (BDD)** and **requests**, with **miniconda** for package management.

It tests two public APIs with positive, negative and edge-case scenarios: posts and users on [JSONPlaceholder](https://jsonplaceholder.typicode.com/), and the product catalogue and JWT authentication on [DummyJSON](https://dummyjson.com/docs) (lookup, pagination, sorting, search, simulated writes, login, protected routes, token refresh). Known API bugs, including three security issues, are recorded as scenarios that are skipped by default.

## Project Structure

```
automation_py_api/
├── api/
│   ├── client.py                  # ApiClient + cookie-free session: base URL, timeout, headers, UTF-8 JSON
│   ├── assertions.py              # Response checks with dotted-path field access
│   ├── auth.py                    # DummyJSON credentials and login
│   ├── tokens.py                  # JWT decoding (no signature check) and tampering for negative tests
│   ├── step_data.py               # "{name}" placeholders and data-table bodies
│   └── redaction.py               # Hides the configured password in failure output
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
│   ├── environment.py             # Hooks: settings, one client per API, @authenticated login, failure log
│   └── steps/
│       ├── api_steps.py           # Request and response steps (thin wrappers over api/)
│       └── auth_steps.py          # Login, token and JWT steps
├── .env.example                   # Template for a local .env (copy and edit)
├── behave.ini                     # Behave defaults (paths, format, default tag filter)
├── environment.yml                # Conda environment (Python 3.11 + requirements)
├── requirements.txt               # Python dependencies (pinned)
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

# Create the 'api_automation' environment (Python 3.11 + requirements.txt)
conda env create -f environment.yml

# Activate the environment
conda activate api_automation
```

### 3. Install Dependencies

`environment.yml` already installs everything in `requirements.txt`. When the pinned versions change, update the existing environment instead of recreating it:

```bash
conda env update -f environment.yml --prune
```

Not using conda? Any Python 3.10+ virtual environment works:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then create your local settings file. The DummyJSON login scenarios need the credentials in it:

```bash
cp .env.example .env
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

## What Gets Tested

**Reading posts** ([posts_read.feature](features/jsonplaceholder/posts_read.feature)) - 16 scenarios, counting each Examples row:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /posts/1` | 200, JSON content type, `id` is 1, `userId` is an integer, `title` and `body` are non-empty strings |
| Positive | `GET /posts` | 100 posts, each with `userId`, `id`, `title`, `body` |
| Positive | `GET /posts?userId=1`, `5`, `10` | 10 posts, all from that user |
| Positive | `GET /posts/1/comments` | 5 comments, all for post 1, every email contains `@` |
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
| Positive | `GET /users/1` | `address.city`, `address.geo.lat` (`"-37.3159"`), `address.geo.lng`, non-empty `company.name` |
| Positive | `GET /users` | 10 users, each with `address.geo.lat`, `address.geo.lng`, `company.name` |
| Negative | `GET /users/11` | 404 with an empty object |

**Products** ([products.feature](features/dummyjson/products.feature)) - 23 scenarios. DummyJSON fakes writes too, so add, update and delete are checked by their responses:

| Type | Request | Checks |
|---|---|---|
| Positive | `GET /products/1` | 200, has `id`, `title`, `price`, `category`, `stock`, `rating`; `price` above 0 |
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
| Positive | `POST /auth/login` | 200; `accessToken` and `refreshToken` are JWTs; `username` matches the configured user; `id` is an integer; no `password` field |
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

The credentials have no default on purpose. To use the public DummyJSON demo account, copy the template; `.env` is git-ignored:

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

The read scenarios keep their inputs in the feature file too. To try another id or user, add a row to the matching `Examples:` table in [posts_read.feature](features/jsonplaceholder/posts_read.feature); the `note` column says why the row is there and shows up in the scenario name.

## Troubleshooting

**Environment not found?**
```bash
conda env list  # Check if api_automation exists
```

**Import errors?**
```bash
conda activate api_automation
pip install -r requirements.txt --force-reinstall
```

**`ModuleNotFoundError: No module named 'config'` (or `'api'`)?**
- Run `behave` from the repository root, not from inside `features/`

**Editor says `parse` or `register_type` can't be resolved?**
- The editor is using a different Python. Point it at the `api_automation` environment (VS Code: *Python: Select Interpreter*). `parse` is installed with behave.

**`HOOK-ERROR in before_tag(tag=authenticated): RuntimeError: DummyJSON credentials are not set`?**
- Create `.env` with `cp .env.example .env`, or set `DUMMYJSON_USERNAME` and `DUMMYJSON_PASSWORD`. The other features still run without it.

**Reading a failure**
- When a step fails, the log line above the error shows the last request and response, e.g. `LOG_ERROR:api: PUT https://jsonplaceholder.typicode.com/posts/9999 -> 500`, followed by the first 500 characters of the body.

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

- Add JSON Schema contract checks and pytest unit tests for helpers
- Add Allure/JUnit reporting and a GitHub Actions pipeline

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
