#!/bin/bash

# Build script for Docker image with Fargate compatibility
# This script builds the Docker image with linux/amd64 platform for AWS Fargate

set -e

# Configuration
IMAGE_NAME="pwn-ops-utils"
REGISTRY="441336784271.dkr.ecr.us-east-2.amazonaws.com"
REGION="us-east-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Docker image for Fargate compatibility...${NC}"

# Build the Docker image with linux/amd64 platform
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:latest${NC}"
docker build \
    --platform linux/amd64 \
    --tag ${IMAGE_NAME}:latest \
    --file Dockerfile \
    .

# Tag for registry
REGISTRY_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"
echo -e "${YELLOW}Tagging for registry: ${REGISTRY_IMAGE}${NC}"
docker tag ${IMAGE_NAME}:latest ${REGISTRY_IMAGE}

# Authenticate with ECR and push
echo -e "${YELLOW}Authenticating with ECR...${NC}"
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${REGISTRY}

echo -e "${YELLOW}Pushing image to ECR...${NC}"
docker push ${REGISTRY_IMAGE}

echo -e "${GREEN}Build and push completed successfully!${NC}"
echo -e "${GREEN}Registry image: ${REGISTRY_IMAGE}${NC}"
echo -e "${YELLOW}Image is ready for AWS Fargate deployment.${NC}"
