import boto3
from strands import Agent, tool
from strands.models import BedrockModel

# Uses your AWS_PROFILE / AWS_REGION credentials.
ec2 = boto3.client("ec2")


@tool
def get_security_groups() -> dict:
    """List AWS Security Groups and their inbound rules for a security review."""
    groups = []
    paginator = ec2.get_paginator("describe_security_groups")
    for page in paginator.paginate():
        for sg in page["SecurityGroups"]:
            groups.append({
                "id": sg["GroupId"],
                "name": sg["GroupName"],
                "vpc_id": sg.get("VpcId"),
                "inbound_rules": sg["IpPermissions"],
            })
    return {"security_groups": groups}


model = BedrockModel(
    model_id="us.amazon.nova-lite-v1:0",
    region_name="us-east-1",
)

agent = Agent(
    model=model,
    system_prompt=(
        "You are an AWS Network Security Investigator. "
        "Use the available tool to inspect security groups. "
        "Identify potentially risky inbound rules, explain why, "
        "and recommend improvements. Never modify AWS resources. "
        "Do not claim a host is publicly reachable based only on its security group."
    ),
    tools=[get_security_groups],
)

agent("Review my AWS Security Groups for security risks.")
