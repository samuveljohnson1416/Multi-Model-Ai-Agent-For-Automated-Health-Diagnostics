# Hugging Face Spaces Deployment Guide

## Quick Start

### 1. Create a Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose:
   - **SDK**: Streamlit
   - **Hardware**: CPU Basic (free) or upgrade for better performance
   - **Visibility**: Public or Private

### 2. Get Your API Keys

#### Required: Hugging Face Token
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a new token with "Read" access
3. Copy the token

#### Recommended: OCR.space API Key (FREE)
1. Go to [ocr.space/ocrapi/freekey](https://ocr.space/ocrapi/freekey)
2. Enter your email
3. Get instant free API key (500 requests/day)
4. No credit card required!

### 3. Configure Secrets in HF Space

In your Space settings, add these secrets:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `HF_API_TOKEN` | Your Hugging Face token | ✅ Yes |
| `LLM_PROVIDER_PRIORITY` | `hf_only` | ✅ Yes |
| `OCR_SPACE_API_KEY` | Your OCR.space key | ✅ Yes |
| `OCR_PROVIDER_PRIORITY` | `api_only` | ✅ Yes |

### 4. Upload Files

Upload these files to your Space:

```
├── app.py                    # Main entry point
├── requirements.txt          # Python dependencies
├── packages.txt              # System dependencies (Tesseract, Poppler)
├── README_HF.md → README.md  # Rename for HF display
├── src/                      # All source code
│   ├── core/
│   ├── phase1/
│   ├── phase2/
│   ├── ui/
│   └── utils/
└── config/                   # Configuration files
```

---

## Free OCR API Options

| Provider | Free Tier | Best For | Get Key |
|----------|-----------|----------|---------|
| **OCR.space** | 500/day | General use, recommended | [Get Free Key](https://ocr.space/ocrapi/freekey) |
| **Google Vision** | 1000/month | High accuracy | [Google Cloud Console](https://console.cloud.google.com) |
| **Hugging Face** | Rate limited | Fallback option | Uses HF_API_TOKEN |

### OCR.space (Recommended)
- ✅ 500 free requests per day
- ✅ No credit card required
- ✅ Instant activation
- ✅ Good accuracy for medical documents
- ✅ Supports PDF and images

### Google Cloud Vision
- ✅ 1000 free requests per month
- ⚠️ Requires Google Cloud account
- ⚠️ Needs billing enabled (won't charge within free tier)
- ✅ Excellent accuracy

### Hugging Face OCR
- ✅ Free with HF token
- ⚠️ Rate limited
- ⚠️ Less accurate for tables
- ✅ Good fallback option

---

## LLM Provider Configuration

The system supports dual LLM backends with automatic fallback:

### Provider Priority Options

| Setting | Behavior |
|---------|----------|
| `ollama_first` | Try local Ollama → fallback to HF API |
| `hf_first` | Try HF API → fallback to Ollama |
| `ollama_only` | Only use local Ollama (fails if unavailable) |
| `hf_only` | Only use HF API (recommended for cloud) |

### For Local Development
```env
LLM_PROVIDER_PRIORITY=ollama_first
OCR_PROVIDER_PRIORITY=tesseract_first
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral:instruct
```

### For Hugging Face Spaces
```env
LLM_PROVIDER_PRIORITY=hf_only
OCR_PROVIDER_PRIORITY=api_only
HF_API_TOKEN=your_token_here
HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
OCR_SPACE_API_KEY=your_ocr_space_key
```

---

## Supported HF Models

You can use any of these models by changing `HF_MODEL_ID`:

| Model | ID |
|-------|-----|
| Mistral 7B Instruct v0.2 | `mistralai/Mistral-7B-Instruct-v0.2` |
| Mistral 7B Instruct v0.3 | `mistralai/Mistral-7B-Instruct-v0.3` |
| Llama 2 7B Chat | `meta-llama/Llama-2-7b-chat-hf` |
| Gemma 7B IT | `google/gemma-7b-it` |

---

## Troubleshooting

### "Model is loading" Error
HF Inference API models may take 20-60 seconds to load on first request. The system will retry automatically.

### OCR Not Working
1. Ensure `OCR_SPACE_API_KEY` is set in secrets
2. Set `OCR_PROVIDER_PRIORITY=api_only`
3. Check that `packages.txt` includes tesseract (as fallback)

### Import Errors
Check that `app.py` correctly adds `src/` to the Python path:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
```

### Memory Issues
If you hit memory limits on free tier:
- Upgrade to CPU Basic+ or higher
- Reduce image processing resolution
- Limit concurrent users

---

## Local Testing Before Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment for API testing
export LLM_PROVIDER_PRIORITY=hf_only
export OCR_PROVIDER_PRIORITY=api_only
export HF_API_TOKEN=your_token
export OCR_SPACE_API_KEY=your_key

# Run locally
streamlit run app.py
```

---

## Cost Considerations

| Tier | Cost | Best For |
|------|------|----------|
| CPU Basic | Free | Testing, low traffic |
| CPU Upgrade | ~$0.03/hr | Production, moderate traffic |
| GPU | ~$0.60/hr | Heavy OCR processing |

All APIs used have generous free tiers:
- HF Inference API: Free with rate limits
- OCR.space: 500 requests/day free
- Google Vision: 1000 requests/month free
