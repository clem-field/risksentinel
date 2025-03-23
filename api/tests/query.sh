curl -X POST \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"vector": [0.1, 0.2, ...]}' \
  https://<API_ID>.execute-api.us-east-1.amazonaws.com/prod/tenants/123/query
