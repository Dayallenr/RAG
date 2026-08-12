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

## Two tiers, and the expensive one is opt-in

| | Created | Rough cost |
|---|---|---|
| **Default** (`enable_compute = false`) | OpenSearch domain + access policy | **~$0.04/hr**, ~$27/mo |
| **With compute** (`-var enable_compute=true`) | …plus VPC, NAT, EKS cluster, 2× t3.medium, ECR | **~$0.23/hr**, ~$165/mo |

The compute tier defaults to **off** deliberately. An EKS control plane
bills ~$73/month continuously whether or not a single pod is scheduled, and
unlike an EC2 instance there is no "stopped" state — you either have a
cluster or you don't. Requiring an explicit flag means the expensive stack
cannot be created by muscle memory.

Everything bills **hourly from creation until destroyed**. Against the ~$100
credit budget this project shares with another, a forgotten compute stack
burns roughly $5.50/day. The failure mode that actually costs money is never
the demo — it is forgetting to destroy afterwards.

## Running it (requires an explicit human decision)

Storage only — the cheap demo:

```bash
terraform -chdir=terraform init
terraform -chdir=terraform apply
```

Full stack, including EKS and ECR:

```bash
terraform -chdir=terraform apply -var enable_compute=true
```

Point the application at the managed domain with no code change:

```bash
export DUEDILIGENCE_OPENSEARCH_BACKEND=aws
export DUEDILIGENCE_OPENSEARCH_ENDPOINT=https://<domain_endpoint>
python scripts/build_index.py --recreate
```

The `deploy_to_eks` output prints the exact build/push/deploy commands for
the compute tier, including `--platform linux/amd64` — the nodes are x86 and
a Mac builds arm64 by default, which produces pods that crash-loop with an
exec format error.

**Destroy as soon as the demo is done:**

```bash
terraform -chdir=terraform destroy -var enable_compute=true
```

Pass the same `-var` you applied with, or Terraform will plan against a
different configuration than the one that exists.

## What has never been tested

Beyond the fact that nothing has been applied: the `aws` backend in
`duediligence/index/opensearch_client.py` — SigV4 request signing via boto3
— has never run against a real domain. Its only test coverage is the
"unknown backend is rejected" path. The first apply is also the first real
exercise of that code.

IAM permissions the applying principal needs: `es:*`, `ec2:*`, `eks:*`,
`ecr:*`, `iam:*` (for role creation), and `iam:CreateServiceLinkedRole` —
AWS OpenSearch and EKS both require service-linked roles that are created on
first use.

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
