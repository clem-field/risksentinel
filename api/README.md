# Multi-Tenant LLM RAG API with AWS Bedrock and OpenSearch Serverless

This project implements a serverless, multi-tenant API for private LLM Retrieval-Augmented Generation (RAG) using AWS Bedrock and Amazon OpenSearch Serverless. It ensures secure, isolated access to LLM capabilities for multiple tenants.

## Architecture

- **Authentication**: Amazon Cognito with a custom `tenant_id` attribute in JWT tokens for tenant isolation.
- **API**: Amazon API Gateway with the following endpoints:
  - `POST /tenants/{tenantId}/query`: Submits a query and retrieves a response.
  - `POST /tenants/{tenantId}/documents`: Adds documents to the tenant’s index.
- **Processing**: AWS Lambda functions:
  - `query_handler`: Processes queries using OpenSearch Serverless and Bedrock.
  - `document_handler`: Adds documents by generating embeddings and storing them.
- **Vector Database**: Amazon OpenSearch Serverless with a single collection and tenant-specific indices (e.g., `tenant_123`).
- **LLM/Embeddings**: AWS Bedrock for embeddings (Titan Text Embeddings) and LLM responses (Anthropic Claude).

## Prerequisites

- An AWS account with access to Cognito, API Gateway, Lambda, OpenSearch Serverless, and Bedrock.
- [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) installed for IaC deployment.
- Python 3.9+ and `pip` for Lambda dependencies.
- AWS CLI configured with credentials (`aws configure`).

## Deployment Steps

### 1. Set Up Amazon OpenSearch Serverless Using Terraform

1. **Create a Terraform File** (`main.tf`):
   ```hcl
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
   ```

2. **Initialize Terraform**:
   ```bash
   terraform init
   ```

3. **Plan the Deployment**:
   ```bash
   terraform plan
   ```

4. **Apply the Configuration**:
   ```bash
   terraform apply
   ```
   - Type `yes` to confirm the deployment.

5. **Retrieve the Endpoint**:
   - After deployment, note the `collection_endpoint` from the output (e.g., `multi-tenant-rag.aoss.us-east-1.amazonaws.com`). This will be used in Lambda configuration.

### 2. Set Up Amazon Cognito Using Terraform

1. **Create a Terraform File** (`cognito.tf`):
   ```hcl
   resource "aws_cognito_user_pool" "multi_tenant_rag_pool" {
     name = "MultiTenantRAGPool"

     username_attributes = ["email"]

     schema {
       name                = "tenant_id"
       attribute_data_type = "String"
       mutable             = true
       required            = false
     }

     schema {
       name                = "email"
       attribute_data_type = "String"
       mutable             = true
       required            = true
     }

     password_policy {
       minimum_length    = 8
       require_lowercase = true
       require_numbers   = true
       require_symbols   = true
       require_uppercase = true
     }
   }

   resource "aws_cognito_user_pool_client" "app_client" {
     name         = "MultiTenantRAGAppClient"
     user_pool_id = aws_cognito_user_pool.multi_tenant_rag_pool.id

     read_attributes  = ["email", "custom:tenant_id"]
     write_attributes = ["email", "custom:tenant_id"]

     generate_secret = false

     allowed_oauth_flows  = ["code", "implicit"]
     allowed_oauth_scopes = ["email", "openid", "profile"]
     callback_urls        = ["https://your-app.com/callback"]  # Replace with your app's callback URL
   }
   ```

2. **Initialize Terraform** (if not already done):
   ```bash
   terraform init
   ```

3. **Plan the Deployment**:
   ```bash
   terraform plan
   ```

4. **Apply the Configuration**:
   ```bash
   terraform apply
   ```
   - Type `yes` to confirm.

5. **Retrieve User Pool and Client IDs**:
   - Note the User Pool ID and App Client ID from the Terraform output or the AWS Management Console. These will be used for API Gateway authentication.

### 3. Set Up AWS Lambda Functions

1. **Create Functions**:
   - In the AWS Lambda console, create two functions: `query_handler` and `document_handler` using Python 3.9+.
   - Set the timeout to 30 seconds for both.

2. **Package Code**:
   - Install Python dependencies in a local directory:
     ```bash
     pip install -r requirements.txt -t ./package
     ```
   - Copy `query_handler.py` and `document_handler.py` into the `package` directory.
   - Create a ZIP file:
     ```bash
     zip -r lambda_package.zip package/
     ```

3. **Upload Code**:
   - Upload `lambda_package.zip` to both Lambda functions via the AWS console or CLI.

4. **Set Environment Variables**:
   - Add the following environment variables to both functions:
     - `OPENSEARCH_HOST`: The collection endpoint from Step 1 (e.g., `multi-tenant-rag.aoss.us-east-1.amazonaws.com`).
     - `REGION`: Your AWS region (e.g., `us-east-1`).

5. **Attach IAM Role**:
   - Create an IAM role for Lambda with the following policies:
     - `AmazonBedrockFullAccess`
     - `AmazonOpenSearchServiceServerlessFullAccess`
     - `AWSLambdaBasicExecutionRole`
   - Attach this role to both Lambda functions.

### 4. Set Up Amazon API Gateway

1. **Create a REST API**:
   - In the API Gateway console, create a new REST API named `RAGAPI`.

2. **Define Resources**:
   - Create a resource `/tenants` and a sub-resource `/{tenantId}` (enable proxy integration).
   - Add two POST methods under `/{tenantId}`:
     - `/query` (integrated with `query_handler` Lambda).
     - `/documents` (integrated with `document_handler` Lambda).

3. **Set Up Authorizer**:
   - Create a Cognito authorizer using the User Pool from Step 2.
   - Apply this authorizer to both POST methods to enforce JWT-based authentication.

4. **Deploy API**:
   - Deploy the API to a stage (e.g., `prod`).
   - Note the invoke URL (e.g., `https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod`).

### 5. Test the API

1. **Sign Up a User**:
   - Use the Cognito Hosted UI or AWS CLI to sign up a user with a `tenant_id` (e.g., `123`) and email.

2. **Get JWT Token**:
   - Authenticate the user to obtain an ID token (JWT) from Cognito.

3. **Test Endpoints**:
   - **Add Documents**:
     ```bash
     curl -X POST \
       -H "Authorization: Bearer <JWT_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{"document": {"text": "Sample document", "vector": [0.1, 0.2, 0.3]}}' \
       https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/tenants/123/documents
     ```
   - **Query**:
     ```bash
     curl -X POST \
       -H "Authorization: Bearer <JWT_TOKEN>" \
       -H "Content-Type: application/json" \
       -d '{"vector": [0.1, 0.2, 0.3]}' \
       https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/tenants/123/query
     ```

## Program Files

- `query_handler.py`: Contains the logic for processing queries using OpenSearch and Bedrock.
- `document_handler.py`: Handles document uploads, generating embeddings, and storing them in OpenSearch.
- `requirements.txt`: Lists Python dependencies for Lambda functions (e.g., `boto3`, `requests`).

## Notes

- **OpenSearch**: Tenant-specific indices (e.g., `tenant_123`) are created dynamically within the single OpenSearch Serverless collection.
- **Security**: Ensure IAM roles are scoped tightly to prevent unauthorized access.
- **Customization**: Modify Bedrock model IDs (e.g., Titan or Claude) and Cognito OAuth settings based on your requirements.
