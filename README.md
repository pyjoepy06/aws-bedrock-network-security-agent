# AWS Bedrock Network Security Investigator

A read-only open-source example for investigating AWS Security Group inbound rules using **Amazon Bedrock (Nova Lite)**, **Strands Agents**, **Python**, and **Boto3**.

> Educational demonstration, not a comprehensive security assessment. Verify AI conclusions against AWS configuration.

## How it works

```text
Terminal (AWS SSO credentials)
  |
  +-- Python / Strands Agent
        |-- Bedrock Nova Lite — analyzes findings
        |
        +-- @tool get_security_groups()
              +-- Boto3 -> EC2 DescribeSecurityGroups (read-only)
```

**The Model** provides the intelligence. **The Tools** retrieve AWS information. **The Permissions** control access.

## Prerequisites

- Python 3.10+ and AWS CLI v2
- An AWS development/sandbox account and appropriate IAM Identity Center (SSO) access
- EC2 `DescribeSecurityGroups` and permission to invoke the selected Bedrock inference profile
- Amazon Nova Lite cross-Region inference profile available in `us-east-1` (verify availability in your account)

AWS Bedrock inference can incur charges. Do not use root credentials. Use an authorized development or sandbox account for testing.

## Installation

```bash
git clone https://github.com/pyjoepy06/aws-bedrock-network-security-agent.git
cd aws-bedrock-network-security-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## AWS authentication

Configure your own organization's IAM Identity Center start URL and **SSO Region** (which may differ from `us-east-1`).

```bash
aws configure sso --profile ai-dev
aws sso login --profile ai-dev
export AWS_PROFILE=ai-dev
export AWS_REGION=us-east-1
aws sts get-caller-identity
```

Confirm you are in the intended **development account**. Rerun `aws sso login --profile ai-dev` when the SSO session expires.

## Run the investigator

```bash
python agent.py
```

The included working example uses `us.amazon.nova-lite-v1:0` with Bedrock in `us-east-1`. Boto3's EC2 client uses your active AWS profile/Region and paginates **all** Security Groups in that Region. Results include ID, group name, VPC ID and inbound rules.

The agent explains potentially risky inbound rules, suggests improvements and **does not modify AWS resources**. A default Security Group self-reference is not automatically a vulnerability. A public CIDR on a Security Group does not, by itself, establish actual host reachability.

## Optional test: intentionally permissive SSH rule

**Only in an authorized sandbox**, create a test Security Group that is **not attached** to any instance or network interface. Do not use an existing Security Group.

```bash
export DEMO_VPC_ID=vpc-REPLACE_WITH_YOUR_DEV_VPC

export DEMO_SG_ID=$(aws ec2 create-security-group \
  --group-name ai-agent-security-demo \
  --description "Unattached Security Group for AI security testing" \
  --vpc-id "$DEMO_VPC_ID" \
  --query GroupId --output text)

echo "$DEMO_SG_ID"

aws ec2 authorize-security-group-ingress \
  --group-id "$DEMO_SG_ID" \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

python agent.py
```

**What to look for:** Review why SSH from `0.0.0.0/0` is overly permissive, what risk it *could* create if attached to a publicly reachable resource, and which other factors (attachment, public IP, internet routes, NACLs, host firewall) determine actual reachability.

### Cleanup — required

```bash
aws ec2 delete-security-group --group-id "$DEMO_SG_ID"
```

Verify the group is deleted. If `DEMO_SG_ID` is unset, obtain and verify the exact demo group's ID before deleting anything. No EC2 instances are launched.

## Least-privilege IAM

The [iam-policy.json](iam-policy.json) file is an **illustrative template**, **not a ready-to-attach or independently tested policy**. It contains `<ACCOUNT_ID>` and `<REPLACE_WITH_ACTUAL_MODEL_REGION>` placeholders that must be replaced. A correctly scoped cross-Region policy needs the inference profile ARN plus all foundation model ARNs for its source and destination Regions; otherwise invocation may fail. Confirm actual model ARNs with:

```bash
aws bedrock get-inference-profile \
  --inference-profile-identifier us.amazon.nova-lite-v1:0 \
  --region us-east-1 \
  --query '{profileArn:inferenceProfileArn,modelArns:models[].modelArn}'
```

If the returned models include several Regions, include **each** model ARN in the policy. AWS Organizations SCPs must also allow the required destination Regions (or a suitable inference-profile exception). See [AWS cross-Region inference IAM requirements](https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html).

For the real application, grant access through a dedicated role with no write permissions. The separate *demo setup* CLI commands need EC2 create/delete/authorize permissions and should be run only by an authorized operator in a sandbox.

## Limitations and security

This example sends Security Group rule details to the Bedrock model and analyzes all Security Groups in the configured Region. For sensitive or production environments, scope by VPC/group and minimize data shared with the model. There is no automated remediation, deterministic scoring, rule applicability evaluation, or complete public exposure analysis.

Never commit access keys, SSO caches, `.aws` configuration, `.venv`, or client resource inventories. The supplied `.gitignore` helps with local development, but does not replace secret scanning and review.

