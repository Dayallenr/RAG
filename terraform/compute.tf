# VPC, EKS cluster, and ECR registry to run the API on real AWS.
#
# ############################################################
# #  STATUS: NEVER APPLIED. No EKS cluster, VPC, NAT gateway  #
# #  or ECR repository has ever been created from this file.  #
# #  It passes `fmt` and `validate` only — that proves the    #
# #  HCL is well-formed, not that the stack provisions or     #
# #  that the API runs on it.                                 #
# #                                                           #
# #  OPT-IN. Everything in this file is gated behind          #
# #  `var.enable_compute`, which defaults to FALSE.           #
# #                                                           #
# #  A plain `terraform apply` creates ONLY the OpenSearch    #
# #  domain (~$0.04/hr). This file adds roughly $0.23/hr      #
# #  (~$165/month) and is created only with:                  #
# #      terraform apply -var enable_compute=true             #
# ############################################################
#
# The default is false on purpose. The single most expensive mistake
# available in this repository is leaving an EKS control plane running —
# it bills continuously at ~$73/month whether or not a single pod is
# scheduled, and unlike a forgotten EC2 instance there is no "stopped"
# state. Making the expensive path require an explicit flag means it cannot
# be created by muscle memory.
#
# Uses the official upstream modules rather than hand-rolled resources.
# A correct EKS setup is several hundred lines of IAM, security groups, and
# subnet tagging that Kubernetes' AWS cloud provider depends on in ways that
# fail obscurely when wrong; the maintained modules encode that. Versions
# are pinned so a re-apply months later provisions the same thing.

locals {
  compute_count = var.enable_compute ? 1 : 0
  cluster_name  = "${var.domain_name}-eks"

  # Two AZs: EKS requires subnets in at least two availability zones.
  azs = ["${var.aws_region}a", "${var.aws_region}b"]
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  count = local.compute_count

  name = "${var.domain_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = local.azs
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # One NAT gateway, not one per AZ. Nodes sit in private subnets and need
  # egress to pull images and reach the OpenSearch endpoint. A NAT per AZ is
  # the highly-available choice and doubles this line item; for a
  # short-lived demo a single gateway is the right trade, and it is a
  # deliberate trade rather than an oversight.
  enable_nat_gateway = true
  single_nat_gateway = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  # Subnet tags the AWS load balancer controller and EKS itself look for
  # when deciding where to place load balancers. Omitting them is a classic
  # cause of "service stuck in pending" with no useful error.
  public_subnet_tags = {
    "kubernetes.io/role/elb"                      = 1
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"             = 1
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.24"

  count = local.compute_count

  cluster_name    = local.cluster_name
  cluster_version = "1.31"

  vpc_id     = module.vpc[0].vpc_id
  subnet_ids = module.vpc[0].private_subnets

  # Public API endpoint so kubectl works from a laptop without a bastion or
  # VPN. Access is still authenticated and authorized through IAM; this is
  # not an unauthenticated endpoint. A production cluster would restrict
  # `cluster_endpoint_public_access_cidrs` to known ranges.
  cluster_endpoint_public_access = true

  # Grant the identity running Terraform cluster-admin, otherwise the
  # cluster is created and then immediately unusable from this machine —
  # a genuinely common first-EKS surprise.
  enable_cluster_creator_admin_permissions = true

  eks_managed_node_groups = {
    default = {
      # t3.medium is the smallest instance that comfortably runs the API:
      # the pod requests 1Gi and holds two transformer models resident.
      instance_types = ["t3.medium"]
      min_size       = 2
      max_size       = 4
      desired_size   = 2

      # The API image is ~2.1GB and the model cache is an emptyDir sized at
      # 2Gi; the default 20GB root volume leaves little room once a couple
      # of image layers and logs are present.
      disk_size = 40
    }
  }

  tags = {
    Name = local.cluster_name
  }
}

resource "aws_ecr_repository" "api" {
  count = local.compute_count

  name = var.domain_name
  # EKS nodes pull by digest on restart; mutable tags mean "latest" can
  # silently change under a running deployment.
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  # Lets `terraform destroy` remove the repository even with images in it.
  # Correct for a demo that must tear down cleanly; wrong for production,
  # where the images are the artifact you least want deleted by accident.
  force_delete = true
}

resource "aws_ecr_lifecycle_policy" "api" {
  count = local.compute_count

  repository = aws_ecr_repository.api[0].name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 5 most recent images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}
