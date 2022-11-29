# AWS Route53 Modification Service

This service is designed primarily for hobiests and is not deemed ready for a Production environment. In a multie AWS account environment it may be desired to have multiple accounts leverage Route53 Hosted Zone records that are owned and governed by different AWS account. It is often less than ideal to allow those accounts full access to Route53 Hosted Zones to limit your attack surface.

This service tries to solve that issue by allowing specified accounts to submit Route53 modification requests that require approval from a list of email addresses for the execution to actually take place. This allows for easier CloudFormation deployments as you do not need to allow access to an entire remote account and all entities within that account to be able to modify your Route53 records. Instead, CloudFormation deployments can create Custom resources that submit Route53 modification requests to this service that then get approved by a list of approvers before it is allowed to be changed.

## Current State
This code base is functional but still in development for feature refinement and edge case testing / bug fixing. Use at your own risk.

# Deployment Parameters
> ## AwsAcmCertificateArn
> The ACM Certificate Arn within the account that will be leveraged for this services' API Gateway Custom Domain Name. This currently must be created and verified prior to deployment.

> ## APICustomDomainName
> The full API Gateway Custom Domain Name you wish to assign to the API Gateway resource.

> ## MetricNamespace
> The metric Namespace you wish to assign metrics in CloudWatch Metrics for this service.

> ## ServiceName
> The service name being leveraged in this deployment. Used in Lambda Power Tools Metrics & CloudWatch Log names.

> ## AWSAccountsAllowedAccess
> A CommaDeliminatedList of AWS Account Ids you wish to allow access to this service via API Gateway Resource.

> ## Route53ChangeApprovalEmailTargets
> A CommaDeliminatedList of Email Addresses that you wish to send verification notifications to for each Route53 request.

# Configuration File
There is a "configuration JSON structure" that exists in secrets manager when the template is created. This file is used to scope down access to Hosted Zones if an AWS account owns / governs more than one Hosten Zone in question. It is fairly basic and allows you to create an entry similar to the below:

```json
{
    "<AWS_Account_Id>": [
        "<AWS_Hosted_Zone_Name>",
        "<AWS_Hosted_Zone_Id>"
    ]
}
```

What this does is allows the AWS account specified only to submit requests for the Hosted Zone Names or Ids within the list.

# Caveats

## Time Constrain - Five Minutes
> ### Description:
>The current design requires that an owner of an approver email address respond to the request within five minutes or it will cound as a rejection.
>
>### Rationale:
>This service was primarily designed to solve a Route53 switching issue I was bumping into when trying to leverage a Domain governed by another AWS account I owned. The timeout for CloudFormation was often much faster than I could switch accounts and alter the records. I didn't want to expand my risk surface of allowing account B to freely modify Hosted Zones in Account A and so I came up with this solution. Since CloudFormation can have short DNS Validation windows I have reduced the approval window in this service as well.