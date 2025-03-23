# Developer API Usage Documentation

This document provides a detailed guide for developers to interact with the multi-tenant LLM Retrieval-Augmented Generation (RAG) API. The API enables secure document management and query processing in a tenant-isolated environment, built on AWS services like Amazon Cognito, API Gateway, Lambda, OpenSearch Serverless, and Bedrock.

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Add Documents](#add-documents)
   - [Query](#query)
4. [Error Handling](#error-handling)
5. [Additional Notes](#additional-notes)

---

## Introduction

The multi-tenant LLM RAG API allows developers to:
- **Add documents**: Store tenant-specific documents with precomputed vector embeddings.
- **Query**: Retrieve relevant documents based on vector similarity and generate responses using an LLM.

Tenant data is isolated using separate indices in Amazon OpenSearch Serverless, ensuring privacy and security. All requests require authentication via Amazon Cognito using a JWT token.

**Base URL**: `https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod`

---

## Authentication

Authentication is managed through Amazon Cognito. You’ll need a valid JWT token, included in the `Authorization` header of every request.

### Steps to Obtain a JWT Token

1. **Sign Up**: Register a user in the Cognito User Pool with a `tenant_id` and email.
2. **Sign In**: Authenticate via the Cognito Hosted UI or AWS CLI to get an ID token (JWT).

   **Example using AWS CLI**:
   ```bash
   aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id <APP_CLIENT_ID> \
     --auth-parameters USERNAME=<EMAIL>,PASSWORD=<PASSWORD>
   ```

3. **Extract the ID Token**: The response includes an `IdToken`, which is your JWT token.

### Using the Token in Requests

Include the JWT token in the `Authorization` header:
```http
Authorization: Bearer <JWT_TOKEN>
```

**Note**: The JWT token contains a `tenant_id` claim, which the API validates against the `tenantId` in the request path to enforce tenant isolation.

---

## API Endpoints

The API provides two primary endpoints:
1. **Add Documents**: Upload documents to a tenant’s index.
2. **Query**: Retrieve relevant documents based on a vector query.

### Add Documents

- **Endpoint**: `POST /tenants/{tenantId}/documents`
- **Description**: Adds a document to the tenant’s index in OpenSearch Serverless.
- **Path Parameter**:
  - `tenantId`: Unique tenant identifier (e.g., `123`).
- **Request Body**:
  ```json
  {
    "document": {
      "text": "Sample document content",
      "vector": [0.1, 0.2, 0.3, ...]  // Precomputed vector embedding
    }
  }
  ```
  - `text`: The document’s textual content.
  - `vector`: Precomputed vector embedding (dimension must match OpenSearch configuration).
- **Response**:
  - **201 Created**: Document added successfully.
    ```json
    {
      "message": "Document indexed",
      "id": "<DOCUMENT_ID>"
    }
    ```
- **Example**:
  ```bash
  curl -X POST \
    -H "Authorization: Bearer <JWT_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"document": {"text": "Sample document", "vector": [0.1, 0.2, 0.3]}}' \
    https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/tenants/123/documents
  ```

### Query

- **Endpoint**: `POST /tenants/{tenantId}/query`
- **Description**: Queries the tenant’s index to retrieve relevant documents based on a vector.
- **Path Parameter**:
  - `tenantId`: Unique tenant identifier (e.g., `123`).
- **Request Body**:
  ```json
  {
    "vector": [0.1, 0.2, 0.3, ...]  // Query vector embedding
  }
  ```
  - `vector`: Vector embedding of the query (dimension must match OpenSearch configuration).
- **Response**:
  - **200 OK**: Query processed successfully.
    ```json
    {
      "results": [
        {
          "id": "<DOCUMENT_ID>",
          "score": 0.95,
          "document": {
            "text": "Sample document content",
            "vector": [0.1, 0.2, 0.3, ...]
          }
        }
      ]
    }
    ```
- **Example**:
  ```bash
  curl -X POST \
    -H "Authorization: Bearer <JWT_TOKEN>" \
    -H "Content-Type: application/json" \
    -d '{"vector": [0.1, 0.2, 0.3]}' \
    https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/tenants/123/query
  ```

**Note**: The API supports vector-based queries. For text-based queries, consider integrating a separate embedding step or extending the API with an additional parameter.

---

## Error Handling

The API uses standard HTTP status codes to indicate request outcomes. Below are common error responses:

- **400 Bad Request**: Invalid request format or missing parameters.
  ```json
  {
    "error": "Invalid request body"
  }
  ```
- **401 Unauthorized**: Missing or invalid JWT token.
  ```json
  {
    "error": "Unauthorized"
  }
  ```
- **403 Forbidden**: Tenant mismatch between JWT `tenant_id` and request `tenantId`.
  ```json
  {
    "error": "Tenant mismatch"
  }
  ```
- **404 Not Found**: Tenant or resource not found.
  ```json
  {
    "error": "Tenant not found"
  }
  ```
- **500 Internal Server Error**: Unexpected server issue.
  ```json
  {
    "error": "Internal server error"
  }
  ```

**Note**: Additional error codes or messages may occur depending on specific conditions. Handle errors robustly in your application.

---

## Additional Notes

- **Rate Limits**: The API may impose tenant-specific rate limits. Contact the administrator for details.
- **Data Formats**: Vector embeddings must match the dimension used in OpenSearch (e.g., 1536 for some models).
- **Tenant Isolation**: Data is stored in tenant-specific indices (e.g., `tenant_123`), with isolation enforced via JWT validation.
- **Vector Generation**: The API expects precomputed vectors. Use an embedding service (e.g., AWS Bedrock) to generate them prior to API calls.
- **Scalability**: Built on serverless architecture, the API scales automatically to handle multiple tenants and large datasets.
- **Optional Endpoints**: For advanced use cases, consider adding `PUT` (update) or `DELETE` (remove) document endpoints.
