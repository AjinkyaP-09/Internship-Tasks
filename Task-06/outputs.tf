output "website_url" {
  description = "The public URL of the web server."
  value       = "http://${module.web_server.public_ip}"
}

output "web_server_public_ip" {
  description = "Public IP of the Web Server"
  value       = module.web_server.public_ip
}

output "rds_database_endpoint" {
  description = "The connection endpoint for the RDS database."
  value       = module.database.rds_endpoint
}
