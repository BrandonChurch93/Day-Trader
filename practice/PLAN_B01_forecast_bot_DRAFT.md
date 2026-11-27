# Plan B01: our forecasting bot for the Metaculus FutureEval bot rounds (DRAFT)

Lead agent's queue row 147. Status: built and tested offline. Not switched on. No request of any kind has gone to
metaculus.com or its API, from code or by hand. The bot cannot send one until the owner has made the bot account, the
lead sets `forecast_bot.network_allowed` to true, and `B01_START=<frozen build hash>` is written on ledger row 239.

Labels: MEASURED (we ran or read it), STATED (a page says so), INFERENCE (our reasoning), UNKNOWN (not settled).

Code: `practice/forecast_bot/` (standard library plus PyYAML, and the sandbox model SDK already used by desk E15).
Tests: `practice/test_forecast_bot.py`, offline, on made-up questions. Settings: `forecast_bot` in
`config/thresholds.yaml`. Background reading: `docs/research/207_forecasting_bot_entry_facts.md` and
`practice/PLAN_F01_forecast_scorecard_DRAFT.md`.

## Sources read

- The public API description, Metaculus/metaculus `docs/openapi.yml`, as committed at f96f08be (2026-10-17), read as an
  ordinary page from GitHub. Repo license BSD-2-Clause. Line numbers below are from that copy. MEASURED.
- The bot tournament resources page, https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/ , and the
  rules page, https://www.metaculus.com/notebooks/28751/q4-ai-forecasting-benchmark-rules/ , ordinary page reads.
- No code was copied from Metaculus/metac-bot-template (no license). The bot is written from the API description. The
  forecasting-tools library is not used.

## Endpoints and fields

Every request carries `Authorization: Token <token>`. STATED, openapi.yml lines 122-131 ("The token should be prefixed
by the string literal "Token""). All requests need it: line 19 ("All API requests require valid authentication").

- List open posts of one tournament: `GET /api/posts/?tournaments=<slug>&statuses=open&limit=&offset=`. STATED, line
  1364 (path), 1372 (`tournaments`, "Tournament slug"), 1380 (`statuses`, enum includes `open`). `with_cp` is left at
  its default, false (line 1395). Pages are followed while `next` is set, up to `max_pages`.
- Fields read from each post: `id`, `title`, `question` or `group_of_questions` (Post schema, line 416; conditional at
  494 and group at 496). From each question: `id`, `type`, `status`, `title`, `label`, `description`,
  `resolution_criteria`, `fine_print`, `options`, `unit`, `scaling`, `open_lower_bound`, `open_upper_bound`,
  `inbound_outcome_count`, `open_time`, `scheduled_close_time`, `actual_close_time`, `scheduled_resolve_time`
  (Question schema, line 623; types enum at 662; always-returned list at line 73; QuestionScaling at 762, with
  `range_min`, `range_max`, `zero_point`).
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
  95th; ISO dates for date questions). Each run becomes a curve on the question's internal axis (linear, or logarithmic
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
- Each open post seen in a pass gets exactly one outcome row in that pass: `submitted`, `already_answered`,
  `duplicate_in_pass`, `skipped:<reason>`, `no_open_question`, `no_time`, `failed_runs`, `failed_build`,
  `failed_http_<code>`, `unknown_outcome`, `guard_cannot_check`, `deferred_guard_unavailable` or
  `gave_up_after_attempts`. A failed list call writes `list_failed`. Nothing is skipped silently. MEASURED in tests.
- A question is answered once. It is skipped when our log has a `submitted` row for it or the site shows our forecast
  on it. If the site read fails, no post is sent that pass.
- Before each send a `claim` row is written. A 201 settles it. A 400 or 403 settles it as failed (nothing saved, STATED).
  A timeout or 5xx leaves it open; the next pass reads our forecasts on the site and settles it as
  `submitted_confirmed_later` or `claim_not_on_site` (then it may be tried again). No POST is ever retried blind.
- A post is tried at most `forecast_bot.max_attempts_per_post` times. No send when fewer than
  `forecast_bot.min_minutes_left` remain before close.

## Which tournament

- `forecast_bot.targets` lists tournament slugs in order. Now: `minibench` only (resources page: the "minibench" id
  always points at the active round, STATED). Second, after the lead says so: `fall-futureeval-2026` (project 33121).
  A change of targets is a change of setting, so it is a new frozen build and a new ledger key.
- `forecast_bot.testing_target` is `bot-testing-area` (32977), unscored. The `testing` command uses it and needs its
  own key, `B01_TEST=<hash>`, on the same ledger row. Testing there is allowed (resources page, STATED).

## The forecasting method, fixed before the first live question

- Research step: one call to `forecast_bot.research_model` (claude_sonnet_5_5) with the model provider's own web search,
  through the sandbox model SDK, the same path desk E15's scout uses. It is asked for dated facts and a SOURCES list,
  and no forecast. MEASURED: the SDK's web search works for claude_sonnet_5_5 and gpt_5_4 from a detached process
  (parent pid 1), on a made-up test prompt; gemini_3_flash failed with a provider timeout. Cost: 1 call per post,
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
  MEASURED: a live-model dry run on the five made-up sample posts (6 questions) made 35 calls; all 30 runs returned
  valid forms and every payload passed `bot.validate`.
- No Community Prediction, by rule: the list call never asks for it, and the packet the models see is built from a fixed
  field list (`questions.PACKET_FIELDS`) that holds no `aggregations` or `my_forecasts`. MEASURED in tests.
- Fixed in config before the first live question: models, run count, prompts (their SHA-256 is in the log header),
  clips and limits. The log header pins every setting and the source hashes; a pass refuses if any of them changed.
- Research quality risk, MEASURED: on the same made-up CPI prompt gpt_5_4 once said a figure was not published and once
  gave one. The runs are told the brief may be wrong.

## Secrets

- The token is read at request time from the environment variable `forecast_bot.token_env` (METACULUS_TOKEN). It is
  never stored on an object, written to the log, put in an error, passed on a command line or put in a prompt; the
  prompt is built only from the question packet. MEASURED in tests with a fake token.
- Errors carry only the HTTP status and path. Redirects are refused, so the token cannot follow one to another host.
  Only https to the configured host.
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
- Start, once the lead says so: set `forecast_bot.network_allowed` true and commit; write `B01_START=<that hash>` on
  ledger row 239 on local main; run `pass` once by hand, then `loop` detached. The private log is at
  `forecast_bot.private_dir` (folder 0700, file 0600), off the repo. It keeps ids, hashes of question text (not the
  text), our forecasts and outcomes.

## Rules page: design choices that carry a disqualification risk

- Human in the loop. STATED (resources page): testing on open or upcoming tournament questions and then changing the
  bot counts as a human in the loop. So: no dry run, live-model run or manual look at open tournament questions, ever.
  After start, a repair only for a crash or a rejected payload, never because of a forecast's content, each as a new
  build and ledger key. The private log should not be read for forecast content while questions are open.
- Commercial use and open code. STATED (openapi.yml line 12): "any commercial use whatsoever requires a separate
  written agreement". The rules ask bots tied to a company to publish their code. Our code is in a public repo, but the
  model calls go through the internal sandbox SDK, which is not public. The organizer may judge that not fully open, or
  this entry commercial. The lead or owner should ask the organizer before start. A public model backend option is
  possible but not built.
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
