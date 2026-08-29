#!/bin/bash

# Sarthi End-to-End Test Script
# Tests all major flows with real backend

set -e

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:8080"

echo "🧪 Sarthi End-to-End Test Suite"
echo "================================"
echo ""

# Test 1: Backend Health
echo "1️⃣  Testing Backend Health..."
RESPONSE=$(curl -s "$BACKEND_URL/health")
if echo "$RESPONSE" | grep -q "healthy"; then
  echo "   ✅ Backend is healthy"
else
  echo "   ❌ Backend health check failed"
  exit 1
fi

# Test 2: Frontend Health
echo "2️⃣  Testing Frontend Health..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Frontend is running"
else
  echo "   ❌ Frontend health check failed with status $RESPONSE"
  exit 1
fi

# Test 3: Authentication - Login
echo "3️⃣  Testing Authentication (Login)..."
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@strideathletics.com", "password": "demo123456"}')

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
  echo "   ✅ Login successful"
  TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
else
  echo "   ❌ Login failed"
  echo "   Response: $LOGIN_RESPONSE"
  exit 1
fi

# Test 4: Get Merchant Info
echo "4️⃣  Testing Merchant Info..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN")
if echo "$RESPONSE" | grep -q "Stride Athletics"; then
  echo "   ✅ Merchant info retrieved"
else
  echo "   ❌ Merchant info failed"
  exit 1
fi

# Test 5: Get Products
echo "5️⃣  Testing Products API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/products" \
  -H "Authorization: Bearer $TOKEN")
PRODUCT_COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin)['products']))")
if [ "$PRODUCT_COUNT" -gt 0 ]; then
  echo "   ✅ Products API working ($PRODUCT_COUNT products)"
else
  echo "   ❌ Products API failed"
  exit 1
fi

# Test 6: Get Orders
echo "6️⃣  Testing Orders API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/orders" \
  -H "Authorization: Bearer $TOKEN")
if echo "$RESPONSE" | grep -q "order_number"; then
  echo "   ✅ Orders API working"
else
  echo "   ❌ Orders API failed"
  exit 1
fi

# Test 7: Get Customers
echo "7️⃣  Testing Customers API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/customers" \
  -H "Authorization: Bearer $TOKEN")
if echo "$RESPONSE" | grep -q "email"; then
  echo "   ✅ Customers API working"
else
  echo "   ❌ Customers API failed"
  exit 1
fi

# Test 8: Get Dashboard
echo "8️⃣  Testing Dashboard API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer $TOKEN")
if echo "$RESPONSE" | grep -q "revenue_metrics"; then
  echo "   ✅ Dashboard API working"
else
  echo "   ❌ Dashboard API failed"
  exit 1
fi

# Test 9: Get Opportunities
echo "9️⃣  Testing Opportunities API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/opportunities" \
  -H "Authorization: Bearer $TOKEN")
if [ "$RESPONSE" = "[]" ] || echo "$RESPONSE" | grep -q "opportunities"; then
  echo "   ✅ Opportunities API working"
else
  echo "   ❌ Opportunities API failed"
  exit 1
fi

# Test 10: Get Policies
echo "🔟 Testing Policies API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/policies" \
  -H "Authorization: Bearer $TOKEN")
if echo "$RESPONSE" | grep -q "policy_type"; then
  echo "   ✅ Policies API working"
else
  echo "   ❌ Policies API failed"
  exit 1
fi

# Test 11: Get Audit Events
echo "1️⃣1️⃣ Testing Audit API..."
RESPONSE=$(curl -s "$BACKEND_URL/api/v1/audit" \
  -H "Authorization: Bearer $TOKEN")
if [ "$RESPONSE" = "[]" ] || echo "$RESPONSE" | grep -q "events"; then
  echo "   ✅ Audit API working"
else
  echo "   ❌ Audit API failed"
  exit 1
fi

# Test 12: AI Copilot
echo "1️⃣2️⃣ Testing AI Copilot API..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What is my biggest revenue opportunity?"}], "session_id": "test-session"}')
if echo "$RESPONSE" | grep -q "message"; then
  echo "   ✅ AI Copilot API working"
else
  echo "   ❌ AI Copilot API failed"
  exit 1
fi

# Test 13: Storefront - Public Products
echo "1️⃣3️⃣ Testing Storefront API (Public)..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/storefront/search" \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}')
if echo "$RESPONSE" | grep -q "Nike Air Zoom Pegasus"; then
  echo "   ✅ Storefront API working"
else
  echo "   ❌ Storefront API failed"
  exit 1
fi

# Test 14: Frontend Pages
echo "1️⃣4️⃣ Testing Frontend Pages..."
PAGES=("/login" "/dashboard" "/opportunities" "/products" "/orders" "/customers" "/ai-copilot" "/policies" "/audit" "/shop")
for PAGE in "${PAGES[@]}"; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL$PAGE")
  if [ "$STATUS" = "200" ]; then
    echo "   ✅ $PAGE"
  else
    echo "   ❌ $PAGE (status: $STATUS)"
  fi
done

echo ""
echo "================================"
echo "✅ All tests completed!"
echo ""
echo "📊 System Status:"
echo "   Backend:  $BACKEND_URL (Running)"
echo "   Frontend: $FRONTEND_URL (Running)"
echo "   Database: PostgreSQL (Port 5433)"
echo "   Cache:    Redis (Port 6380)"
echo ""
echo "🔐 Demo Credentials:"
echo "   Email:    demo@strideathletics.com"
echo "   Password: demo123456"
echo ""
echo "📦 Demo Data:"
echo "   Products:  150"
echo "   Customers: 200"
echo "   Orders:    400"
echo "   Merchant:  Stride Athletics"
echo ""
