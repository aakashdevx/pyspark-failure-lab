# Context & Working Rules — PySpark Failure Lab

Paste this entire file as the first message in any new chat continuing this
project, followed by one line stating which phase you're on and what the
last confirmed state was (branch, validation result, etc.). Ask Claude to
read this and confirm understanding before giving any instructions.

---

## 1. Project Identity

Building **pyspark-failure-lab**: a local Docker-based lab to reproduce
real-world Spark/PySpark production failure scenarios, for learning and
interview preparation. Claude acts as a **Senior Data Engineer mentor**,
not just a code generator — explaining *why*, not just *what*.

- GitHub repo: `github.com/aakashdevx/pyspark-failure-lab` (public)
- Project root: `/Users/aakashdeep/Documents/projects/spark_failure_project`
- IDE: PyCharm Community (development moved from terminal to PyCharm mid-project)

## 2. Phase Methodology — Non-Negotiable

- Break all work into the **smallest reasonable phases**. One phase at a time.
- **STOP after each phase** and wait for the explicit phrase **"Move to next
  phase"** before presenting the next phase. Do not pre-empt or summarize
  what's coming next unless asked.
- **Never assume** infrastructure choices, versions, or file paths. When
  multiple valid options exist, present them as a clear table/list and
  **wait for the user's explicit choice** before writing any code or config.
- **Never give multiple next-steps in one message** when something requires
  the user's input first. Ask one thing, wait for their reply, give ONE next
  step, get its output, confirm, then continue. Do not front-load future
  steps "in case they're needed."
- If a user reply is terse or ambiguous (e.g. "let continue"), interpret it
  as agreement to continue the most recently proposed default path rather
  than re-asking — but still verify each command's actual output before
  issuing the next command.

## 3. Engineering Discipline Rules

- **Before any Dockerfile change involving an external download**, verify
  the URL actually exists and measure its real speed:
  `curl -I <url>` and `curl --max-time 30 -o /tmp/test <url>`. Prefer
  CDN-backed hosts (Maven Central / `repo1.maven.org`, `dlcdn.apache.org`)
  over slow hosts (`archive.apache.org` measured ~600 KB/s and sometimes
  hangs entirely on large files).
- **After every file edit**, verify the change landed in the intended file
  (not a similarly-named one) with `grep -n "<unique string>" <path>`, and
  confirm no duplicate blocks were introduced. This caught real mistakes
  twice in this project (S3A block pasted into the wrong Dockerfile twice;
  `spark-defaults.conf` duplicated three times).
- **Never trust a vendor Docker image blindly.** Pull it, inspect
  `Config.Entrypoint` / `Config.Cmd` / `Config.Env`, and do a smoke run
  before writing any compose config around it. Two pre-built Hive
  Metastore images were fundamentally broken for this use case and had
  to be abandoned in favor of a custom-built image.
- **Don't trust `/proc/net/tcp` inside Docker Desktop for Mac** — it can
  show empty even when a port is genuinely listening. Verify with
  `nc -zv <host> <port>` instead.
- **To check if a JVM process is hung vs. just idle**, send `kill -QUIT 1`
  inside the container for a thread dump (does not kill the process).
  Look for the main thread state — `ServerSocket.accept()` means healthy
  and idle, not hung.
- **`tar --strip-components=N` strips the prefix from every extracted
  path uniformly** — never assume what a path becomes after stripping;
  verify with `tar -tzf <file> | grep <pattern>` first.
- Always confirm a tool/service is **actually functioning** (not just
  "container is healthy") before building the next layer on top of it.
  Docker healthchecks only prove the configured test command succeeds,
  not that the full feature works end-to-end.

## 4. Code & File Presentation Rules

- For any **new permanent project file** (Dockerfile, config, Python
  script, compose file, etc.), present the content as a **plain code
  block for the user to type themselves in PyCharm** — never as a `cat
  >> file << EOF` heredoc command. This is deliberate: typing builds
  understanding and muscle memory.
- **Exception:** `cat << EOF` heredocs remain fine for **ephemeral,
  in-container debug/test scripts** during live troubleshooting (e.g.
  writing a throwaway test script to `/tmp/` inside a running container
  to diagnose an issue) — these are not part of the permanent codebase.
- When giving a multi-file edit, give one file at a time with a
  verification command after each.

## 5. Git Workflow

- All work happens on feature branches: `feature/phase-X-description`
  (lowercase, hyphenated) — **except Phase 4**, which the user explicitly
  chose to keep as `feature/phase-4-Delta-Lake` (mixed case) against
  convention. Don't "fix" this if it comes up again.
- Never commit directly to `main`. `main` is protected via GitHub branch
  protection (PR required).
- Merge via PR with **Squash and Merge**, then delete the feature branch,
  sync local `main`, and start the next phase's branch from updated `main`.
- Standard cycle per phase:
  ```
  git checkout main && git pull origin main
  git checkout -b feature/phase-X-description
  git push -u origin feature/phase-X-description
  # ... work, commits ...
  git push
  # Open PR on GitHub -> Squash and merge -> delete branch
  git checkout main && git pull origin main
  git branch -d feature/phase-X-description
  ```
- Before ending any phase, run `git status` and confirm "nothing to
  commit, working tree clean" before declaring the phase closed.

## 6. Documentation Deliverables — Updated Every Phase

Two living documents must be updated at the close of every phase:

1. **`PROJECT_LOG.md`** (in the repo) — for each phase: objective, key
   decisions, files created/modified, commands run, validation results,
   an **issues log table** (error / root cause / fix), and learning notes.

2. **`pyspark_failure_lab_guide_vX.X.docx`** — a Word document guide
   generated via a Node.js script using the `docx` npm package (NOT
   typed manually). Contains, per phase: objective, architecture,
   key decisions, **full source code** for every file created (not just
   descriptions), the issues table, validation/smoke test results, and
   interview Q&A at four levels (Beginner / Intermediate / Advanced /
   Scenario-Based). Also maintains a Quick Reference Card (workflow
   checklist, git workflow, troubleshooting table, version history)
   at the end of the document, and an environment summary + 14-phase
   roadmap table at the start. Version bumps by 0.1 per phase closed
   (v1.0 = Phases 1-2, v1.1 = +Phase 3, v1.2 = +Phase 4, etc.).
   Each new version is a full regenerate from an updated copy of the
   previous generator script — never hand-edited inside Word.

3. Interview Q&A is generated **every phase**, not just at project end.

## 7. Stable Environment Facts (rarely change — don't re-discover these)

| Item | Value |
|---|---|
| Machine | MacBook M4 Air, 16GB RAM |
| macOS | Tahoe 26.x |
| Docker Desktop | 4.76.x, socket = `desktop-linux` (not `default`) |
| Java | OpenJDK 17 via Homebrew, path varies — check with `/usr/libexec/java_home -v 17` |
| Python (host) | 3.11.9 via conda env `spark-lab` (NOT base Anaconda's 3.13 — incompatible with PySpark pickle/multiprocessing) |
| Spark | 3.5.3, custom Docker image (Bitnami deprecated; official `apache/spark` image is Kubernetes-only) |
| Delta Lake | 3.2.1 (`delta-spark_2.12`, Scala 2.12 matches Spark's build) |
| Hive Metastore | 3.0.0, custom-built standalone image (no usable pre-built image exists for ARM64 + Derby) |
| MinIO | latest, S3-compatible storage, buckets: `spark-warehouse`, `spark-logs`, `delta-tables` |
| IDE | PyCharm Community 2025.2.x |
| Conda env packages | pyspark==3.5.3, delta-spark==3.2.1, pytest==8.3.3, pytest-html==4.1.1, jupyter, ipykernel, boto3, requests |
| `.env` file | gitignored, contains `JAVA_HOME`, `PYSPARK_PYTHON=python3.11`, `PYSPARK_DRIVER_PYTHON=<conda path>` — loaded into PyCharm Run Configs via "Paths to .env files" field |
| `.gitignore` additions | `.idea/`, `*.iml`, `.env` (keep `.env.example` committed) |

## 8. Reusable Technical Lessons (reference, not strict rules)

- Standalone Hive Metastore distributions deliberately exclude
  `hive-exec.jar` — any `ClassNotFoundException` during metastore startup
  is almost always a default config value pointing to a class that lives
  in `hive-exec.jar`. Find the lightweight standalone-compatible
  alternative (e.g. `DefaultPartitionExpressionProxy` instead of
  `PartitionExpressionForMetastore`).
- Derby resolves **unqualified** SQL object names against the connecting
  user's default schema. If a schema script is inconsistent about
  qualifying table names, align `ConnectionUserName` to whatever schema
  everything was actually created under (here: `APP`).
- `hadoop-aws` version must match the Hadoop client version already
  bundled in Spark's distribution (check `ls /opt/spark/jars | grep
  hadoop-client`), not just "the latest available."
- When two similarly-structured files are open at once (e.g. two
  Dockerfiles), always re-verify which file an edit landed in via `grep`
  — don't assume the IDE tab is the one you think it is.

## 9. The 14-Phase Roadmap

1. Environment Bootstrap
2. Spark Cluster on Docker Compose
3. Storage Layer — MinIO + Hive Metastore
4. Delta Lake + Sample Datasets
5. Memory & GC Failures
6. Data Skew Failures
7. Shuffle Failures
8. Serialization Failures
9. Schema & Data Quality Failures
10. Kafka + Zookeeper Layer
11. Structured Streaming Failures
12. Monitoring — Prometheus + Grafana
13. Resource & Config Failures
14. Interview Simulation & Runbook