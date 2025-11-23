# API Setup Guide

This guide explains how to obtain API credentials for eBay, Amazon, and Etsy.

## eBay API Setup

### 1. Create Developer Account

1. Go to https://developer.ebay.com/
2. Sign in with your eBay account or create a new one
3. Navigate to "My Account" → "Keys"

### 2. Create Application Keys

1. Click "Create an Application Key"
2. Fill in application details:
   - Application Title: "Fisher" (or your preferred name)
   - Application Purpose: Select appropriate category
3. Accept the API License Agreement
4. Click "Create"

### 3. Get Credentials

You'll receive:
- **App ID (Client ID)**: Your application identifier
- **Dev ID**: Developer ID
- **Cert ID (Client Secret)**: Certificate ID

### 4. Add to .env

```env
EBAY_APP_ID=YourAppId
EBAY_CERT_ID=YourCertId
EBAY_DEV_ID=YourDevId
EBAY_ENVIRONMENT=production
```

For testing, use `EBAY_ENVIRONMENT=sandbox`

### Rate Limits

- **Sandbox**: 5,000 calls/day
- **Production**: 5,000 calls/day (can request increase)

### Documentation

- [eBay Developer Program](https://developer.ebay.com/develop/get-started)
- [Finding API](https://developer.ebay.com/DevZone/finding/Concepts/MakingACall.html)

---

## Amazon Product Advertising API Setup

### 1. Create Amazon Associates Account

1. Go to https://affiliate-program.amazon.com/
2. Sign up for Amazon Associates program
3. Complete the application process

### 2. Get PA-API Access

1. Once approved, log in to Associates Central
2. Navigate to "Tools" → "Product Advertising API"
3. Request access to PA-API 5.0
4. Wait for approval (may take 1-2 business days)

### 3. Create Access Keys

1. Go to AWS IAM Console: https://console.aws.amazon.com/iam/
2. Create a new IAM user for API access
3. Attach the "ProductAdvertisingAPIFullAccess" policy
4. Generate access keys

### 4. Get Credentials

You'll need:
- **Access Key ID**: AWS access key
- **Secret Access Key**: AWS secret key
- **Partner Tag (Associate ID)**: From Associates Central

### 5. Add to .env

```env
AMAZON_ACCESS_KEY=YourAccessKey
AMAZON_SECRET_KEY=YourSecretKey
AMAZON_PARTNER_TAG=YourPartnerTag-20
AMAZON_REGION=us-east-1
```

### Rate Limits

- Based on revenue generated (typically 1-10 requests/second)
- Free tier: 8,640 requests/day

### Documentation

- [PA-API 5.0 Documentation](https://webservices.amazon.com/paapi5/documentation/)
- [Getting Started Guide](https://webservices.amazon.com/paapi5/documentation/quick-start.html)

### Important Notes

- You must maintain an active Associates account
- Link to Amazon products drives eligibility
- PA-API requires AWS Signature V4 authentication

---

## Etsy API Setup

### 1. Create Etsy Account

1. Go to https://www.etsy.com/
2. Create an account if you don't have one

### 2. Register as Developer

1. Go to https://www.etsy.com/developers/
2. Click "Register as a Developer"
3. Accept the API Terms of Use

### 3. Create an App

1. Navigate to "Your Apps" → "Create a New App"
2. Fill in application details:
   - App Name: "Fisher"
   - App Description: Product analysis tool
   - Purpose: Research/Analytics
3. Submit application

### 4. Get API Key

After approval, you'll receive:
- **Keystring (API Key)**: Your application key
- **Shared Secret**: For OAuth authentication

### 5. Add to .env

```env
ETSY_API_KEY=YourApiKey
ETSY_SHARED_SECRET=YourSharedSecret
```

### Rate Limits

- **10,000 requests/day** per application
- No more than 10 requests/second

### API Versions

Fisher uses Etsy API v3. Make sure your app is configured for v3.

### Documentation

- [Etsy Developer Documentation](https://developers.etsy.com/documentation)
- [API v3 Reference](https://developers.etsy.com/documentation/reference)

### Important Notes

- Some endpoints require OAuth 2.0 authentication
- Read-only operations (like search) work with API key only
- Write operations need full OAuth flow

---

## Testing Your Configuration

After setting up your API credentials, test them with:

```bash
python -m fisher status
```

This will show which marketplaces are properly configured:

```
Marketplace API Status
┌─────────────┬─────────────────────┬─────────────┐
│ Marketplace │ Status              │ Details     │
├─────────────┼─────────────────────┼─────────────┤
│ EBAY        │ Configured ✓        │ App ID: ✓   │
│ AMAZON      │ Configured ✓        │ Access Key: ✓│
│ ETSY        │ Not Configured ✗    │ API Key: ✗  │
└─────────────┴─────────────────────┴─────────────┘
```

## Security Best Practices

1. **Never commit .env file**: Already in .gitignore
2. **Use environment variables**: In production, use proper secret management
3. **Rotate keys regularly**: Update API keys periodically
4. **Limit permissions**: Only grant necessary API access
5. **Monitor usage**: Track API calls to avoid exceeding limits

## Troubleshooting

### eBay

**Error: "Invalid App ID"**
- Verify App ID is correct
- Check environment (sandbox vs production)
- Ensure app is active in developer portal

### Amazon

**Error: "Authentication failed"**
- Verify Access Key and Secret Key
- Check Partner Tag format (should end with -20)
- Ensure IAM user has PA-API permissions
- Verify Associates account is active

### Etsy

**Error: "Invalid API key"**
- Check API key is for API v3
- Verify app is approved and active
- Ensure keystring is copied correctly

## Getting Help

- **eBay**: https://developer.ebay.com/support
- **Amazon**: https://webservices.amazon.com/paapi5/support
- **Etsy**: https://www.etsy.com/developers/support

## Cost Considerations

- **eBay**: Free (with rate limits)
- **Amazon**: Free tier available, paid tiers based on revenue
- **Etsy**: Free (with rate limits)

All APIs have free tiers suitable for research and analysis purposes.
