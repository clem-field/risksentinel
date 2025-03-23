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
    # Extract tenant_id from Cognito JWT
    tenant_id = event['requestContext']['authorizer']['claims']['custom:tenant_id']
    index_name = f'tenant_{tenant_id}'
    
    # Parse query and vector from event body
    body = json.loads(event['body'])
    query_vector = body['vector']  # Assumed to be the query embedding from Bedrock
    
    # Perform vector similarity search
    search_body = {
        'query': {
            'knn': {
                'vector_field': {
                    'vector': query_vector,
                    'k': 5  # Number of nearest neighbors
                }
            }
        }
    }
    
    response = client.search(
        index=index_name,
        body=search_body
    )
    
    hits = response['hits']['hits']
    results = [{'id': hit['_id'], 'score': hit['_score'], 'document': hit['_source']} for hit in hits]
    
    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }
