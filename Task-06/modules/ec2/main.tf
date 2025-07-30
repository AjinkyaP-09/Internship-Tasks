// modules/ec2/main.tf
// Creates a single EC2 instance with specified settings.
resource "aws_instance" "main" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.vpc_security_group_ids
  key_name                    = var.key_name
  associate_public_ip_address = var.associate_public_ip

  tags = {
    Name = var.instance_name
  }
}
