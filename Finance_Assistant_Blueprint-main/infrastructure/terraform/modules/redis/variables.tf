variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Redis will be deployed"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the Redis subnet group"
  type        = list(string)
}

variable "allowed_security_group_ids" {
  description = "Security group IDs allowed to connect to Redis"
  type        = list(string)
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t4g.micro"
}

variable "num_cache_clusters" {
  description = "Number of cache clusters (1 for dev, 2+ for HA)"
  type        = number
  default     = 1
}

variable "transit_encryption" {
  description = "Enable TLS for Redis connections"
  type        = bool
  default     = false
}

variable "snapshot_retention_days" {
  description = "Number of days to retain Redis snapshots"
  type        = number
  default     = 1
}
