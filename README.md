# AWS template

## Installation

1. Install Git CLI
    
    `sudo apt install git`
    
1. Install AWS CLI
  
    `sudo apt install awscli`
  
1. Install Terraform
  
    <pre>
    sudo apt install unzip
    wget https://releases.hashicorp.com/terraform/0.12.20/terraform_0.12.20_linux_amd64.zip
    unzip terraform_0.12.20_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
    terraform --version
    </pre>

1. Clone this repo
  
    `git clone https://github.com/popiol/aws_template.git`
  
1. Create new repo on github.com
  
1. Fork aws_template into your new repo
  
    `aws_template/lifecycle/fork_template.sh <new_repo_clone_url>`
  
1. Go to your new project 
  
    `cd <new_repo_name>`
  
## Lifecycle functions

1. Fork aws_template repo
1. Update aws_template scripts
1. Create new dev brach from master
1. Deploy dev branch to AWS
1. Commit & push dev branch once a day
1. Automated tests of dev deployment
1. Create release branch from master
1. Merge from dev to release
1. Deploy release branch to AWS
1. Automated tests of release deployment
1. Merge from release to master
1. Deploy master branch to AWS
1. Automated tests of prod deployment
1. Commit & push master branch once a day
