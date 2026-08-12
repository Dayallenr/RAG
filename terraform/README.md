# Terraform — AWS OpenSearch Service (money-gated)

**This configuration has never been applied.** It is written, formatted,
and validated (`terraform validate` passes, and CI enforces `fmt -check` and
`validate` on every push), but no AWS resource has been created from it. The
retrieval numbers reported in this project were produced against the local
Docker OpenSearch, not against AWS.

That distinction is deliberate and is the honest state of things: a
`validate` pass proves the configuration is syntactically and semantically
well-formed, and nothing more. It does not prove the domain comes up, that
the k-NN plugin behaves identically on AWS's managed build, or that SigV4
request signing works end to end. Those claims would require an apply, and
an apply costs money.

## Why it is gated

`terraform apply` provisions a real, billable AWS OpenSearch Service
domain. It bills **hourly from creation until destroyed**, whether or not
anything queries it.

Rough order of magnitude for the configured `t3.small.search` single node
plus 10 GB gp3 in `us-east-1`: a few cents per hour, so roughly **$25–30 per
month** if left running. A weekend forgotten is a few dollars; a forgotten
month is a meaningful fraction of the ~$100 credit budget this project
shares with another.

The failure mode that actually costs money is not the demo — it is
forgetting to destroy afterwards.

## Running it (requires an explicit human decision)

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan     # review what will be created
terraform -chdir=terraform apply    # ← creates billable resources
```

Then point the application at it with no code change:

```bash
export DUEDILIGENCE_OPENSEARCH_BACKEND=aws
export DUEDILIGENCE_OPENSEARCH_ENDPOINT=https://<domain_endpoint>
python scripts/build_index.py --recreate
```

**Destroy as soon as the demo is done:**

```bash
terraform -chdir=terraform destroy
```

## What CI does and does not do

CI runs `fmt -check`, `init -backend=false`, and `validate`. It deliberately
does **not** run `plan` (which needs real credentials) or `apply` (which
creates billable infrastructure). There is no AWS credential configured in
the repository's CI at all, so an accidental apply from automation is not
possible.

## Design notes

- **IAM/SigV4, not a master password.** The access policy grants
  `es:ESHttp*` to the calling AWS principal only. An OpenSearch domain with
  an open access policy is a well-known data-exposure pattern; the corpus
  here is public SEC filings, but the default should not depend on that.
- **Encryption at rest, node-to-node encryption, and TLS 1.2 enforced.**
  Cheap to enable, and awkward to retrofit.
- **Single node, no zone awareness, no dedicated masters.** Matches the
  local single-node setup and the index's `number_of_replicas: 0`. A
  multi-AZ production topology would multiply the bill without demonstrating
  anything this project claims.
- **Everything is tagged** `Project=duediligence-rag`, including a
  `CostCenter`, so a forgotten domain is findable in Cost Explorer.
