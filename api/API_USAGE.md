# API Usage Documentation

This document provides detailed instructions for interacting with the multi-tenant LLM Retrieval-Augmented Generation (RAG) API. The API enables secure document management and querying in a tenant-isolated environment, leveraging AWS services such as Amazon Cognito, API Gateway, Lambda, OpenSearch Serverless, and Bedrock.

## Table of Contents
1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Add Document](#add-document)
   - [Update Document](#update-document)
   - [Delete Document](#delete-document)
   - [Delete All Documents](#delete-all-documents)
   - [Query](#query)
4. [Error Handling](#error-handling)
5. [Additional Notes](#additional-notes)

---

## Introduction

The multi-tenant LLM RAG API allows developers to:
- **Manage documents**: Add, update, or delete tenant-specific documents with precomputed vector embeddings.
- **Query**: Retrieve relevant documents based on vector similarity for use in RAG systems.

Each tenant’s data is stored in a separate index in Amazon OpenSearch Serverless (e.g., `tenant_123`), ensuring isolation and security. All API requests require authentication via Amazon Cognito using a JWT token.

**Base URL**: `https://<API_ID>.execute-api.<REGION>.amazonaws.com/prod`

---

## Authentication

Authentication is handled through Amazon Cognito. A valid JWT token must be included in the `Authorization` header of every request.

### Obtaining a JWT Token

1. **Sign Up**: Register a user in the Cognito User Pool with a `tenant_id` (custom attribute) and email.
2. **Sign In**: Authenticate using the Cognito Hosted UI or AWS CLI to obtain an ID token (JWT).

   **Example using AWS CLI**:
   ```bash
   aws cognito-idp initiate-auth \
     --auth-flow USER_PASSWORD_AUTH \
     --client-id <APP_CLIENT_ID> \
     --auth-parameters USERNAME=<EMAIL>,PASSWORD=<PASSWORD>
