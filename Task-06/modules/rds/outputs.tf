// modules/rds/outputs.tf
output "rds_endpoint" { value = aws_db_instance.main.endpoint }
output "rds_port" { value = aws_db_instance.main.port }
output "db_name" { value = aws_db_instance.main.db_name }
