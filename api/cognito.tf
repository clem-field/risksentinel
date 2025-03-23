resource "aws_cognito_user_pool" "multi_tenant_rag_pool" {
  name = "MultiTenantRAGPool"

  # Allow users to sign in with their email
  username_attributes = ["email"]

  # Define a custom attribute for tenant_id
  schema {
    name                = "tenant_id"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  # Define the standard email attribute
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
  }

  # Enforce a secure password policy
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

  # Specify attributes the app client can read and write
  read_attributes  = ["email", "custom:tenant_id"]
  write_attributes = ["email", "custom:tenant_id"]

  # Disable client secret for simplicity
  generate_secret = false

  # Configure OAuth settings (customize as needed)
  allowed_oauth_flows  = ["code", "implicit"]
  allowed_oauth_scopes = ["email", "openid", "profile"]
  callback_urls        = ["https://your-app.com/callback"]  # Replace with your app's callback URL
}
