#!/bin/bash

# Build script for Docker image with Fargate compatibility
# This script builds the Docker image with linux/amd64 platform for AWS Fargate

set -e

# Configuration
IMAGE_NAME="pwn-ops-utils"
TAG=${1:-latest}
REGISTRY=${2:-"441336784271.dkr.ecr.us-east-2.amazonaws.com/pwn-ops-utils"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Building Docker image for Fargate compatibility...${NC}"

# Build the Docker image with linux/amd64 platform
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${TAG}${NC}"
docker build \
    --platform linux/amd64 \
    --tag ${IMAGE_NAME}:${TAG} \
    --file ../Dockerfile \
    ../

# If registry is provided, tag for registry
if [ ! -z "$REGISTRY" ]; then
    REGISTRY_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
    echo -e "${YELLOW}Tagging for registry: ${REGISTRY_IMAGE}${NC}"
    docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY_IMAGE}
    
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo -e "${GREEN}Local image: ${IMAGE_NAME}:${TAG}${NC}"
    echo -e "${GREEN}Registry image: ${REGISTRY_IMAGE}${NC}"
    echo ""
    echo -e "${YELLOW}To push to registry, run:${NC}"
    echo -e "docker push ${REGISTRY_IMAGE}"
else
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo -e "${GREEN}Image: ${IMAGE_NAME}:${TAG}${NC}"
fi

echo -e "${YELLOW}Image is ready for AWS Fargate deployment.${NC}"
