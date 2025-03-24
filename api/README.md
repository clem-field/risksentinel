# Multi-Tenant LLM RAG API

This project provides a serverless, multi-tenant API for Retrieval-Augmented Generation (RAG) using AWS Bedrock. It allows multiple tenants to securely manage and query their own documents, with data isolation enforced through tenant-specific indices in Amazon OpenSearch Serverless. The API is built using AWS services and leverages Infrastructure as Code (IaC) with Terraform for easy deployment and management.

## Architecture

The architecture consists of the following components:

- **Authentication**: Amazon Cognito with JWT tokens and a custom `tenant_id` attribute for tenant isolation.
- **API Layer**: Amazon API Gateway exposing RESTful endpoints for document management and querying.
- **Processing**: AWS Lambda functions handling requests for adding, updating, deleting, and querying documents.
- **Vector Database**: Amazon OpenSearch Serverless with tenant-specific indices (e.g., `tenant_123`) for storing document embeddings.
- **LLM/Embeddings**: AWS Bedrock for generating embeddings and processing queries with large language models.

## Prerequisites

To deploy and use this project, you need:

- An AWS account with access to Cognito, API Gateway, Lambda, OpenSearch Serverless, and Bedrock.
- [Terraform](https://www.terraform.io/downloads.html) installed for provisioning infrastructure.
- Python 3.9+ and `pip` for managing Lambda dependencies.
- AWS CLI configured with appropriate credentials (`aws configure`).

## Deployment Steps

### Infrastructure Setup with Terraform

#### a. OpenSearch Serverless Collection

Create a file named `opensearch.tf`:

```hcl
provider "aws" {
  region = "us-east-1"  # Adjust to your region
}

resource "aws_opensearchserverless_collection" "multi_tenant_rag" {
  name        = "multi-tenant-rag"
  description = "OpenSearch Serverless collection for multi-tenant RAG"
  type        = "VECTORSEARCH"
}

output "collection_endpoint" {
  value = aws_opensearchserverless_collection.multi_tenant_rag.endpoint
}
