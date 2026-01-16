# Automated Deployment Guide

This project supports automated deployment to **Hugging Face Spaces** (recommended) and **Vercel**.

---

## 🚀 Quick Comparison

| Platform | Best For | Streamlit Support | Free Tier |
|----------|----------|-------------------|-----------|
| **Hugging Face Spaces** ⭐ | Full app with UI | ✅ Native | ✅ Unlimited |
| **Vercel** | API-only / Static | ❌ Limited | ✅ Generous |

**Recommendation**: Use **Hugging Face Spaces** for this Streamlit app.

---

## 🤗 Hugging Face Spaces (Recommended)

### One-Time Setup

1. **Create a Hugging Face Account**
   - Go to [huggingface.co](https://huggingface.co) and sign up

2. **Create a New Space**
   - Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Name: `blood-report-analyzer` (or your choice)
   - SDK: **Streamlit**
   - Hardware: **CPU Basic** (free)
   - Click "Create Space"

3. **Get Your Tokens**
   - HF Token: [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → Create "Write" token
   - OCR.space Key: [ocr.space/ocrapi/freekey](https://ocr.space/ocrapi/freekey)

4. **Add Secrets to Your Space**
   - Go to your Space → Settings → Variables and secrets
   - Add these secrets:
     ```
     HF_API_TOKEN = hf_xxxxxxxxxxxxx
     LLM_PROVIDER_PRIORITY = hf_only
     OCR_SPACE_API_KEY = K8xxxxxxxxxxxxx
     OCR_PROVIDER_PRIORITY = api_only
     ```

5. **Add GitHub Secrets** (for automation)
   - Go to your GitHub repo → Settings → Secrets → Actions
   - Add:
     ```
     HF_TOKEN = hf_xxxxxxxxxxxxx (Write token)
     HF_SPACE_NAME = your-username/blood-report-analyzer
     ```

### Automated Deployment

Once set up, every push to `main` branch automatically deploys to HF Spaces!

```bash
git add .
git commit -m "Update feature"
git push origin main
# → Automatically deploys to HF Spaces
```

### Manual Deployment

```bash
# One-time: Add HF remote
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME

# Deploy
git push hf main
```

---

## ▲ Vercel Deployment

> ⚠️ **Note**: Vercel's serverless architecture doesn't fully support Streamlit. 
> Use this for API-only deployment or consider HF Spaces for full UI.

### One-Time Setup

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com) and sign up with GitHub

2. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

3. **Link Project**
   ```bash
   vercel link
   ```

4. **Add Environment Variables**
   ```bash
   vercel env add HF_API_TOKEN
   vercel env add OCR_SPACE_API_KEY
   vercel env add LLM_PROVIDER_PRIORITY
   vercel env add OCR_PROVIDER_PRIORITY
   ```

5. **Get Project IDs** (for GitHub Actions)
   ```bash
   cat .vercel/project.json
   # Copy orgId and projectId
   ```

6. **Add GitHub Secrets**
   - `VERCEL_TOKEN`: Get from [vercel.com/account/tokens](https://vercel.com/account/tokens)
   - `VERCEL_ORG_ID`: From step 5
   - `VERCEL_PROJECT_ID`: From step 5

### Manual Deployment

```bash
vercel --prod
```

---

## 🔧 GitHub Actions Workflows

### Hugging Face Deployment
File: `.github/workflows/deploy-huggingface.yml`

**Required Secrets:**
| Secret | Description |
|--------|-------------|
| `HF_TOKEN` | HF token with Write access |
| `HF_SPACE_NAME` | `username/space-name` |

### Vercel Deployment
File: `.github/workflows/deploy-vercel.yml`

**Required Secrets:**
| Secret | Description |
|--------|-------------|
| `VERCEL_TOKEN` | Vercel API token |
| `VERCEL_ORG_ID` | Your Vercel org ID |
| `VERCEL_PROJECT_ID` | Your Vercel project ID |

---

## 📋 Checklist

### For Hugging Face Spaces
- [ ] Created HF account
- [ ] Created new Space (Streamlit SDK)
- [ ] Added Space secrets (HF_API_TOKEN, OCR_SPACE_API_KEY, etc.)
- [ ] Added GitHub secrets (HF_TOKEN, HF_SPACE_NAME)
- [ ] Pushed to main branch

### For Vercel
- [ ] Created Vercel account
- [ ] Linked project with `vercel link`
- [ ] Added environment variables
- [ ] Added GitHub secrets (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID)
- [ ] Pushed to main branch

---

## 🆘 Troubleshooting

### HF Spaces: "Model is loading"
- First request takes 20-60 seconds
- Subsequent requests are faster
- This is normal for free tier

### HF Spaces: Build Failed
- Check `packages.txt` exists with system dependencies
- Ensure `app.py` is at root level
- Check logs in Space → Logs tab

### Vercel: Streamlit Not Working
- Vercel doesn't support long-running processes
- Use HF Spaces for Streamlit apps
- Vercel is better for APIs and static sites

### GitHub Actions: Permission Denied
- Ensure tokens have correct permissions
- HF token needs "Write" access
- Vercel token needs deployment permissions
