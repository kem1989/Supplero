# External APIs Setup Guide

This guide explains how to configure external APIs for enhanced supplier risk assessment in Supplero.

## Overview

The external data aggregation service integrates with several public APIs to provide comprehensive supplier risk signals:

- **News APIs**: For real-time news sentiment analysis and risk detection
- **Financial Data APIs**: For company financial health indicators
- **Industry Risk APIs**: For sector-specific risk factors

## Required Environment Variables

Add these to your `.env` file:

```bash
# News API (https://newsapi.org/)
NEWS_API_KEY=your_news_api_key_here

# Dun & Bradstreet (https://www.dnb.com/)
DUN_BRADSTREET_API_KEY=your_dnb_api_key_here

# Refinitiv (https://developers.refinitiv.com/)
REFINITIV_API_KEY=your_refinitiv_api_key_here
```

## API Setup Instructions

### 1. News API (Recommended - Free Tier Available)

1. Visit [https://newsapi.org/](https://newsapi.org/)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Add to `.env`: `NEWS_API_KEY=your_key_here`

**Free Tier Limits:**
- 1,000 requests per day
- Basic news search and sentiment analysis
- Perfect for development and testing

**Paid Plans:**
- Developer: $449/month - 10,000 requests/day
- Business: $1,999/month - 100,000 requests/day

### 2. Dun & Bradstreet (Enterprise)

1. Contact Dun & Bradstreet sales team
2. Request API access for supplier risk assessment
3. Get API credentials and documentation
4. Add to `.env`: `DUN_BRADSTREET_API_KEY=your_key_here`

**Features:**
- Company financial health scores
- Credit ratings and risk indicators
- Industry benchmarking data
- Compliance and regulatory information

### 3. Refinitiv (Enterprise)

1. Contact Refinitiv sales team
2. Request API access for financial data
3. Get API credentials and documentation
4. Add to `.env`: `REFINITIV_API_KEY=your_key_here`

**Features:**
- Real-time financial market data
- Company financial metrics
- Risk assessment tools
- Industry analysis

## Testing Your Setup

Run the test script to verify your API configurations:

```bash
cd backend
python test_external_data_aggregation.py
```

Expected output:
```
✅ External data aggregation completed successfully!
✅ News API integration working! Found X articles
```

## API Rate Limits and Best Practices

### News API
- **Free tier**: 1,000 requests/day
- **Best practice**: Cache results for 1 hour to minimize API calls
- **Usage**: Primarily for supplier risk assessment triggers

### Financial APIs
- **Rate limits**: Vary by plan and API
- **Best practice**: Cache financial data for 24 hours
- **Usage**: Regular supplier risk reviews and monitoring

## Fallback Behavior

If API keys are not configured or APIs are unavailable:

1. **News API**: Uses placeholder data, no risk signals generated
2. **Financial APIs**: Uses basic risk scoring only
3. **Overall**: Falls back to rule-based risk assessment

## Security Considerations

1. **API Key Storage**: Never commit API keys to version control
2. **Environment Variables**: Use `.env` files for local development
3. **Production**: Use secure secret management (Kubernetes secrets, AWS Secrets Manager, etc.)
4. **Access Control**: Limit API key access to necessary team members

## Troubleshooting

### Common Issues

1. **"News API key not configured"**
   - Check your `.env` file
   - Verify the variable name is correct
   - Restart your application after adding the key

2. **"API request failed"**
   - Check your internet connection
   - Verify API key is valid
   - Check API rate limits
   - Review API documentation for changes

3. **"No data returned"**
   - Verify supplier name spelling
   - Check if the company exists in the API databases
   - Try different search terms

### Debug Mode

Enable debug logging to see detailed API interactions:

```bash
LOG_LEVEL=DEBUG python test_external_data_aggregation.py
```

## Next Steps

Once your APIs are configured:

1. **Test with real suppliers**: Create supplier profiles and run enhanced risk assessments
2. **Monitor API usage**: Track your API call volumes and costs
3. **Customize risk models**: Adjust risk scoring based on your industry needs
4. **Set up alerts**: Configure notifications for high-risk suppliers

## Support

For issues with:
- **Supplero integration**: Check the main documentation
- **News API**: Visit [https://newsapi.org/docs](https://newsapi.org/docs)
- **Dun & Bradstreet**: Contact your account representative
- **Refinitiv**: Visit [https://developers.refinitiv.com/](https://developers.refinitiv.com/)
