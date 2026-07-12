# ============================================================
# Meridian — Aurora PostgreSQL Module
# ============================================================
# Creates an Aurora PostgreSQL Serverless v2 cluster with:
# - pgvector extension support
# - Multi-AZ for production
# - Automated backups
# - Performance Insights
# - Encryption at rest (KMS)
# ============================================================

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ---- Security Group ----

resource "aws_security_group" "aurora" {
  name_prefix = "${var.project_name}-${var.environment}-aurora-"
  vpc_id      = var.vpc_id
  description = "Security group for Aurora PostgreSQL cluster"

  ingress {
    description     = "PostgreSQL from application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ---- Subnet Group ----

resource "aws_db_subnet_group" "aurora" {
  name       = "${var.project_name}-${var.environment}-aurora"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-subnet-group"
  }
}

# ---- Parameter Group (pgvector + performance tuning) ----

resource "aws_rds_cluster_parameter_group" "aurora" {
  name   = "${var.project_name}-${var.environment}-aurora-pg16"
  family = "aurora-postgresql16"

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements,pgvector"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = var.slow_query_log_ms
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-params"
  }
}

# ---- Aurora Cluster ----

resource "aws_rds_cluster" "main" {
  cluster_identifier = "${var.project_name}-${var.environment}"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "16.4"

  database_name   = var.database_name
  master_username = var.master_username
  # In production, use aws_secretsmanager_secret for the password
  manage_master_user_password = true

  db_subnet_group_name            = aws_db_subnet_group.aurora.name
  vpc_security_group_ids          = [aws_security_group.aurora.id]
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.aurora.name

  storage_encrypted = true
  # kms_key_id      = var.kms_key_id  # Uncomment to use customer-managed KMS key

  backup_retention_period = var.backup_retention_days
  preferred_backup_window = "03:00-04:00"

  deletion_protection = var.environment == "prod"
  skip_final_snapshot = var.environment != "prod"
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-${var.environment}-final" : null

  enabled_cloudwatch_logs_exports = ["postgresql"]

  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora"
  }

  lifecycle {
    prevent_destroy = false  # Set true in prod
  }
}

# ---- Aurora Instances ----

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "${var.project_name}-${var.environment}-writer"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-writer"
  }
}

resource "aws_rds_cluster_instance" "reader" {
  count = var.reader_count

  identifier         = "${var.project_name}-${var.environment}-reader-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled = true

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-reader-${count.index + 1}"
  }
}
