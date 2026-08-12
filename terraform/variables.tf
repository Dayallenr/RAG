variable "aws_region" {
  description = "AWS region for the OpenSearch domain."
  type        = string
  # us-east-1 is the cheapest region for this instance family and where the
  # account's free-tier allowances apply.
  default = "us-east-1"
}

variable "domain_name" {
  description = "Name of the AWS OpenSearch Service domain."
  type        = string
  default     = "duediligence-rag"

  validation {
    # AWS rejects names outside this shape with an opaque error at apply
    # time; catching it at plan time is cheaper than a failed apply.
    condition     = can(regex("^[a-z][a-z0-9-]{2,27}$", var.domain_name))
    error_message = "Domain name must be 3-28 chars, start with a lowercase letter, and contain only lowercase letters, numbers and hyphens."
  }
}

variable "instance_type" {
  description = "OpenSearch data node instance type. Drives almost the entire cost."
  type        = string
  # Smallest current-generation instance that supports the k-NN plugin.
  default = "t3.small.search"
}

variable "environment" {
  description = "Environment tag applied to all resources."
  type        = string
  default     = "demo"
}
