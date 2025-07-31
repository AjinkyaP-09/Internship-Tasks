# 3-Tier Web Application on AWS with Terraform and Ansible
This project deploys a classic 3-tier web application architecture on AWS. The infrastructure is provisioned using Terraform, and the servers are configured using Ansible.

The application consists of a simple user registration form where data is submitted to a PHP backend and stored in a MySQL database.

## Architecture Overview
The infrastructure is deployed in a custom VPC and is distributed across two Availability Zones for high availability.

- **Web Tier (Public Subnet):** An Nginx web server that serves a static HTML registration form and acts as a reverse proxy. This is the only layer accessible from the public internet.

- **Application Tier (Private Subnet):** An Apache server with PHP that processes the form data submitted from the web tier. It connects to the database to store the information.

- **Database Tier (Private Subnet):** A managed Amazon RDS (MySQL) instance that stores the user registration data. It is only accessible from the Application Tier.

The web server in the public subnet also functions as a bastion host, allowing Ansible to securely connect to and configure the application server in the private subnet.

## Prerequisites
Before you begin, ensure you have the following installed and configured:

**AWS CLI:** Install and configure with your IAM user credentials.

**Terraform:** Install Terraform.

**Ansible:** Install Ansible.

**AWS Account & IAM User:** An AWS account and an IAM user with sufficient permissions to create the resources defined in the Terraform code.

**EC2 Key Pair:** An EC2 key pair created in your AWS account. The private key (.pem file) should be located in the ~/.ssh/ directory on your local machine. This project assumes the key is named demo.pem.

## Project Structure
```
/3-tier-terraform-ansible/
├── main.tf
├── variables.tf
├── outputs.tf
├── providers.tf
├── terraform.tfvars
├── ansible/
│   ├── playbook.yml
│   ├── inventory.tf.tpl
│   ├── roles/
│   │   ├── webserver/
│   │   │   ├── tasks/
│   │   │   │   └── main.yml
│   │   │   ├── handlers/
│   │   │   │   └── main.yml
│   │   │   └── templates/
│   │   │       ├── default.conf.j2
│   │   │       └── index.html.j2
│   │   └── appserver/
│   │       ├── tasks/
│   │       │   └── main.yml
│   │       ├── handlers/
│   │       │   └── main.yml
│   │       └── templates/
│   │           └── submit.php.j2
│   └── ansible.cfg
└── modules/
    ├── ec2/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── rds/
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── vpc/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```
## Deployment Steps
1. Create the structure and write content of the files.

2. Configure Variables

- Open `terraform.tfvars` and update the following variables:

  - `my_ip`: Set this to your current public IP address with /32 appended (e.g., "123.45.67.89/32"). You can find your IP by searching "what is my ip" on Google.

  - `key_name`: Ensure this matches the name of your EC2 key pair in AWS.

  - `db_password`: Set a secure password for the RDS database.

3. Prepare SSH Agent

   - In the same terminal session you will use for deployment, start the SSH agent and add your private key. This is crucial for Ansible to connect to the private app server via the bastion host.
```
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/demo.pem
```
4. Initialize Terraform

   - This command downloads the necessary provider plugins.
```
terraform init
```
5. Deploy the Infrastructure

   - This command will create all the AWS resources and then automatically trigger the Ansible playbook to configure the servers.
```
terraform apply --auto-approve
```
6. Verify the Application

   - After the apply command completes, Terraform will display the website_url in the outputs.

   - Open this URL in your web browser. You should see the registration form.

   - Fill out and submit the form. You should see a "Success!" message.

## How the System Works
- **Terraform:** The .tf files define the desired state of the infrastructure on AWS. Terraform creates the VPC, subnets, EC2 instances, RDS database, and all necessary networking and security components in a modular and repeatable way.

- **Ansible:** After Terraform creates the servers, a `local-exec` provisioner in `main.tf` runs the `ansible-playbook` command.

  - Terraform first generates an `inventory.ini` file with the dynamic IP addresses of the new servers.

  - Ansible connects to the public web server and configures it by installing Nginx and setting up the reverse proxy.

  - Ansible then uses the web server as a **bastion host** (via `ProxyJump`) to securely connect to the private app server. It configures this server by installing Apache, upgrading PHP, altering the database for compatibility, and deploying the `submit.php` script.

## Cleanup
To avoid ongoing AWS charges, you can destroy all the created resources with a single command:
```
terraform destroy --auto-approve
```
