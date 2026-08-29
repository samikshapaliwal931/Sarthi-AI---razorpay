#!/bin/bash

# Sarthi Frontend Test Script
# Tests all major flows from login to client interactions

BASE_URL="http://localhost:8080"

echo "🧪 Starting Sarthi Frontend Tests..."
echo "======================================"
echo ""

# Test 1: Landing Page
echo "1️⃣  Testing Landing Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Landing page loads successfully"
else
  echo "   ❌ Landing page failed with status $RESPONSE"
fi

# Test 2: Login Page
echo "2️⃣  Testing Login Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/login")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Login page loads successfully"
else
  echo "   ❌ Login page failed with status $RESPONSE"
fi

# Test 3: Dashboard Page (requires auth in real mode, but works with mock)
echo "3️⃣  Testing Dashboard Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/dashboard")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Dashboard page loads successfully"
else
  echo "   ❌ Dashboard page failed with status $RESPONSE"
fi

# Test 4: Opportunities Page
echo "4️⃣  Testing Opportunities Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/opportunities")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Opportunities page loads successfully"
else
  echo "   ❌ Opportunities page failed with status $RESPONSE"
fi

# Test 5: Products Page
echo "5️⃣  Testing Products Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/products")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Products page loads successfully"
else
  echo "   ❌ Products page failed with status $RESPONSE"
fi

# Test 6: Orders Page
echo "6️⃣  Testing Orders Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/orders")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Orders page loads successfully"
else
  echo "   ❌ Orders page failed with status $RESPONSE"
fi

# Test 7: Customers Page
echo "7️⃣  Testing Customers Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/customers")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Customers page loads successfully"
else
  echo "   ❌ Customers page failed with status $RESPONSE"
fi

# Test 8: AI Copilot Page
echo "8️⃣  Testing AI Copilot Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/ai-copilot")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ AI Copilot page loads successfully"
else
  echo "   ❌ AI Copilot page failed with status $RESPONSE"
fi

# Test 9: Policies Page
echo "9️⃣  Testing Policies Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/policies")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Policies page loads successfully"
else
  echo "   ❌ Policies page failed with status $RESPONSE"
fi

# Test 10: Audit Page
echo "🔟 Testing Audit Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/audit")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Audit page loads successfully"
else
  echo "   ❌ Audit page failed with status $RESPONSE"
fi

# Test 11: Shop (Storefront) Page
echo "1️⃣1️⃣ Testing Shop Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/shop")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Shop page loads successfully"
else
  echo "   ❌ Shop page failed with status $RESPONSE"
fi

# Test 12: Shop Search Page
echo "1️⃣2️⃣ Testing Shop Search Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/shop/search")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Shop search page loads successfully"
else
  echo "   ❌ Shop search page failed with status $RESPONSE"
fi

# Test 13: Analytics Page
echo "1️⃣3️⃣ Testing Analytics Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/analytics")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Analytics page loads successfully"
else
  echo "   ❌ Analytics page failed with status $RESPONSE"
fi

# Test 14: Campaigns Page
echo "1️⃣4️⃣ Testing Campaigns Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/campaigns")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Campaigns page loads successfully"
else
  echo "   ❌ Campaigns page failed with status $RESPONSE"
fi

# Test 15: Agent Activity Page
echo "1️⃣5️⃣ Testing Agent Activity Page..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/agent-activity")
if [ "$RESPONSE" = "200" ]; then
  echo "   ✅ Agent Activity page loads successfully"
else
  echo "   ❌ Agent Activity page failed with status $RESPONSE"
fi

echo ""
echo "======================================"
echo "✅ All tests completed!"
echo ""
echo "📝 Note: Frontend is running in MOCK mode."
echo "   To connect to real backend:"
echo "   1. Start backend: cd Backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "   2. Update .env: VITE_USE_MOCK=false"
echo "   3. Restart frontend: npm run dev"
echo ""
