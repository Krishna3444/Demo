#!/usr/bin/env bash
# Smoke test for the Dhaniti FastAPI backend.
# Usage: bash tests/smoke.sh [base_url]   (default http://localhost:5000)
set -u
BASE="${1:-${SMOKE_BASE_URL:-http://localhost:5000}}"
PASS=0; FAIL=0

check() { # name expected_status actual_status [extra]
  if [ "$2" = "$3" ]; then echo "PASS: $1 ($3)"; PASS=$((PASS+1));
  else echo "FAIL: $1 (expected $2, got $3) ${4:-}"; FAIL=$((FAIL+1)); fi
}

echo "=== 1. Auth: protected endpoints without token ==="
check "kpis unauthenticated → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' $BASE/api/kpis)"
check "applications unauthenticated → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' $BASE/api/applications)"

echo "=== 2. Login flows ==="
check "valid admin login → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@dhaniti.ai","password":"DhanitiAdmin@123"}')"
check "wrong password → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@dhaniti.ai","password":"wrong"}')"
check "unknown user → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"email":"nobody@x.com","password":"whatever1"}')"
check "missing fields → 422" 422 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{}')"

TOKEN=$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"email":"admin@dhaniti.ai","password":"DhanitiAdmin@123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
AUTH="Authorization: Bearer $TOKEN"
check "me → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/auth/me)"
check "invalid token → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer garbage.token.here' $BASE/api/auth/me)"

echo "=== 3. Analytics (existing functionality preserved) ==="
check "kpis → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/kpis)"
check "charts → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/charts)"
check "insights → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/insights)"
check "data-quality → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/data-quality)"
check "filters → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/filters)"
COUNT=$(curl -s -H "$AUTH" "$BASE/api/applications" | python3 -c "import sys,json;print(json.load(sys.stdin)['count'])")
check "applications count = 151" 151 "$COUNT"

echo "=== 4. CRUD ==="
CREATE_RESP=$(curl -s -X POST $BASE/api/applications -H "$AUTH" -H 'Content-Type: application/json' -d '{
  "studentName":"Smoke Test Student","age":21,"studentState":"Karnataka",
  "institutionId":"INS001","courseId":"CRS001",
  "loanAmountRequestedInr":1500000,"parentMonthlyIncomeInr":120000,
  "existingMonthlyObligationsInr":15000,"creditScore":720,
  "employmentType":"Salaried","applicationChannel":"Website"}')
NEW_ID=$(echo "$CREATE_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
check "create application → EDU1152" "EDU1152" "$NEW_ID"
check "get created → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/applications/$NEW_ID)"
check "get missing → 404" 404 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/applications/EDU9999)"
check "patch status → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X PATCH $BASE/api/applications/$NEW_ID -H "$AUTH" -H 'Content-Type: application/json' -d '{"applicationStatus":"Approved"}')"
check "put update → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X PUT $BASE/api/applications/$NEW_ID -H "$AUTH" -H 'Content-Type: application/json' -d '{"studentName":"Smoke Test Student II","creditScore":770}')"
check "invalid create → 422" 422 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/applications -H "$AUTH" -H 'Content-Type: application/json' -d '{"studentName":"x"}')"
check "delete → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $BASE/api/applications/$NEW_ID -H "$AUTH")"
check "delete again → 404" 404 "$(curl -s -o /dev/null -w '%{http_code}' -X DELETE $BASE/api/applications/$NEW_ID -H "$AUTH")"

echo "=== 5. RBAC (analyst read-only) ==="
ANALYST_TOKEN=$(curl -s -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{"email":"analyst@dhaniti.ai","password":"Analyst@123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
A_AUTH="Authorization: Bearer $ANALYST_TOKEN"
check "analyst can read → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -H "$A_AUTH" $BASE/api/applications)"
check "analyst cannot create → 403" 403 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/applications -H "$A_AUTH" -H 'Content-Type: application/json' -d '{"studentName":"Blocked Guy","age":22,"studentState":"Goa","institutionId":"INS001","courseId":"CRS001","loanAmountRequestedInr":100000,"parentMonthlyIncomeInr":50000,"existingMonthlyObligationsInr":5000,"employmentType":"Salaried","applicationChannel":"Website"}')"

echo "=== 6. OTP flow (login via code, outbox transport) ==="
rm -f logs/emails/*.eml 2>/dev/null
SEND_RESP=$(curl -s -X POST $BASE/api/auth/send-otp -H 'Content-Type: application/json' -d '{"email":"admin@dhaniti.ai","purpose":"login"}')
echo "  send-otp response: $SEND_RESP"
sleep 1
OTP_CODE=$(ls -t logs/emails/*.eml 2>/dev/null | head -1 | xargs cat 2>/dev/null | grep -oE '[0-9]{6}' | head -1)
check "OTP code delivered to outbox" "6" "${#OTP_CODE}"
check "wrong OTP → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/verify-otp -H 'Content-Type: application/json' -d "{\"email\":\"admin@dhaniti.ai\",\"code\":\"000000\",\"purpose\":\"login\"}")"
check "OTP reuse blocked → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/verify-otp -H 'Content-Type: application/json' -d "{\"email\":\"admin@dhaniti.ai\",\"code\":\"000000\",\"purpose\":\"login\"}")"
OTP_LOGIN=$(curl -s -X POST $BASE/api/auth/verify-otp -H 'Content-Type: application/json' -d "{\"email\":\"admin@dhaniti.ai\",\"code\":\"$OTP_CODE\",\"purpose\":\"login\"}")
OTP_TOKEN=$(echo "$OTP_LOGIN" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('token',''))" 2>/dev/null)
if [ -n "$OTP_TOKEN" ] && [ "$OTP_TOKEN" != "" ]; then echo "PASS: OTP login returns token"; PASS=$((PASS+1)); else echo "FAIL: OTP login: $OTP_LOGIN"; FAIL=$((FAIL+1)); fi
check "OTP reuse after success → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/verify-otp -H 'Content-Type: application/json' -d "{\"email\":\"admin@dhaniti.ai\",\"code\":\"$OTP_CODE\",\"purpose\":\"login\"}")"

echo "=== 7. Logout revocation ==="
check "logout → 200" 200 "$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/api/auth/logout -H "$AUTH")"
check "token revoked after logout → 401" 401 "$(curl -s -o /dev/null -w '%{http_code}' -H "$AUTH" $BASE/api/auth/me)"

echo "=== 8. OAuth unconfigured ==="
check "google unconfigured → 503" 503 "$(curl -s -o /dev/null -w '%{http_code}' $BASE/auth/google)"

echo ""
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" = "0" ] && echo "ALL SMOKE TESTS PASSED" || echo "SOME TESTS FAILED"
