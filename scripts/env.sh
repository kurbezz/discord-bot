#! /usr/bin/env sh

response=`curl -X 'GET' "https://$VAULT_HOST/v1/$VAULT_SECRET_PATH" -s \
  -H 'accept: application/json' \
  -H "X-Vault-Token: $VAULT_TOKEN"`

data=`echo $response | jq -r '.data.data'`

echo "$data" | jq -r 'to_entries[] | "\(.key)=\(.value)"' | while IFS= read -r line; do
    key=$(echo "$line" | cut -d '=' -f 1)
    value=$(echo "$line" | cut -d '=' -f 2-)
    echo "$key=\"$value\""
done
