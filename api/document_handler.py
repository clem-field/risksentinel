import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    """
    AWS Lambda handler to manage tenant documents in OpenSearch Serverless.
    Handles POST (add), PUT (update), and DELETE (delete specific/all) requests.
    
    Args:
        event (dict): The Lambda event object containing HTTP method, path parameters, and body.
        context (object): The Lambda context object (unused in this function).
    
    Returns:
        dict: A response with statusCode and body in JSON format.
    """
    # Extract HTTP method and path parameters
    http_method = event['httpMethod']
    path_parameters = event.get('pathParameters', {})
    tenant_id = path_parameters.get('tenantId')
    document_id = path_parameters.get('documentId')
    
    # Extract tenant_id from JWT token for tenant isolation
    claims = event['requestContext']['authorizer']['claims']
    if claims['custom:tenant_id'] != tenant_id:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': 'Tenant mismatch'})
        }
    
    # Set up OpenSearch client
    host = 'your-opensearch-domain-endpoint'  # Replace with your OpenSearch Serverless endpoint
    region = 'us-east-1'  # Replace with your AWS region
    service = 'aoss'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(
        credentials.access_key,
        credentials.secret_key,
        region,
        service,
        session_token=credentials.token
    )
    client = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    
    # Define the tenant-specific index name
    index_name = f'tenant_{tenant_id}'
    
    # Handle POST request: Add a new document
    if http_method == 'POST' and not document_id:
        body = json.loads(event['body'])
        document = body['document']
        response = client.index(index=index_name, body=document)
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Document indexed',
                'id': response['_id']
            })
        }
    
    # Handle PUT request: Update an existing document
    elif http_method == 'PUT' and document_id:
        if not client.exists(index=index_name, id=document_id):
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
        body = json.loads(event['body'])
        document = body['document']
        response = client.index(index=index_name, id=document_id, body=document)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document updated',
                'id': response['_id']
            })
        }
    
    # Handle DELETE request with documentId: Delete a specific document
    elif http_method == 'DELETE' and document_id:
        if not client.exists(index=index_name, id=document_id):
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Document not found'})
            }
        client.delete(index=index_name, id=document_id)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Document deleted',
                'id': document_id
            })
        }
    
    # Handle DELETE request without documentId: Delete all documents for the tenant
    elif http_method == 'DELETE' and not document_id:
        if not client.indices.exists(index=index_name):
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'No documents to delete'})
            }
        query = {"query": {"match_all": {}}}
        response = client.delete_by_query(index=index_name, body=query)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'All documents deleted',
                'deleted': response['deleted']
            })
        }
    
    # Handle invalid requests
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid request'})
        }
