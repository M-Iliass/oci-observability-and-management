# OCI APM data querier function setup

This is a OCI (Oracle Cloud Infrastructure) APM data querier function setup which at the end will create an OCI function wrapped within an API gateway that can then be queried to get APM data in an easy to use format, the function code is also available if the default format does not fit your needs. 

This project aims to create all the necessary OCI resources required including creating the image, the OCI functions application and function, the API Gateway and policies. And all of this is done using terraform.

In this example we will be creating:

* 1 x Container registry to store the image (apm-data-querier-repository/apm-data-querier)
* 1 x Virtual Cloud Network (VCN) (apm-data-querier-vcn)
* 1 x Subnet (Public) (public)
* 1 x Internet Gateway for Public Subnet (igw)
* 1 x OCI application (apm-data-querier-app)
* 1 x OCI function (apm-data-querier)
* 1 x API Gateway (apm-data-querier-gateway)
* 1 x API Gateway deployment for the function (apm-data-querier-gateway-deployment)
* Create and push the function's image to the registry
* Create Functions and gateway Policies.

## Prerequisites

Before you deploy this function for use, make sure you have run step C - 3 of the [Oracle Functions Quick Start Guide for Cloud Shell](https://www.oracle.com/webfolder/technetwork/tutorials/infographics/oci_functions_cloudshell_quickview/functions_quickview_top/functions_quickview/index.html), the auth token is required to push the image to the repository.

    C - 3. Generate auth token

## Terraform Deployment

# Deploy to OCI with one click

Cick on button bellow to deploy the function to OCI using the resource manager, some values will be prepopulated:

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/M-Iliass/oci-observability-and-management/releases/download/v1.0.0/oci-apm-query-data-release.zip) 

# Deploy using local dev environment:

## Preparation:

Prepare one variable file named `terraform.tfvars` with the required information.

The contents of `terraform.tfvars` should look something like the following:

```
tenancy_ocid = "ocid1.tenancy.oc1..xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
compartment_ocid = "ocid1.compartment.oc1..xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
region = "us-ashburn-1"
current_user_ocid = "ocid1.user.oc1..xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
user_auth_token = "xxxxxxxxxxxxxxx" # Replace with your own auth token
apm_domain_id = ""
```

## Deploying the function:

Apply the changes using the following commands:

```
  terraform init
  terraform plan
  terraform apply
```

## Output

```
Outputs:

URL_to_call = "url/v1/query?query_result_name="
```

You can then call the link above while adding the background query name to the end, and that should return the query result in an easy to use format
