# Registration Guide

## Prerequisites

- Compliance tests all passing (`pytest tests/test_compliance.py -v`)
- Your app deployed at a public HTTPS URL

## Steps

### 1. Deploy your app

**Railway (recommended — free tier available):**
1. Push your repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub Repo
3. Add environment variable: `DPW_API_KEY=<a secret you choose>`
4. Railway auto-detects the Dockerfile and deploys
5. Your app URL: `https://your-app.up.railway.app`

**Any other host:** Fly.io, Render, AWS, GCP, Azure — any public HTTPS endpoint works.

### 2. Verify your deployed app

```bash
# Health check
curl https://your-app.up.railway.app/health

# Test invoke (should return 401 with wrong key)
curl -X POST https://your-app.up.railway.app/invoke \
  -H "x-api-key: wrong-key" \
  -H "Content-Type: application/json" \
  -d '{"case_id":"test","state_code":"PA","layer_id":1,...}'
```

### 3. Register on the DPW Developer Portal

1. Go to https://portal-production-162a.up.railway.app
2. Click **Create Account** — fill in your name, email, organization
3. **Save your API key** — it's shown once and stored in your account

### 4. Register your app

1. Sign in → **My Apps** → **Register New App**
2. Fill in:
   - **Layer**: select your layer number (1–11)
   - **States**: which US states your app covers (e.g. PA, CA, TX)
   - **Endpoint URL**: your app's base URL (e.g. `https://your-app.up.railway.app`)
   - **App API Key**: the `DPW_API_KEY` value you set in your deployment environment
3. Submit

### 5. Wait for activation

Your app status will be **PENDING** while DPW reviews it. Once **ACTIVE**, your app receives
live traffic routed from the platform for the layers and states you registered.

## What Happens After Activation

The platform calls `POST {your_endpoint_url}/invoke` with a JSON body matching your layer's
request schema. Your app responds with the appropriate response. The platform logs the
`CaseEvent` and returns the response to the caller.

## Registering for Multiple States

You can register the same app for multiple states in one registration, or create separate
registrations per state for state-specific deployments. The `state_code` in every request
tells your app which state's rules to apply.

## Updating Your App

Contract changes don't require re-registration as long as your app remains compliant.
If you change your endpoint URL, update it in **My Apps**.
