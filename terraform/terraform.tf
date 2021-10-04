terraform {
    # I'd recommend changing the backend to S3 or some other remote backend,
    # but for reusability, I'll just leave this to local.
    backend "local" {
        path = "state/terraform.tfstate"
    }
}

provider "aws" {
  region  = "eu-west-1"
  profile = "stack-half-full"   # change this to your own IAM profile
}