#!/bin/sh
set -eu

call() {
  if [ "$#" -eq 3 ]; then
    response=$(curl -sS -X "$1" -H 'Content-Type: application/json' -d "$3" -w '\n%{http_code}' "http://127.0.0.1:9100$2")
  else
    response=$(curl -sS -X "$1" -w '\n%{http_code}' "http://127.0.0.1:9100$2")
  fi
  body=$(printf '%s\n' "$response" | sed '$d')
  status=$(printf '%s\n' "$response" | tail -n 1)
}
string_field() { printf '%s' "$1" | sed -n "s/.*\"$2\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p"; }
number_field() { printf '%s' "$1" | sed -n "s/.*\"$2\"[[:space:]]*:[[:space:]]*\([-0-9.]*\).*/\1/p"; }

call POST /products '{"name":"Wireless Keyboard","price":2499}'
[ "$status" = 201 ]
created_id=$(string_field "$body" productId)
created_name=$(string_field "$body" name)
created_price=$(number_field "$body" price)
printf '%s' "$created_id" | grep -Eq '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'

call GET "/products/$created_id"
[ "$status" = 200 ] || [ "$status" = 404 ]
if [ "$status" = 200 ] &&
   [ "$(string_field "$body" productId)" = "$created_id" ] &&
   [ "$(string_field "$body" name)" = "$created_name" ] &&
   [ "$(number_field "$body" price)" = "$created_price" ]; then
  echo "Regular mock unexpectedly preserved the Product" >&2
  exit 1
fi
echo "Stateless behavior verified"
