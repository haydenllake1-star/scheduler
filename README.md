# Job Scheduler (in progress)

A small job scheduler built from scratch in Python to learn how systems like Celery, Sidekiq, and Airflow work under the hood — no framework, no library doing the hard parts for me.

## What it does right now

- Jobs are submitted by name and stored in a SQLite database (`jobs.db`), so the queue survives a restart or crash instead of disappearing when the program stops.
- A worker picks up all `pending` jobs and runs them **concurrently** using Python threads, instead of one at a time.
- Each job's status (`pending` → `done`) is tracked in the database as it completes.

## Why I built it this way

I started with the simplest possible version — an in-memory list acting as a queue, with one worker running jobs one at a time — and added complexity in layers, testing each piece before moving to the next:

1. **v0:** in-memory queue, single-threaded worker.
2. **v1:** concurrent execution using `threading`, so multiple jobs run at the same time instead of blocking each other.
3. **v2:** persistence — jobs are stored in SQLite instead of a Python list, so the queue survives a restart.

## Bugs I hit and fixed (and what they taught me)

- **Threads sharing one SQLite connection/cursor:** SQLite restricts objects created in one thread from being used safely in another. Fixed by giving each thread its own connection instead of sharing a global one.
- **`database is locked`:** SQLite only allows one writer at a time. Two threads finishing at nearly the same moment collided trying to write at once.
- **The real root cause turned out to be simpler than it looked:** my main connection was holding an uncommitted write transaction open for the entire program because I'd forgotten a `conn.commit()` after an insert — which silently blocked every other connection's writes. This is a good reminder that concurrency bugs aren't always about the concurrency code itself; sometimes the real bug is upstream and just *surfaces* as a threading problem.

## Known limitations (what I'd fix in a "real" version)

- Everything runs on a single machine — a production job scheduler would distribute workers across multiple machines communicating over a network, not just threads on one process.
- SQLite is a good fit for a single-machine project like this, but a multi-machine system would need something like Redis or Postgres that many servers can talk to at once.
- No retry logic yet — if a job fails partway through, it's currently just left as `pending` forever rather than being retried or marked `failed`.
- No handling yet for a job whose name isn't in `available_jobs` — it would currently raise a `KeyError` instead of failing gracefully.

## What's next

- Add error handling so a failed job gets marked `failed` instead of silently crashing its thread.
- Add retries with backoff for failed jobs.
- Explore running workers as separate processes (or containers) talking to a shared queue over the network, instead of threads on one machine.

## Running it

\```
git clone https://github.com/haydenllake1-star/scheduler.git
cd scheduler
python scheduler.py
\```
