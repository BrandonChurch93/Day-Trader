# Plan B01: our forecasting bot for the Metaculus FutureEval bot rounds (DRAFT)

Lead agent's queue row 147. Status: built and tested offline. Not switched on. No request of any kind has gone to
metaculus.com or its API, from code or by hand. The bot cannot send one until the owner has made the bot account, the
lead sets `forecast_bot.network_allowed` to true, and `B01_START=<frozen build hash>` is written on ledger row 239.

Labels: MEASURED (we ran or read it, with a test in this repo or a saved artifact named here), STATED (a page says
so; "STATED by the builder" means the builder ran it but kept no artifact in the repo), INFERENCE (our reasoning),
UNKNOWN (not settled).

Audit round 1 (lead's message on d0391a0) is folded in below: descriptions asked for, hidden text never forecast,
allowlisted child environments, token taken out of the environment, claims kept open when an id is omitted, proxy
ignored and host pinned, loop survives errors, soonest close first, a wall-clock budget per post, retries across the
whole window, and crowd numbers kept out of research.

Code: `practice/forecast_bot/` (standard library plus PyYAML, and the sandbox model SDK already used by desk E15).
Tests: `practice/test_forecast_bot.py`, offline, on made-up questions. Settings: `forecast_bot` in
`config/thresholds.yaml`. Background reading: `docs/research/207_forecasting_bot_entry_facts.md` and
`practice/PLAN_F01_forecast_scorecard_DRAFT.md`.

## Sources read

- The public API description, Metaculus/metaculus `docs/openapi.yml`, as committed at f96f08be (2026-10-17), read as an
  ordinary page from GitHub. Repo license BSD-2-Clause. Line numbers below are from that copy, which the builder
  read (STATED by the builder; the copy is not saved in the repo, and the commit above pins it).
- The bot tournament resources page, https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/ , and the
  rules page, https://www.metaculus.com/notebooks/28751/q4-ai-forecasting-benchmark-rules/ , ordinary page reads.
- No code was copied from Metaculus/metac-bot-template (no license). The bot is written from the API description. The
  forecasting-tools library is not used.

## Endpoints and fields

Every request carries `Authorization: Token <token>`. STATED, openapi.yml lines 122-131 ("The token should be prefixed
by the string literal "Token""). All requests need it: line 19 ("All API requests require valid authentication").

- List open posts of one tournament:
  `GET /api/posts/?tournaments=<slug>&statuses=open&include_descriptions=true&limit=&offset=`. STATED, line 1364
  (path), 1372 (`tournaments`, "Tournament slug"), 1380 (`statuses`, enum includes `open`), 1409
  (`include_descriptions`: "each post question will include the description, fine_print, and resolution_criteria
  fields"). `with_cp` is left at its default, false (line 1395). Pages are followed while `next` is set, up to
  `max_pages`; more pages than that is an error, not a silent cut. MEASURED in tests (query string and paging).
- Hidden text. STATED, lines 64-80: the gateway sets description, resolution_criteria and fine_print to null unless the
  question is open now (or we forecast it, or the project is accessible), and keeps the key. A question whose
  `resolution_criteria` is null (and, in a group, whose group criteria are null too) is recorded
  `not_ready:resolution_criteria_hidden` and tried again next pass. It is never forecast blind and does not use up an
  attempt. MEASURED in tests.
- Fields read from each post: `id`, `title`, `question` or `group_of_questions` (Post schema, line 416; conditional at
  494 and group at 496). From each question: `id`, `type`, `status`, `title`, `label`, `description`,
  `resolution_criteria`, `fine_print`, `options`, `unit`, `scaling`, `open_lower_bound`, `open_upper_bound`,
  `inbound_outcome_count`, `open_time`, `scheduled_close_time`, `actual_close_time`, `scheduled_resolve_time`
  (Question schema, line 623; types enum at 662; always-returned list at line 73; QuestionScaling at 762, with
  `range_min`, `range_max`, `zero_point`). The bounds are read from the question, or from `scaling` when the top-level
  key is missing or null (QuestionScaling also has them, line 784). MEASURED in tests.
- Our own forecasts, the duplicate guard's site check: `GET /api/questions/bulk-forecast-read/?question_ids=1&question_ids=2`.
  STATED, line 2559. "Questions the acting user can't view are left out" and "Questions with no forecasts are included
  with an empty `forecasts` list". The bot treats a missing id as "cannot check" and does not send for it.
- Submit forecast and comment together: `POST /api/questions/bulk-forecast-comment/` with `forecasts` and
  `comments`. STATED, line 2491: "a single atomic transaction: if any forecast or comment is invalid, nothing is saved".
  Each comment has `on_post`, `text`, `is_private` ("Must be true; only private comments are accepted") and
  `included_forecast` ("Attach the acting user's latest forecast on the post's question"). Responses: 201 saved, 400
  "Nothing was saved", 403 bad `acting_user`. `acting_user` is not sent; the token is the bot account's own.
- Not used: `POST /api/questions/forecast/` (line 2325) and `POST /api/comments/create/` (line 2692). The bulk call does
  both in one atomic step, so a forecast can never be saved without its comment.

## Question types and how each is sent

All MEASURED in the tests on made-up questions; the field names are STATED in the Forecast schemas (line 849 on).

- Binary: `{"question": id, "probability_yes": p}`. Median of the runs, clipped to `forecast_bot.binary_clip`.
- Multiple choice: `{"question": id, "probability_yes_per_category": {option: p}}`, every option exactly once, summing
  to 1 (MultipleChoiceForecast, line 948, "Sum of values must equal 1.0"). Mean of the runs per option, each raised to
  at least `forecast_bot.mc_floor`, then normalized.
- Numeric, discrete and date: `{"question": id, "continuous_cdf": [...]}`. Each run gives seven percentiles (5th to
  95th; ISO dates for date questions). A run with a value the axis cannot hold (at or below `zero_point` on a log
  scale) is dropped as `bad_reply:percentile`; the other runs go on. If every run puts its belief beyond a closed
  bound, there is no honest CDF to send: the post is recorded `no_valid_distribution` and tried again. Each run becomes a curve on the question's internal axis (linear, or logarithmic
  when `zero_point` is set), the curves are averaged point by point, and the average is made valid. The rules, all
  STATED in ContinuousForecast (line 876) and the CDF guide (lines 291-303):
  - `inbound_outcome_count + 1` points: 201 for the usual 200, 11 for a discrete question with 10 outcomes;
  - strictly increasing by at least 0.01 / inbound_outcome_count per step (line 295, line 902);
  - no step above 0.2 * 200 / inbound_outcome_count (line 300), and never above 0.59 (line 905);
  - closed lower bound: `cdf[0]` exactly 0.0; open: at least 0.001 (lines 891-895);
  - closed upper bound: `cdf[-1]` exactly 1.0; open: at most 0.999 (lines 897-900).
  `practice/forecast_bot/cdf.py` is our own code from those rules. A payload that fails `cdf.check` is never sent.
- Group of questions: one task per open subquestion, all in one bulk request with one comment on the post. Already
  answered subquestions are left out. INFERENCE: `included_forecast` attaches the forecast of "the post's question",
  which for a group is UNKNOWN; the comment text shows every subquestion's forecast anyway.
- Conditional posts: skipped and recorded as `skipped:conditional_not_supported`. INFERENCE: the bot rounds have not
  used them; see UNKNOWN.

## The comment

- One private comment per post, sent in the same atomic request as the forecast. STATED (resources page): private
  comments are required and are made public after close.
- It shows the forecast in words (rules page: a comment that displays the forecast is needed), the method, each run's
  model, status and short reasons, and the research step's https sources. Cut to `forecast_bot.comment_max_chars`.
- It never holds a token: `bot.validate` refuses a payload that looks like one.

## Polling and the duplicate guard

- Questions open for about 3 hours at random hours (resources page, STATED). The loop runs a pass every
  `forecast_bot.poll_minutes` (15), on the quarter hour, so each question gets about 12 chances. INFERENCE: one pass is
  1 list call per target and page, 1 read call and 1 submit per new post; well under any polite rate. No polling limit
  is stated; see UNKNOWN.
- One pass at a time: a file lock in the private folder.
- Posts are handled soonest close first (`actual_close_time`, else `scheduled_close_time`), and the clock is read fresh
  before each post, so a long pass cannot send after the time check has gone stale.
- Each open post seen in a pass gets exactly one outcome row in that pass: `submitted`, `already_answered`,
  `duplicate_in_pass`, `bad_post_id` (no integer id), `skipped:<reason>`, `not_ready:<reason>`, `no_open_question`,
  `no_time`, `failed_runs`, `no_valid_distribution`, `failed_budget`, `failed_build`, `failed_http_<code>`,
  `unknown_outcome`, `claim_still_open`, `guard_cannot_check`, `deferred_guard_unavailable` or
  `gave_up_after_attempts`. A failed list call writes `list_failed`. Nothing is skipped silently. MEASURED in tests.
- A question is answered once. It is skipped when our log has a `submitted` row for it or the site shows our forecast
  on it. If the site read fails, no post is sent that pass.
- Before each send a `claim` row is written. A 201 settles it. A 400 or 403 settles it as failed (nothing saved, STATED).
  A timeout, 5xx or crash leaves it open. The next pass reads our forecasts on the site and writes a `settle` row:
  `submitted_confirmed_later` when every id shows a forecast; `claim_not_on_site` only when every id is reported with
  none (then the post may be tried again); `claim_cannot_check` when an id is omitted, and then the claim stays open
  and the post is recorded `claim_still_open` and not sent. No POST is ever retried blind. MEASURED in tests,
  including a crash after the site saved the forecast but before the outcome row.
- Retries last the whole window: `forecast_bot.max_attempts_per_post` (12) times `forecast_bot.poll_minutes` (15) is
  180 minutes, and `settings.required` refuses a smaller product. The real stop is `forecast_bot.min_minutes_left`
  before close. Worst case for one post that keeps failing: 12 tries of 6 calls, 72 model calls.

## Time budget per post

- One post's research and runs run under one hard wall-clock limit, `forecast_bot.question_budget_s` (480 s). Research
  comes first (the runs need its brief); then every run for every open subquestion goes at the same time. Over the
  limit, the post is recorded `failed_budget` and tried again next pass. MEASURED in tests.
- Each call has its own limit as well: `forecast_bot.research_timeout_s` (240 s) and `forecast_bot.run_timeout_s`
  (180 s). So one post needs at most 240 + 180 = 420 s, and never more than 480 s.
- Worst case, arithmetic: ten posts open at once and every one hits the budget: 10 x 480 s = 4800 s = 80 minutes for
  the pass, plus seconds of HTTP. The last post (soonest close first) still starts within 80 minutes and finishes
  within 88 of the pass start, inside a 180-minute window, leaving room for the 15-minute wait before the pass and
  one retry. Posts are done one at a time on purpose (at most 6 model calls in flight, within our limit of heavy
  processes). INFERENCE: the measured dry run below is far below this.

## Which tournament

- `forecast_bot.targets` lists tournament slugs in order. Now: `minibench` only (resources page: the "minibench" id
  always points at the active round, STATED). Second, after the lead says so: `fall-futureeval-2026` (project 33121).
  A change of targets is a change of setting, so it is a new frozen build and a new ledger key.
- `forecast_bot.testing_target` is `bot-testing-area` (32977), unscored. The `testing` command uses it and needs its
  own key, `B01_TEST=<hash>`, on the same ledger row. Testing there is allowed (resources page, STATED).

## The forecasting method, fixed before the first live question

- Research step: one call to `forecast_bot.research_model` (claude_sonnet_5_5) with the model provider's own web search,
  through the sandbox model SDK, the same path desk E15's scout uses. It is asked for dated facts and a SOURCES list,
  and no forecast. It is told not to open, cite or report anything from metaculus.com, and no crowd forecast,
  prediction market price or betting odds from any site. Source URLs on those sites are dropped from the comment
  (`models.BARRED_HOSTS`). INFERENCE: the prompt cannot stop a model from mentioning such a number it found; it only
  makes it rare, and the comment would show it.
- STATED by the builder (probe scripts and raw output kept off the repo in the builder's scratch folder, not saved as
  artifacts): the SDK's web search worked for claude_sonnet_5_5 and gpt_5_4 from a detached process (parent pid 1) on
  a made-up test prompt; gemini_3_flash failed with a provider timeout. Cost: 1 call per post,
  plus the provider's own search calls inside it (UNKNOWN count; the SDK reports them as server tool usage).
- AskNews is not built in this version: `forecast_bot.asknews_enabled` is false and `settings.required` refuses true.
  It needs the owner's signup (STATED: 1k calls a month, 4k per tournament). Adding it later is a new build.
- Runs: `forecast_bot.runs` lists five independent runs: claude_sonnet_5_5 three times and gpt_5_4 twice. Each gets the
  same packet and brief, at the same time, and returns a fixed JSON form with reasons. A run that errors, times out, is
  cut off or breaks the form is left out. At least `forecast_bot.min_valid_runs` (3) must be valid, else the post is
  recorded `failed_runs` and tried again next pass.
- Aggregate: median for binary; mean per option for multiple choice; the average of the runs' distributions for numeric,
  discrete and date. Clipping away from 0 and 1: `forecast_bot.binary_clip`, `forecast_bot.mc_floor`, and the CDF's
  uniform share `forecast_bot.cdf_uniform_mix` and open-bound share `forecast_bot.cdf_open_bound_mass`.
- Calls per question: 1 research + 5 runs = 6 model calls. A group with k open subquestions: 1 + 5k.
  MEASURED in tests with the fake model: 5 research and 30 run calls for the five sample posts (6 questions).
- MEASURED, live models on made-up questions only: `python3 -m forecast_bot.bot dry-run --live-models` (code in
  `practice/forecast_bot/bot.py`, `dry_run` and `save_summary`) on the five sample posts (6 questions), prompt SHA-256
  585196e0...fa194: 5 research and 30 run calls; research ok 5 of 5; runs ok 18 of 18 claude_sonnet_5_5 and 12 of 12
  gpt_5_4; 5 payloads built and validated; 62.8 s in all. Counts-only summary (no model or question text) saved at
  `/home/user/workspace/rig/data/forecast_bot_dry_runs/live_dry_2026-11-27T173834Z.json` (off the repo, 0600).
- No Community Prediction, by rule: the list call never asks for it, and the packet the models see is built from a fixed
  field list (`questions.PACKET_FIELDS`) that holds no `aggregations` or `my_forecasts`. MEASURED in tests.
- Fixed in config before the first live question: models, run count, prompts (their SHA-256 is in the log header),
  clips and limits. The log header pins every setting and the source hashes; a pass refuses if any of them changed.
- Research quality risk, STATED by the builder (no artifact kept): on the same made-up CPI prompt gpt_5_4 once said a
  figure was not published and once gave one. The runs are told the brief may be wrong.

## Crowd numbers and the rules

- STATED, rules page: "if a community prediction (CP) is available on a question, bots are not allowed to blindly copy
  this prediction as their forecast (either programmatically or via asking an LLM to copy it without notable
  independent reasoning) in a way that consistently results in a prediction close to the CP."
- STATED, resources page: "A bot may use any resources that are generally available to human forecasters. This
  includes using publicly available forecasts on questions found on other platforms or on Metaculus itself."
- So the rules do not bar market prices or other crowds. This version keeps them out anyway, so the result measures
  our agent: the CP is never requested or shown, and research is told to leave out crowd and market numbers.

## Secrets

- The token comes from the environment variable `forecast_bot.token_env` (METACULUS_TOKEN). The first time the client
  needs it, it is taken out of the process environment (so no child process can inherit it) and held only inside
  `metaculus.py`. It is never stored on the client object, written to the log, put in an error, passed on a command
  line or put in a prompt; the prompt is built only from the question packet. MEASURED in tests with a fake token.
- Order in an armed pass: git checks first, then the client takes the token, then model calls. So the token is out of
  the environment before any model call.
- Child processes: the only one the bot starts is git (`settings.literal_git`), with an environment built from an
  allowlist (PATH, HOME, LANG, LC_ALL, TZ) plus the GIT_* overrides. MEASURED in tests.
- The model SDK: the installed `pplx.python.sdks.llm_api` package has no subprocess, spawn or fork call in its source
  (searched by the builder), and one run call plus one research call with web search started no process when every
  Python-level spawn function was hooked. STATED by the builder (no artifact kept). It reads only its own variables
  (address, key, metrics names).
- Payload check: `bot.validate` gets the client's own `holds_token` check in live passes, so a payload holding the token
  or anything shaped like a token header is refused (`failed_build`) without the token leaving the client module.
  MEASURED in tests.
- Errors carry only the HTTP status (or the error type) and path, raised without the original exception attached.
  Proxies from the environment are ignored (HTTPS_PROXY cannot reroute the token), redirects are refused, and
  `api_base` must be exactly https://www.metaculus.com: no userinfo, port, path, query or fragment, checked both in
  `settings.required` and by the client. MEASURED in tests.
- Where the value comes from. STATED: the practice desk's keys are GitHub Actions repo secrets passed in as environment
  variables (`.github/workflows/practice-trader.yml`). The model SDK runs only in this sandbox, so the bot loop must run
  here, not in GitHub Actions. INFERENCE: the owner adds the token as an environment-type credential in the Perplexity
  credential vault, named METACULUS_TOKEN, which the platform sets in every shell; never in chat. UNKNOWN whether that
  reaches a long detached loop; see below.

## Start, selfcheck and dry run

- `python3 -m forecast_bot.bot selfcheck` (from `practice/`): with sockets blocked, shows that the start path refuses
  (network not allowed; with it allowed, the build or ledger key check refuses), that no client is built unarmed or
  without a token, and that a wrong ledger key refuses. Exit 0 only if every path refused and no connection was tried.
  MEASURED.
- `python3 -m forecast_bot.bot dry-run` prints what it would submit for the made-up sample posts with a fake model.
  `--live-models` uses real model calls on the same made-up posts. It never builds a Metaculus client.
- The loop: a changed build or setting stops it (that would be a new attempt). Anything else (no token, a refused
  client, an HTTP failure, a crash inside a pass) is written to the private log as a `loop` row and the loop goes on
  to the next pass. MEASURED in tests.
- Start, once the lead says so: set `forecast_bot.network_allowed` true and commit; write `B01_START=<that hash>` on
  ledger row 239 on local main; run `pass` once by hand, then `loop` detached. The private log is at
  `forecast_bot.private_dir` (folder 0700, file 0600), off the repo. It keeps ids, hashes of question text (not the
  text), our forecasts and outcomes.

## Rules page: design choices that carry a disqualification risk

- Human in the loop. STATED (resources page): testing on open or upcoming tournament questions and then changing the
  bot counts as a human in the loop. So: no dry run, live-model run or manual look at open tournament questions, ever.
  After start, a repair only for a crash or a rejected payload, never because of a forecast's content, each as a new
  build and ledger key. The private log should not be read for forecast content while questions are open.
- Commercial status and prizes. STATED (resources page): a commercial bot is "any bot that is built or operated on
  behalf of a for-profit entity that has three or more founders/employees/contractors", including "any bots built using
  company resources, and any bot built by someone who works at an organization that runs a commercial bot".
  Commercial bots compete on the same questions; "Closed-source commercial bots are not eligible for prizes";
  "Commercial participants that fully open-source their bot's code by the end of the season can still earn prize
  money"; "Commercial bots are not eligible for LLM credits". INFERENCE: this bot uses company resources (the sandbox
  model SDK), so it is commercial. Our code is public, but the model calls go through an SDK that is not, so the
  organizer may judge it not fully open-source: a prize risk, not an entry risk. A public model backend would settle
  it; not built.
- API terms. STATED (openapi.yml line 12): "any commercial use whatsoever requires a separate written agreement".
  INFERENCE: a commercial bot's use of the API may count. The owner should ask the organizer before start.
- Storing content: the terms bar storing a significant portion of the site's content. The log keeps hashes only.
- One bot per person (rules page): one account only, used for MiniBench and the seasonal tournament.
- No copying of the Community Prediction: never read (above).

## UNKNOWN, and what settles each once we have an account

- Whether `tournaments=minibench` resolves the alias in the posts filter, or needs the numeric id or round slug.
  Settles with: one `GET /api/posts/?tournaments=minibench&statuses=open` and one on the testing area.
- Request rate limits for the bot tier (the description mentions throttling, line 16, without numbers). Settles with:
  the organizer, or response headers on the first passes.
- The comment length limit. Settles with: a long private comment in the testing area.
- What `included_forecast` attaches on a group post. Settles with: one group question in the testing area.
- Error body formats for 400 on the bulk call, and whether a closed question gives 400 (the bulk call lists no 405).
  Settles with: the testing area.
- Whether discrete, date or conditional questions appear in MiniBench. Settles with: a closed round's question list.
- The next MiniBench round's start date. Settles with: the resources page or the organizer.
- Whether a vault environment credential reaches a detached loop for days, across sandbox restarts. Settles with: a
  short detached test that checks only that the variable is set, without printing it.
- Whether the organizer accepts public code that calls an internal model SDK, and whether this entry counts as
  commercial. Settles with: asking the organizer.
- The bot's user id, which would allow the posts filter `forecaster_id`. Not needed: the bulk read covers the guard.
- How many provider search calls a research step makes. Settles with: the SDK usage record on the first passes.
