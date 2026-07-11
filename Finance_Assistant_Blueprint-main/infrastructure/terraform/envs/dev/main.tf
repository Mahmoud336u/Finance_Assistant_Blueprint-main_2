# ============================================================
# Meridian — Dev Environment
# ============================================================
# This is the entry point for the dev environment.
# It composes all modules with dev-appropriate settings.
#
# Usage:
#   cd infrastructure/terraform/envs/dev
#   terraform init
#   terraform plan
#   terraform apply
# ============================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "meridian-terraform-state"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "meridian-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "meridian"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

# ---- Variables ----

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

# ---- VPC Module ----

module "vpc" {
  source = "../../modules/vpc"

  project_name       = "meridian"
  environment        = "dev"
  vpc_cidr           = "10.0.0.0/16"
  az_count           = 2
  single_nat_gateway = true   # Cost saving for dev
  enable_flow_logs   = false  # Enable in staging/prod
}

# ---- Outputs ----

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

# TODO: Add Aurora, Redis, ECS modules (Phase 2)
