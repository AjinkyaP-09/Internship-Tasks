# ansible/inventory.tf.tpl
# INI-style template with native bastion host support.
[web]
${web_public_ip} app_server_private_ip=${app_private_ip}

[app]
${app_private_ip}

[all:vars]
ansible_ssh_user=ec2-user
ansible_ssh_private_key_file=${key_path}

[app:vars]
ansible_ssh_bastion_host=${web_public_ip}
ansible_ssh_bastion_user=ec2-user
db_endpoint="${db_endpoint}"
db_user="${db_user}"
db_pass="${db_pass}"
db_name="${db_name}"
