cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# S3 Bucket for database logs
resource "aws_s3_bucket" "db_logs" {
  bucket = "remedy-sentinel-logs-${random_id.id.hex}"
}

resource "random_id" "id" {
  byte_length = 4
}

# Simple EC2 to run our Docker setup
resource "aws_instance" "db_server" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04
  instance_type = "t2.micro"
  
  user_data = file("user_data.sh")

  tags = {
    Name = "SentinelRemedy-Server"
  }
}
EOF