variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Aurora will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to connect to Aurora"
  type        = list(string)
}

variable "database_name" {
  description = "Name of the default database"
  type        = string
  default     = "meridian"
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "meridian_admin"
}

variable "min_capacity" {
  description = "Minimum ACUs for Serverless v2 (0.5 ACU = ~1GB RAM)"
  type        = number
  default     = 0.5
}

variable "max_capacity" {
  description = "Maximum ACUs for Serverless v2"
  type        = number
  default     = 4
}

variable "reader_count" {
  description = "Number of read replicas (0 for dev, 1-2 for prod)"
  type        = number
  default     = 0
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 7
}

variable "slow_query_log_ms" {
  description = "Log queries slower than this (ms). -1 disables."
  type        = string
  default     = "1000"
}
