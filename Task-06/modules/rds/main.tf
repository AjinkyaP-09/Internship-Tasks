// modules/rds/main.tf
// Creates a single RDS instance (MySQL).
resource "aws_db_instance" "main" {
  identifier             = var.db_identifier
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "mysql"
  engine_version         = "8.0.41"      // Using modern version, as t4g should support it.
  instance_class         = "db.t4g.micro" // FIXED: Switched to Graviton-based Free Tier instance.
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = var.db_subnet_group_name
  vpc_security_group_ids = var.vpc_security_group_ids
  skip_final_snapshot    = true // Use 'false' in production
  publicly_accessible    = false
}
