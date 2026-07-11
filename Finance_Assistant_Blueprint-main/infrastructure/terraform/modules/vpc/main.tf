# ============================================================
# Meridian — VPC Module
# ============================================================
# Creates a production-ready VPC with:
# - 2 AZ deployment
# - Public subnets (NAT Gateway, ALB)
# - Private subnets (ECS, Aurora, Redis)
# - NAT Gateway for private subnet internet access
# - VPC Flow Logs
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

# ---- Data Sources ----

data "aws_availability_zones" "available" {
  state = "available"
}

# ---- VPC ----

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}

# ---- Public Subnets (ALB, NAT Gateway) ----

resource "aws_subnet" "public" {
  for_each = { for idx, az in slice(data.aws_availability_zones.available.names, 0, var.az_count) : az => idx }

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, each.value)
  availability_zone       = each.key
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-${var.environment}-public-${each.key}"
    Tier = "public"
  }
}

# ---- Private Subnets (ECS, Aurora, Redis) ----

resource "aws_subnet" "private" {
  for_each = { for idx, az in slice(data.aws_availability_zones.available.names, 0, var.az_count) : az => idx }

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, each.value + var.az_count)
  availability_zone = each.key

  tags = {
    Name = "${var.project_name}-${var.environment}-private-${each.key}"
    Tier = "private"
  }
}

# ---- Internet Gateway ----

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-igw"
  }
}

# ---- NAT Gateway (one per AZ for HA in prod, single for dev) ----

resource "aws_eip" "nat" {
  for_each = var.single_nat_gateway ? { "single" = 0 } : { for idx, az in slice(data.aws_availability_zones.available.names, 0, var.az_count) : az => idx }

  domain = "vpc"

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-eip-${each.key}"
  }
}

resource "aws_nat_gateway" "main" {
  for_each = aws_eip.nat

  allocation_id = each.value.id
  subnet_id     = var.single_nat_gateway ? values(aws_subnet.public)[0].id : aws_subnet.public[each.key].id

  tags = {
    Name = "${var.project_name}-${var.environment}-nat-${each.key}"
  }

  depends_on = [aws_internet_gateway.main]
}

# ---- Route Tables ----

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  for_each = var.single_nat_gateway ? { "single" = values(aws_nat_gateway.main)[0].id } : { for k, v in aws_nat_gateway.main : k => v.id }

  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = each.value
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-private-rt-${each.key}"
  }
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = var.single_nat_gateway ? values(aws_route_table.private)[0].id : aws_route_table.private[each.key].id
}

# ---- VPC Flow Logs ----

resource "aws_flow_log" "main" {
  count = var.enable_flow_logs ? 1 : 0

  iam_role_arn    = aws_iam_role.flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.flow_log[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-${var.environment}-flow-log"
  }
}

resource "aws_cloudwatch_log_group" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name              = "/aws/vpc/flow-log/${var.project_name}-${var.environment}"
  retention_in_days = 30
}

resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name = "${var.project_name}-${var.environment}-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0

  name = "flow-log-policy"
  role = aws_iam_role.flow_log[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ]
      Effect   = "Allow"
      Resource = "*"
    }]
  })
}
