#!/bin/bash
set -e

REGION="us-east-2"
CLUSTER_NAME="pwn-ops-utils-cluster"
SERVICE_NAME="pwn-ops-utils-service"

echo "🔄 Restarting ECS service..."
echo "🎯 Cluster: ${CLUSTER_NAME}"
echo "🎯 Service: ${SERVICE_NAME}"
echo ""

# Force new deployment
echo "🚀 Forcing new deployment..."
aws ecs update-service \
  --cluster ${CLUSTER_NAME} \
  --service ${SERVICE_NAME} \
  --force-new-deployment \
  --region ${REGION}

echo ""
echo "✅ Service restart initiated!"
echo "📊 Check status with:"
echo "   aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME} --region ${REGION}"
