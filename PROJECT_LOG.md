# PySpark Failure Lab — Project Log

A living record of every phase of building a local Docker-based lab to
reproduce real-world Spark/PySpark production failure scenarios.

- Repository: github.com/aakashdevx/pyspark-failure-lab
- Project root: /Users/aakashdeep/Documents/projects/spark_failure_project
- Author: Aakashdeep

## Environment Summary

| Item | Value |
|---|---|
| Machine | MacBook M4 Air, 16GB RAM (8 GB allocated to Docker) |
| macOS | Tahoe 26.x |
| Docker Desktop | 4.76.x |
| Java | OpenJDK 17.0.18 via Homebrew |
| Python (host) | 3.11.9 via conda env `spark-lab` |
| Spark | 3.5.3 (custom Docker image) |
| Delta Lake | 3.2.1 (`delta-spark_2.12`) |
| Hive Metastore | 3.0.0 (custom standalone image) |
| Hadoop | 3.3.6 (trimmed, bundled in Hive Metastore image) |
| MinIO | latest (S3-compatible object store) |
| IDE | PyCharm Community 2025.2.x |
| Git | 2.53.0 |

## 14-Phase Roadmap

| # | Phase | Status |
|---|---|---|
| 1 | Environment Bootstrap | Complete |
| 2 | Spark Cluster on Docker Compose | Complete |
| 3 | Storage Layer — MinIO + Hive Metastore | Complete |
| 4 | Delta Lake + Sample Datasets | Complete |
| 5 | Memory & GC Failures | Pending |
| 6 | Data Skew Failures | Pending |
| 7 | Shuffle Failures | Pending |
| 8 | Serialization Failures | Pending |
| 9 | Schema & Data Quality Failures | Pending |
| 10 | Kafka + Zookeeper Layer | Pending |
| 11 | Structured Streaming Failures | Pending |
| 12 | Monitoring — Prometheus + Grafana | Pending |
| 13 | Resource & Config Failures | Pending |
| 14 | Interview Simulation & Runbook | Pending |

---

## Phase 1 — Environment Bootstrap

### Status: Complete

### Objective
Create a clean, fully validated local development environment before
touching any Spark or Docker configuration. A shaky foundation breaks
every later phase.

### Key Decisions
- **Python 3.11.9** — PySpark 3.5.x officially supports up to Python
  3.11; Python 3.13 (the system default) has pickle/multiprocessing
  incompatibilities with PySpark that surface as runtime PicklingError
  in UDFs.
- **conda env `spark-lab`** — keeps the Python interpreter and
  PySpark packages isolated from the base Anaconda 3.13 installation.
- **Git feature-branch workflow** — all work on
  `feature/phase-X-description`, `main` is protected, squash-and-merge
  via PR, delete branch after merge.

### Files Created
- Directory scaffold: `docker/`, `notebooks/`, `scenarios/01-07/`,
  `data/{input,output,checkpoints}/`, `scripts/`, `tests/`, `docs/`,
  `monitoring/{prometheus,grafana/dashboards}/`
- `.gitignore`, `PROJECT_LOG.md`, `README.md`
- `.vscode/settings.json` (later superseded by PyCharm)
- `scripts/validate_phase1.py` (29 checks)

### Python Packages Installed
| Package | Version | Purpose |
|---|---|---|
| pyspark | 3.5.3 | Spark Python client |
| delta-spark | 3.2.1 | Delta Lake client library |
| pytest | 8.3.3 | Test harness |
| pytest-html | 4.1.1 | HTML test reports |
| jupyter | 1.1.1 | Interactive notebooks |
| ipykernel | 6.29.5 | Register conda env as Jupyter kernel |
| boto3 | 1.35.36 | S3/MinIO client |
| requests | 2.32.3 | HTTP utility |

### Validation
`validate_phase1.py`: 29/29 PASS — Python version, all imports, all 17
directories, all 3 key files, Docker daemon reachable, Git initialized.

### Issues Log

| # | Error | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `AttributeError: module 'delta' has no attribute '__version__'` | `delta-spark` does not expose `__version__` at module level — version lives in pip distribution metadata only | Replaced `delta.__version__` with a `get_pip_version('delta-spark')` helper using `subprocess` + `pip show` |

### Learning Notes
- Not every Python package exposes `__version__` as a module attribute —
  pip metadata is the authoritative source.
- IDE-side configuration (`.vscode/settings.json`) is host-specific and
  belongs in `.gitignore` unless deliberately shared.

---

## Phase 2 — Spark Cluster on Docker Compose

### Status: Complete

### Objective
Build a fully running local Spark 3.5.3 cluster inside Docker. By end of
phase: Spark Master + 2 Workers + History Server all healthy, plus a
real PySpark job submitted and passing.

### Architecture
| Component | Detail |
|---|---|
| Docker network | `spark-lab-net` (bridge) |
| spark-master | Ports 8080 (UI) + 7077 (cluster), 1 GB RAM, 1 CPU |
| spark-worker-1 | Port 8081, 2 GB RAM, 1 CPU |
| spark-worker-2 | Port 8082, 2 GB RAM, 1 CPU |
| spark-history | Port 18080, 512 MB RAM, 0.5 CPU |
| Shared volume | `spark-events` mounted in all containers |
| Total Docker RAM | ~5.5 GB of 8 GB allocated |

### Key Decisions
- **Custom Dockerfile** instead of any pre-built Spark image (see
  Issues Log #1 and #2)
- **Base image** `eclipse-temurin:17-jre-jammy` — ARM64 native, OpenJDK
  17 JRE only
- **Python 3.11 installed via deadsnakes PPA** — Ubuntu Jammy ships
  3.10 by default (see Issues Log #3)
- **Non-root `spark` user** (UID 1000) — security baseline
- **tini** as PID 1 — handles signal forwarding and zombie reaping
- **Spark configuration**: event logging on, Kryo serializer, AQE
  enabled, `spark.sql.shuffle.partitions=10` (2 workers x 1 core)

### Files Created
- `docker/spark/Dockerfile`
- `docker/spark/entrypoint.sh`
- `docker/spark/conf/spark-defaults.conf`
- `docker/spark/conf/log4j2.properties`
- `docker/docker-compose.yml`
- `scripts/validate_phase2.py` (15 checks)
- `scripts/smoke_test_phase2.py`

### Validation
- `validate_phase2.py`: 15/15 PASS — image built, all 4 containers
  running+healthy, all 4 UIs reachable, network exists, both workers
  registered with master
- `smoke_test_phase2.py`: 4/4 PASS — RDD sum(1..100)=5050, DataFrame
  1000 rows, aggregation, SQL query returns 499 rows

### Issues Log

| # | Error | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `bitnami/spark:3.5.3 not found` | Bitnami deprecated and removed their Spark image from Docker Hub | Built custom Dockerfile based on `eclipse-temurin:17-jre-jammy` |
| 2 | `apache/spark:3.5.3` entrypoint uses `KubernetesExecutorBackend` | Official Apache image is designed exclusively for Spark-on-Kubernetes, not standalone cluster mode | Custom entrypoint.sh with `master`/`worker`/`history-server` roles via case statement |
| 3 | `PYTHON_VERSION_MISMATCH: worker=3.10, driver=3.11` | Ubuntu Jammy (22.04) ships Python 3.10 by default; PySpark enforces identical minor versions between driver and all executors via a hard check in `worker.py` | Added deadsnakes PPA to Dockerfile, installed `python3.11` explicitly, set `ENV PYSPARK_PYTHON=python3.11` in the image |

### Learning Notes
- Always verify the base OS's default Python version when building
  Spark containers — `apt-get install python3` does not give you the
  version you might expect, and PySpark's driver/worker version check
  is unforgiving.
- `tini` is not optional for production-quality containers — the JVM
  does not handle PID 1 signal duties correctly on its own.
- `host.docker.internal` is required as `spark.driver.host` on macOS
  when running PySpark locally against a Docker cluster — executors
  inside the container can't reach the host's `localhost`.

---

## Phase 3 — Storage Layer (MinIO + Hive Metastore)

### Status: Complete

### Objective
Add S3-compatible object storage (MinIO) and a table metadata catalog
(Hive Metastore) to the Spark cluster, enabling `s3a://` reads/writes
and SQL catalog operations — the foundation for Delta Lake in Phase 4.

### Architecture
| Component | Detail |
|---|---|
| minio | S3-compatible store, ports 9000 (API) + 9001 (Console), 3 auto-created buckets: `spark-warehouse`, `spark-logs`, `delta-tables` |
| minio-setup | One-shot `minio/mc` init container, creates the buckets, then exits |
| hive-metastore | Custom-built image, port 9083 (Thrift), Derby embedded DB, warehouse at `s3a://spark-warehouse/hive` |
| Spark <-> MinIO | Via `hadoop-aws` 3.3.4 + `aws-java-sdk-bundle` 1.12.367 JARs added to the Spark image, configured via `fs.s3a.*` |
| Spark <-> Hive | Via `spark.hadoop.hive.metastore.uris=thrift://hive-metastore:9083` + `spark.sql.catalogImplementation=hive` |

### Why a Custom Hive Metastore Image
Two pre-built Hive Metastore images were evaluated and rejected before
building one from scratch:

| Image | Result | Reason |
|---|---|---|
| `apache/hive:3.1.3` | REJECTED | Entrypoint ignores `SERVICE_NAME` env var; crashes with `NoClassDefFoundError: TezConfiguration` |
| `bitsondatadev/hive-metastore` | REJECTED | Hardcoded MySQL on port 3306 (no Derby support); amd64-only, no ARM64 build |
| Custom Dockerfile | USED | Full control, Derby embedded, ARM64 native, S3A built in |

### Files Created
- `docker/hive-metastore/Dockerfile`
- `docker/hive-metastore/entrypoint.sh`
- `docker/hive-metastore/conf/metastore-site.xml`
- `scripts/validate_phase3.py` (23 checks)
- `scripts/smoke_test_phase3.py`

### Files Modified
- `docker/docker-compose.yml` — added `minio`, `minio-setup`,
  `hive-metastore` services + volumes
- `docker/spark/Dockerfile` — added S3A connectivity JARs
- `docker/spark/conf/spark-defaults.conf` — added S3A + Hive Metastore
  settings; temporarily commented out Delta Lake catalog config
  (deferred to Phase 4 since Delta JARs weren't installed yet, and
  left enabled it broke ALL catalog resolution)

### Validation
- `validate_phase3.py`: 23/23 PASS — all 6 services healthy, MinIO
  API/Console reachable, Hive port 9083 open (via `nc`), all 3 buckets
  present, Spark image has S3A jars, `spark-defaults.conf` has
  required settings
- `smoke_test_phase3.py`: PASSED — end-to-end test created a database
  + table via Hive Metastore, wrote a DataFrame to S3A/MinIO, read it
  back, and confirmed real Parquet files physically present in the
  bucket via `mc ls`

### Issues Log

| # | Error | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `apache/hive:3.1.3` crashes — `NoClassDefFoundError: TezConfiguration`; ignores `SERVICE_NAME` | Official image broken for standalone metastore use — missing Tez dependency, entrypoint bug | Abandoned image; built custom Dockerfile instead |
| 2 | `bitsondatadev/hive-metastore` hardcodes MySQL on port 3306, amd64-only | Community image designed for MySQL-backed metastore, not Derby; no ARM64 build | Abandoned image; built custom Dockerfile instead |
| 3 | Full Hadoop tarball download from `archive.apache.org` measured ~600 KB/s, sometimes hung entirely | Apache's permanent archive host is slow/unreliable for large files | Switched to Maven Central (JARs) and `dlcdn.apache.org` (full tarball) — both CDN-backed (Cloudflare, Varnish) |
| 4 | `tar --strip-components=1` extraction copied to wrong paths (`hadoop/`, `lib/`) repeatedly | `--strip-components=1` removes the leading `hadoop-3.3.6/` from ALL paths uniformly; assumed paths didn't account for this | Used `tar -tzf` to list real extracted paths before each fix instead of guessing |
| 5 | `bin/hadoop` script failed: missing top-level `hadoop-common-*.jar` (only had `lib/` subfolder) | Only extracted `share/hadoop/common/lib/`, missed top-level jars (`hadoop-common`, `hadoop-nfs`, etc.) directly in `share/hadoop/common/` | Extracted the entire `share/hadoop/common/` tree (top-level + lib/) in one copy |
| 6 | `Cannot find hadoop installation: $HADOOP_HOME` | `schematool` requires a real `bin/hadoop` executable, not just JARs — Maven Central has no shell scripts | Downloaded full Hadoop tarball (trimmed to `bin/`, `libexec/`, `etc/hadoop/`, `share/hadoop/common/` only) instead of JARs-only |
| 7 | `Invalid HADOOP_HDFS_HOME` / `YARN_HOME` / `MAPRED_HOME`, one at a time | `hadoop-config.sh` validates these directories exist; auto-derivation from `HADOOP_HOME` only works if `share/hadoop/{hdfs,yarn,mapreduce}` exist, which we deliberately excluded | Set all four `HADOOP_*_HOME` vars explicitly to `HADOOP_HOME` in Dockerfile |
| 8 | `Schema 'HIVE' does not exist` during Derby schema init (statement 364/474) | Known upstream bug in Hive 3.0.0's `hive-schema-3.0.0.derby.sql` — two FK constraints (`TAB_COL_STATS_FK`, `PART_COL_STATS_FK`) reference unqualified table names (`TBLS`, `PARTITIONS` instead of `"APP".TBLS`); Derby resolves unqualified names against the connecting user's schema | Changed `javax.jdo.option.ConnectionUserName` from `hive` to `APP` (Derby's default schema), matching where all other statements create objects |
| 9 | `ClassNotFoundException: PartitionExpressionForMetastore` at server startup | Class lives in `hive-exec.jar`, not bundled with standalone metastore distribution | Set `metastore.expression.proxy=DefaultPartitionExpressionProxy` (lightweight alternative bundled with standalone metastore) |
| 10 | `MetaException: DumpDirCleanerTask class not found` at server startup | Same root cause as #9 — default background task list includes a class only in `hive-exec.jar` | Restricted `metastore.task.threads.always` to only `EventCleanerTask` |
| 11 | Server appeared hung — log silent for 2+ min, `/proc/net/tcp` showed no open ports | False alarm — `/proc/net/tcp` is unreliable inside Docker Desktop for Mac's VM networking | Sent `SIGQUIT` to JVM (PID 1) for a thread dump; confirmed main thread was healthily in `ServerSocket.accept()`. Verified definitively with `nc -zv localhost 9083` — succeeded immediately |
| 12 | `spark-defaults.conf` had `DeltaCatalog` class reference with no Delta JARs installed, breaking ALL catalog operations including Hive Metastore tests | Config added proactively for Phase 4 before Delta JARs existed; `spark_catalog` resolution happens before any specific SQL operation, so it blocked everything | Commented out the two Delta Lake lines with a clear note to re-enable in Phase 4 |
| 13 | S3A JAR edit accidentally applied to `docker/hive-metastore/Dockerfile` instead of `docker/spark/Dockerfile` | Two similarly-structured Dockerfiles open at once; copy-paste landed in wrong file | Caught via `grep -n` verification showing `${SPARK_HOME}` (undefined in that context) in the wrong file; removed and reapplied correctly |
| 14 | `spark-defaults.conf` ended up with duplicate S3A/Hive config blocks | Same config block added twice across the session without checking first | Viewed full file with `cat -n`, identified exact duplicate range, replaced entire file content cleanly in one paste |

### Learning Notes
- **Always verify vendor Docker images actually work before building on
  top of them.** Pull, inspect `Config.Entrypoint`/`Config.Env`, do a
  smoke run before writing any compose config around an image.
- **Download source matters as much as the artifact itself.**
  `archive.apache.org` and Maven Central/`dlcdn.apache.org` can have
  wildly different speeds for the exact same file. Test with
  `curl --max-time 30` before committing to a Dockerfile strategy.
- **`tar --strip-components=N` strips uniformly across ALL extracted
  paths** — never assume what a path becomes after stripping; verify
  with `tar -tzf` first.
- **Standalone Hive Metastore ≠ full Hive** — several default config
  values point to classes that only exist in `hive-exec.jar`, which
  standalone metastore deliberately excludes. Any
  `ClassNotFoundException` during metastore startup is almost always
  this pattern; find the lightweight standalone-compatible alternative.
- **Don't trust `/proc/net/tcp` inside Docker Desktop for Mac** — use
  `nc -zv` for reliable port-open verification instead.
- **A thread dump (`kill -QUIT 1`) is the correct way to diagnose "is
  my JVM hung or just idle?"** — far more reliable than guessing from
  log silence.
- **When editing multiple similar files in the same session, always
  verify with `grep -n` immediately after** — don't assume the IDE tab
  you think is active actually is.

---

## Phase 4 — Delta Lake + Sample Datasets

### Status: Complete

### Objective
Add Delta Lake support on top of the existing Spark + Hive Metastore +
MinIO storage layer, and seed sample datasets for later failure scenario
phases — a skewed dataset (Phase 6), a clean baseline for comparison, a
Delta table with real schema evolution history (Phase 9), and a set of
intentionally malformed local files (Phase 9).

### Key Decisions
- **Delta Lake 3.2.1** (`delta-spark_2.12-3.2.1.jar` +
  `delta-storage-3.2.1.jar`) — Scala 2.12 matches Spark 3.5.3's build
- **Generator scripts as source of truth** — generated datasets
  (MinIO Parquet, MinIO Delta tables, local malformed files) are NOT
  committed to git; they are reproducible artifacts of
  `seed_phase4_datasets.py` and `generate_malformed_files.py`. Same
  pattern already used for `data/output/*` and `spark-warehouse/`
- **`corrupt_data.parquet` deliberately uses `os.urandom()`** — every
  run produces a different corrupt instance; committing one frozen
  copy would just freeze one of many possible failure shapes

### Files Created
- `scripts/seed_phase4_datasets.py` — generates 3 MinIO datasets
- `scripts/generate_malformed_files.py` — generates 4 local malformed
  files under `data/input/`
- `scripts/validate_phase4.py` (20 checks)
- `scripts/smoke_test_phase4.py`
- `docs/CONTEXT_FOR_CLAUDE.md` — reusable project rules document for
  future sessions

### Files Modified
- `docker/spark/Dockerfile` — added Delta Lake JARs
- `docker/spark/conf/spark-defaults.conf` — re-enabled Delta catalog
  config that was deferred in Phase 3
- `docker/docker-compose.yml` — added `../data:/data` volume mount to
  `spark-master`, `spark-worker-1`, `spark-worker-2`
- `.gitignore` — excluded `data/input/*` (except `.gitkeep`) so
  generated malformed files are not committed

### Generated Datasets

**In MinIO (via `seed_phase4_datasets.py`):**

| Path | Format | Purpose |
|---|---|---|
| `s3a://spark-warehouse/datasets/transactions_skewed` | Parquet | 100,000 rows, 80% on `customer_id=1` — extreme skew for Phase 6 |
| `s3a://spark-warehouse/datasets/transactions_clean` | Parquet | 100,000 rows, evenly distributed across 100 customer IDs — baseline |
| `s3a://delta-tables/orders_evolved` | Delta | v0: 3 rows (`order_id`, `customer_id`, `amount`); v1: appends 2 rows + new `region` column via `mergeSchema=true` — schema evolution history for Phase 9 |

**Local files (via `generate_malformed_files.py`):**

| File | Failure Mode |
|---|---|
| `data/input/malformed_transactions.csv` | Mixed: missing columns, extra columns, wrong types, empty values, blank lines, broken quoting |
| `data/input/malformed_events.json` | Missing brace, garbage line, type mismatch, missing field, nested object |
| `data/input/corrupt_data.parquet` | Valid `PAR1` magic bytes, garbage footer — fails on actual parse |
| `data/input/schema_drift_transactions.csv` | "Looks fine" but has renamed and extra columns vs. baseline schema |

### Validation
- `validate_phase4.py`: 20/20 PASS — all 6 containers healthy, Spark
  image has Delta JARs, Delta catalog enabled in
  `spark-defaults.conf`, all 3 MinIO datasets exist, exactly 2 Delta
  commit files in `_delta_log/`, all 4 local malformed files exist,
  `data/` mounted into all 3 job-running Spark containers
- `smoke_test_phase4.py`: PASSED — verified skew ratio (>70% on one
  `customer_id`), exact Delta version count, schema evolution
  correctness (no `region` at v0, present at latest), row counts
  exact, all 4 malformed files accessible inside containers, and
  `corrupt_data.parquet` correctly throws an exception on read
  (intended behavior for Phase 9)

### Issues Log

| # | Error | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | `SyntaxError` in seed script — nested f-string with escaped quotes | Python 3.11 doesn't support same-quote-type nesting inside f-string expressions (Python 3.12+ only) | Extracted the nested expression into a separate variable before the outer f-string |
| 2 | Delta table `DESCRIBE HISTORY` showed 4 versions instead of expected 2 after re-running the seed script | `overwrite` on an *existing* Delta table doesn't reset version numbering — each full script run adds 2 new commits on top, growing history indefinitely on every re-run | Added an idempotency step: delete the existing Delta path before writing v0, so any number of re-runs always produces a clean 2-version history |
| 3 | `IllegalArgumentException: Wrong FS: s3a://..., expected: file:///` when checking if the Delta path existed | `FileSystem.get(hadoop_conf)` without a URI argument returns the default (local) filesystem, not S3A | Passed the path's URI explicitly: `FileSystem.get(uri, hadoop_conf)` instead of `FileSystem.get(hadoop_conf)` |
| 4 | Malformed sample files created in `data/input/` were not visible inside `spark-master` or worker containers | The project's `data/` directory was never mounted into any Spark container since Phase 1 — only `spark-events` was ever mounted | Added `../data:/data` volume mount to `spark-master`, `spark-worker-1`, `spark-worker-2` in `docker-compose.yml` |
| 5 | `corrupt_data.parquet` was silently ignored by git | A blanket `*.parquet` rule in `.gitignore` (added in Phase 1 to exclude generated Spark output) was also excluding our deliberately-created test fixture | Decided not to commit any generated test data — added `data/input/*` to `.gitignore` and rely on `generate_malformed_files.py` as the source of truth (same pattern as MinIO datasets) |

### Learning Notes
- **Seed/setup scripts that write to existing-table-style storage
  (Delta, Hive tables) must be explicitly designed for idempotency** —
  unlike a plain file `overwrite` to a path, Delta's `overwrite` is
  itself a new transaction log entry, not a reset. Always consider
  "what happens if this runs twice?" before treating a script as safe
  to re-run.
- **Hadoop's `FileSystem.get()` needs a URI to resolve the correct
  filesystem implementation** — calling it with only a `Configuration`
  object silently defaults to the local filesystem, which fails loudly
  (and confusingly) the moment you try to use it against a non-local
  scheme like `s3a://`.
- **Volume mounts established early in a project should be audited
  whenever a new directory becomes load-bearing** — `data/input/` was
  scaffolded in Phase 1 but never wired into the actual running
  containers until Phase 4 needed it. A quick `docker exec ... ls`
  check caught this before it became a Phase 9 blocker.
- **Always test the "should fail" path explicitly in a smoke test**,
  not just the happy path — confirming `corrupt_data.parquet` actually
  throws an exception on read is just as important as confirming the
  good datasets read correctly.
- **Generator scripts > committed test fixtures** when the fixtures
  are deterministic or cheap to regenerate; the script is the source
  of truth, and committing the artifacts just adds version-control
  noise and storage cost. Non-deterministic fixtures (anything using
  `os.urandom()` etc.) shouldn't be committed at all since each commit
  freezes one arbitrary instance.

---

## Standing Rules (apply to every future phase)

1. **One phase at a time.** Don't pre-empt next steps. Wait for
   explicit "Move to next phase" before introducing Phase N+1.
2. **Never assume infra/versions/paths.** Present options, wait for
   explicit choice before writing code.
3. **Code blocks for permanent files, not `cat` heredocs.** Typing
   builds understanding. Heredocs are fine only for ephemeral
   in-container debug scripts during live troubleshooting.
4. **Before any Dockerfile download, verify URL + speed** with
   `curl -I` and `curl --max-time 30`. Prefer Maven Central
   (`repo1.maven.org`) and `dlcdn.apache.org` over slow
   `archive.apache.org`.
5. **After every file edit, verify with `grep -n` that the change
   landed in the intended file** and no duplicates were introduced.
6. **All work on feature branches**, PR via squash-and-merge, delete
   branch after merge, sync local `main` before next phase. Exception:
   Phase 4 branch deliberately kept as `feature/phase-4-Delta-Lake`
   (mixed case) against convention.
7. **Update `PROJECT_LOG.md` at the close of every phase** — objective,
   files, validation, issues table, learning notes, interview Q&A.
8. **Generate interview Q&A every phase**, four levels
   (Beginner / Intermediate / Advanced / Scenario-Based).
9. **Maintain `pyspark_failure_lab_guide_vX.X.docx`** — bump 0.1 per
   phase closed, regenerated via Node.js `docx` package (not
   hand-edited), includes full source code for every file.