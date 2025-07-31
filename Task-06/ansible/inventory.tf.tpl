# ansible/inventory.tf.tpl
# DEFINITIVE FIX: Using the most explicit host-level variable definitions
# to ensure correct bastion/ProxyJump connection.
[web]
${web_public_ip} ansible_user=ec2-user ansible_ssh_private_key_file=${key_path} app_server_private_ip=${app_private_ip}

[app]
${app_private_ip} ansible_user=ec2-user ansible_ssh_private_key_file=${key_path} ansible_ssh_common_args='-o StrictHostKeyChecking=no -o ProxyJump=ec2-user@${web_public_ip}'

# Database variables are still passed to the app host group
[app:vars]
db_endpoint="${db_endpoint}"
db_user="${db_user}"
db_pass="${db_pass}"
db_name="${db_name}"
