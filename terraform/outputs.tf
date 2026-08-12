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
