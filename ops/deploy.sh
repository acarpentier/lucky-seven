#!/bin/bash

# CloudFormation deployment script for pwn-ops-utils
set -e

STACK_NAME="pwn-ops-utils"
REGION="us-east-2"
TEMPLATE_FILE="cloudformation.yaml"
ENVIRONMENT="prod"

echo "Deploying CloudFormation stack: $STACK_NAME"
echo "Region: $REGION"
echo "Environment: $ENVIRONMENT"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found"
    exit 1
fi

# Deploy the stack
echo "Deploying stack..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --parameter-overrides Environment="$ENVIRONMENT" \
    --capabilities CAPABILITY_IAM \
    --tags Project=pwn-ops-utils Environment="$ENVIRONMENT"

echo "Stack deployment completed!"

# Get stack outputs
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output table

echo "Deployment finished successfully!"
