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
product_id=$(string_field "$body" productId)
printf '%s' "$product_id" | grep -Eq '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'

call GET "/products/$product_id"
[ "$status" = 200 ]
[ "$(string_field "$body" productId)" = "$product_id" ]
[ "$(string_field "$body" name)" = "Wireless Keyboard" ]
[ "$(number_field "$body" price)" = 2499 ]

call PATCH "/products/$product_id" '{"price":2199}'
[ "$status" = 200 ]
[ "$(string_field "$body" productId)" = "$product_id" ]
[ "$(string_field "$body" name)" = "Wireless Keyboard" ]
[ "$(number_field "$body" price)" = 2199 ]

call GET "/products/$product_id"
[ "$status" = 200 ]
[ "$(string_field "$body" name)" = "Wireless Keyboard" ]
[ "$(number_field "$body" price)" = 2199 ]

call DELETE "/products/$product_id"
[ "$status" = 204 ]
[ -z "$body" ]

call GET "/products/$product_id"
[ "$status" = 404 ]
echo "Stateful CRUD lifecycle verified"
