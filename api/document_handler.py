import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection

client = OpenSearch(
    hosts=[{'host': '<collection-endpoint>', 'port': 443}],
    http_auth=boto3.Session().get_credentials(),
    use_ssl=True,
    connection_class=RequestsHttpConnection
)

def lambda_handler(event, context):
    # Extract tenant_id from Cognito JWT (passed via API Gateway)
    tenant_id = event['requestContext']['authorizer']['claims']['custom:tenant_id']
    index_name = f'tenant_{tenant_id}'
    
    # Parse document from event body
    body = json.loads(event['body'])
    document = body['document']
    
    # Add tenant_id to document for consistency (optional)
    document['tenant_id'] = tenant_id
    
    # Index the document with vector embedding (assumed precomputed)
    response = client.index(
        index=index_name,
        body=document
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Document indexed', 'id': response['_id']})
    }
