# AWS OpenSearch Service domain for the one gated, real-cloud demo.
#
# ############################################################
# #  THIS CONFIGURATION COSTS REAL MONEY WHEN APPLIED.       #
# #  Do not run `terraform apply` without an explicit,       #
# #  real-time go-ahead from the repository owner.           #
# #  See terraform/README.md for the cost breakdown.         #
# ############################################################
#
# CI validates this configuration (`fmt`, `init -backend=false`, `validate`)
# and deliberately never plans or applies it: `plan` would need real
# credentials, and `apply` would provision a billable domain.
#
# The application needs no code change to use this. Pointing it at AWS is
# two environment variables, which is the entire reason
# duediligence/index/opensearch_client.py carries two backends:
#
#     DUEDILIGENCE_OPENSEARCH_BACKEND=aws
#     DUEDILIGENCE_OPENSEARCH_ENDPOINT=https://<domain_endpoint>

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "duediligence-rag"
      ManagedBy   = "terraform"
      Environment = var.environment
      # Tagged so a forgotten domain is findable in the console and in
      # Cost Explorer. The single most expensive mistake available here is
      # leaving this running after the demo.
      CostCenter = "portfolio-demo"
    }
  }
}

data "aws_caller_identity" "current" {}

# Restricts access to the AWS principal running Terraform rather than
# leaving the domain open. An OpenSearch domain with a public, unrestricted
# access policy is a well-known way to expose data to the internet — even
# though this corpus is public SEC filings, the habit matters.
#
# Attached as a separate `aws_opensearch_domain_policy` rather than inline
# on the domain. Inlining creates a dependency cycle — caught by
# `terraform validate`: the policy document needs the domain's ARN, and the
# domain would need the rendered policy. Splitting the attachment out gives
# a linear graph: domain -> policy document -> policy attachment.
data "aws_iam_policy_document" "domain_access" {
  statement {
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = [data.aws_caller_identity.current.arn]
    }

    actions   = ["es:ESHttp*"]
    resources = ["${aws_opensearch_domain.this.arn}/*"]
  }
}

resource "aws_opensearch_domain_policy" "this" {
  domain_name     = aws_opensearch_domain.this.domain_name
  access_policies = data.aws_iam_policy_document.domain_access.json
}

resource "aws_opensearch_domain" "this" {
  domain_name    = var.domain_name
  engine_version = "OpenSearch_2.19"

  cluster_config {
    # Single small node, matching the local single-node setup. A production
    # cluster would use dedicated master nodes and multi-AZ; both multiply
    # the bill, and neither demonstrates anything this project claims.
    instance_type  = var.instance_type
    instance_count = 1

    zone_awareness_enabled = false
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    # The local index is ~370 MB for 38,552 documents. 10 GB is the smallest
    # practical volume and leaves ample room.
    volume_size = 10
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    # IAM-based access via SigV4 (see the access policy above), not an
    # internal master user with a password. This is what
    # opensearch_client.py's "aws" backend signs requests for.
    enabled                        = false
    anonymous_auth_enabled         = false
    internal_user_database_enabled = false
  }

  tags = {
    Name = var.domain_name
  }
}
