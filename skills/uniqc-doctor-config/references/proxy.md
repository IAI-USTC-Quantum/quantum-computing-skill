# Proxy / firewall / connectivity

`uniqc doctor` section 7 ("Platform connectivity") performs a
minimum-permission ping for every configured platform. A failure here
is almost always one of:

1. Token expired / revoked / wrong instance.
2. Outbound HTTPS blocked by the corporate network.
3. Need a proxy uniqc doesn't yet know about.

## Standard envs uniqc honors

uniqc itself only auto-reads:

- `UNIQC_PROFILE` — pick a config profile.
- `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` — picked up by `requests`
  and `urllib3` for generic HTTP traffic.

Platform SDKs sometimes have their own env hooks (qiskit-ibm-runtime
reads `QISKIT_IBM_TOKEN` etc.). uniqc bypasses those by reading from
its own config file — be explicit.

## IBM-specific proxy

IBM Quantum often needs an explicit proxy. Put it in config so the CLI,
Python API, and tests share one source of truth:

```bash
uniqc config set ibm.proxy.https http://127.0.0.1:7890
uniqc config set ibm.proxy.http  http://127.0.0.1:7890
uniqc config validate
uniqc backend update --platform ibm
```

`ibm.proxy.https` / `ibm.proxy.http` map onto the qiskit Sampler
runtime client at submit time.

## Test the path step by step

```bash
# 1. local DNS / reachability (replace host with the platform endpoint
#    printed by `uniqc config get ibm` etc.)
curl -v --max-time 10 https://api.quantum.ibm.com/runtime
curl -v --max-time 10 https://qcloud.originqc.com.cn

# 2. with the configured proxy
HTTPS_PROXY=$(uniqc config get ibm.proxy.https) curl -v --max-time 10 \
    https://api.quantum.ibm.com/runtime

# 3. force-refresh through uniqc
uniqc backend update --platform ibm
uniqc doctor                # the "Platform connectivity" section should now go green
```

## Common patterns

- **`SSLCertVerifyError`** — corporate MITM proxy with a private CA.
  Add the corporate CA to `certifi` or set
  `REQUESTS_CA_BUNDLE=/path/to/corp-ca.pem`. uniqc inherits this from
  `requests`.
- **`401 Unauthorized` on IBM** but token is fresh — `ibm.instance`
  is wrong (account changed plans, or you're on Pay-As-You-Go and need
  `ibm-q/open/main` swapped for the new instance).
- **`NetworkError: Connection timed out`** on OriginQ behind a VPN —
  `originq` doesn't honor the IBM proxy fields. Set
  `HTTPS_PROXY=...` for the shell that runs uniqc, or whitelist the
  OriginQ endpoint in the VPN client.
- **`uniqc backend update --platform ibm` reports success but
  `backend list --platform ibm` is empty** — only happens on pre-0.0.13
  versions (`fetch_platform_backends` swallowed the exception). Upgrade
  uniqc.
