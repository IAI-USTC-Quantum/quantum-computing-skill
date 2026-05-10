# API key / platform health check

The user mentioned "uniqc doctor" — that subcommand **does not exist**. Use
`uniqc config validate` (and `uniqc config list`) instead. They cover the
same ground: did the user write a real config file, are the required token
fields filled in, are the platform SDKs importable.

## Step 1 — show the user the active config

```bash
uniqc config list                  # rich table of platforms + status
uniqc config validate              # exits non-zero if anything is wrong
uniqc config get originq           # prints the originq section
```

`uniqc config list` reports one of:

- `Configured` — token present, SDK importable.
- `Missing token` — `uniqc config set <platform>.token <VALUE>` (Quark uses
  `quark.QUARK_API_KEY` not `token`).
- `Missing SDK` — install the matching extra (see the table below).

## Step 2 — install the platform extra if needed

| Platform | Extra to install                    | Min Python | What it pulls            |
| -------- | ----------------------------------- | ---------- | ------------------------ |
| OriginQ  | `pip install unified-quantum[originq]` | 3.10      | `pyqpanda3`              |
| Quafu    | `pip install unified-quantum[quafu]`   | 3.10      | `pyquafu` (deprecated)    |
| Quark    | `pip install unified-quantum[quark]`   | **3.12**  | `pyquark`                |
| IBM      | `pip install unified-quantum[qiskit]`  | 3.10      | `qiskit-ibm-runtime`     |
| Chip-backed dummy (`dummy:originq:<chip>`, `dummy:quark:<chip>`) | `pip install unified-quantum[qiskit]` | 3.10 | qiskit transpiler |

`unified-quantum[all]` is a convenience meta-extra; **note it does not
include Quafu** (kept out because Quafu is deprecated).

## Step 3 — set the missing token

```bash
uniqc config set originq.token   $ORIGINQ_TOKEN
uniqc config set quafu.token     $QUAFU_TOKEN
uniqc config set quark.QUARK_API_KEY $QUARK_API_KEY    # different key!
uniqc config set ibm.token       $IBM_TOKEN
```

Then re-run `uniqc config validate`.

> ⚠️ Do **not** rely on environment variables. uniqc itself only reads
> `UNIQC_PROFILE` and `HTTP(S)_PROXY`. It does not auto-import
> `ORIGINQ_API_KEY` / `QUAFU_API_TOKEN` / `QUARK_API_KEY` / `IBM_TOKEN`.

## Step 4 — refresh the backend cache

```bash
uniqc backend update --platform originq
uniqc backend update --platform ibm
uniqc backend list                 # combined view across all configured platforms
```

If `backend list` shows a backend with `status=available` for the platform you
care about, you are clear to dry-run and submit.

## Programmatic equivalent

```python
from uniqc import config as cfg

print(cfg.get_active_profile())
for plat in cfg.SUPPORTED_PLATFORMS:
    print(plat, "configured?", cfg.has_platform_credentials(plat))

# Inspect a single platform
print(cfg.get_originq_config())
```

## Common follow-up issues

- `qiskit_runtime_service` warns "Loading account with the given token. A
  saved account will not be used" — harmless, you are using the uniqc-managed
  token rather than a saved IBM account file.
- IBM behind a proxy:
  ```bash
  uniqc config set ibm.proxy.https http://127.0.0.1:7890
  uniqc config set ibm.proxy.http  http://127.0.0.1:7890
  ```
- After fixing config you usually need `uniqc backend update --platform <p>`
  again — `uniqc backend list` returns cached entries until you do.
