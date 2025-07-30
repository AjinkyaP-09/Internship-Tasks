// main.tf
// This file orchestrates the creation of all resources by calling the modules.

// 1. Networking (VPC)
module "vpc" {
  source             = "./modules/vpc"
  project_name       = var.project_name
  vpc_cidr           = var.vpc_cidr
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
  availability_zones = var.availability_zones
}

// 2. Security Groups
// DEFINITIVE FIX: Reverted to inline rules to force an "update" instead of a "destroy".
// This avoids the dependency lock and state inconsistency on the existing infrastructure.
resource "aws_security_group" "web_sg" {
  name        = "${var.project_name}-web-sg"
  description = "Allow HTTP/S and SSH traffic"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-web-sg"
  }
}

resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-app-sg"
  description = "Allow traffic from web tier and SSH"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 80 // For PHP/Apache
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  // This is the definitive rule that allows the web server (bastion) to SSH to the app server.
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.web_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-app-sg"
  }
}

resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Allow traffic only from app tier"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 3306 // MySQL port
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.app_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-db-sg"
  }
}


// 3. EC2 Instances
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "web_server" {
  source                    = "./modules/ec2"
  instance_name             = "${var.project_name}-web-server"
  ami_id                    = data.aws_ami.amazon_linux_2.id
  instance_type             = "t2.micro"
  subnet_id                 = module.vpc.public_subnet_ids[0]
  vpc_security_group_ids    = [aws_security_group.web_sg.id]
  key_name                  = var.key_name
  associate_public_ip       = true
}

module "app_server" {
  source                    = "./modules/ec2"
  instance_name             = "${var.project_name}-app-server"
  ami_id                    = data.aws_ami.amazon_linux_2.id
  instance_type             = "t2.micro"
  subnet_id                 = module.vpc.private_subnet_ids[0]
  vpc_security_group_ids    = [aws_security_group.app_sg.id]
  key_name                  = var.key_name
  associate_public_ip       = false
}

// 4. RDS Database
module "database" {
  source                 = "./modules/rds"
  db_name                = "${var.project_name}db"
  db_identifier          = "${var.project_name}-db"
  db_subnet_group_name   = module.vpc.db_subnet_group_name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_username            = var.db_username
  db_password            = var.db_password
}

// 5. Ansible Integration
// Using the more reliable INI inventory format.
resource "local_file" "ansible_inventory" {
  content = templatefile("${path.module}/ansible/inventory.tf.tpl", {
    web_public_ip    = module.web_server.public_ip,
    app_private_ip   = module.app_server.private_ip,
    key_path         = pathexpand("~/.ssh/${var.key_name}.pem"),
    db_endpoint      = module.database.rds_endpoint,
    db_user          = var.db_username,
    db_pass          = var.db_password,
    db_name          = module.database.db_name
  })
  filename = "${path.module}/ansible/inventory.ini"
}

// This resource runs the Ansible playbook after the infrastructure is ready.
resource "null_resource" "ansible_provision" {
  // Wait until EC2 instances and the inventory file are created
  depends_on = [module.web_server, module.app_server, local_file.ansible_inventory]

  provisioner "local-exec" {
    command = "ansible-playbook -i ansible/inventory.ini ansible/playbook.yml"
  }
}

