variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "rate_limit_per_5min" {
  description = "Maximum requests per IP per 5 minutes"
  type        = number
  default     = 1000
}

variable "alb_arn" {
  description = "ARN of the ALB to protect with WAF. Empty string to skip association."
  type        = string
  default     = ""
}
