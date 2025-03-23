provider "aws" {
  region = "us-east-1"  # Replace with your desired AWS region
}

resource "aws_opensearchserverless_collection" "multi_tenant_rag" {
  name        = "multi-tenant-rag"
  description = "OpenSearch Serverless collection for multi-tenant RAG"
  type        = "VECTORSEARCH"
}

output "collection_endpoint" {
  value = aws_opensearchserverless_collection.multi_tenant_rag.endpoint
}
