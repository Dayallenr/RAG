output "domain_endpoint" {
  description = "HTTPS endpoint. Set DUEDILIGENCE_OPENSEARCH_ENDPOINT to https://<this>."
  value       = "https://${aws_opensearch_domain.this.endpoint}"
}

output "domain_arn" {
  description = "ARN of the OpenSearch domain."
  value       = aws_opensearch_domain.this.arn
}

output "configure_application" {
  description = "Exact environment variables that point the app at this domain."
  value       = <<-EOT
    export DUEDILIGENCE_OPENSEARCH_BACKEND=aws
    export DUEDILIGENCE_OPENSEARCH_ENDPOINT=https://${aws_opensearch_domain.this.endpoint}
    export AWS_REGION=${var.aws_region}
  EOT
}

output "destroy_reminder" {
  description = "This domain bills hourly until destroyed."
  value       = "Run `terraform destroy` as soon as the demo is finished — this domain accrues charges every hour it exists."
}

output "ecr_repository_url" {
  description = "ECR repository to push the API image to. Null unless enable_compute is true."
  value       = var.enable_compute ? aws_ecr_repository.api[0].repository_url : null
}

output "eks_cluster_name" {
  description = "EKS cluster name. Null unless enable_compute is true."
  value       = var.enable_compute ? module.eks[0].cluster_name : null
}

locals {
  # Built as a local rather than inline in the output: a heredoc cannot be
  # an operand of a ternary in HCL, its terminator must stand alone.
  deploy_instructions = var.enable_compute ? join("\n", [
    "# 1. Point kubectl at the new cluster",
    "aws eks update-kubeconfig --region ${var.aws_region} --name ${try(module.eks[0].cluster_name, "")}",
    "",
    "# 2. Build for the cluster architecture (nodes are x86; a Mac builds arm64 by default) and push",
    "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${try(aws_ecr_repository.api[0].repository_url, "")}",
    "docker build --platform linux/amd64 -f docker/Dockerfile -t ${try(aws_ecr_repository.api[0].repository_url, "")}:latest .",
    "docker push ${try(aws_ecr_repository.api[0].repository_url, "")}:latest",
    "",
    "# 3. Deploy, pointing the API at the managed OpenSearch domain",
    "kubectl apply -f k8s/api.yaml",
    "kubectl set image deployment/duediligence-api api=${try(aws_ecr_repository.api[0].repository_url, "")}:latest",
    "kubectl set env deployment/duediligence-api DUEDILIGENCE_OPENSEARCH_BACKEND=aws DUEDILIGENCE_OPENSEARCH_ENDPOINT=https://${aws_opensearch_domain.this.endpoint}",
  ]) : "enable_compute is false - only the OpenSearch domain was created"
}

output "deploy_to_eks" {
  description = "Exact commands to build, push and deploy the API onto the cluster."
  value       = local.deploy_instructions
}

output "estimated_hourly_cost" {
  description = "Rough burn rate, so it is visible in the apply output rather than discovered on a bill."
  value       = var.enable_compute ? "~$0.23/hour (~$165/month) — EKS control plane, 2x t3.medium, NAT gateway, OpenSearch domain. DESTROY WHEN DONE." : "~$0.04/hour (~$27/month) — OpenSearch domain only. DESTROY WHEN DONE."
}
