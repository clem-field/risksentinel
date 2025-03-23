bedrock_client = boto3.client('bedrock')
response = bedrock_client.invoke_model(
    modelId='your-model-id',
    body=json.dumps({'prompt': 'Answer based on this context', 'context': results})
)
