variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "A name for the project, used for tagging resources."
  type        = string
  default     = "threetierapp"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "A list of CIDR blocks for public subnets."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "A list of CIDR blocks for private subnets."
  type        = list(string)
  default     = ["10.0.3.0/24", "10.0.4.0/24"]
}

variable "availability_zones" {
  description = "A list of Availability Zones to deploy into."
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "my_ip" {
  description = "Your local public IP address for SSH access."
  type        = string
  // IMPORTANT: Replace this with your actual public IP.
  // You can find it by searching "what is my ip" in Google.
  default     = "223.228.130.57/32" // For demonstration only. Be more specific in production.
}

variable "key_name" {
  description = "The name of your AWS EC2 key pair."
  type        = string
  default     = "demo"
}

variable "db_username" {
  description = "The username for the RDS database."
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "The password for the RDS database."
  type        = string
  sensitive   = true
}
