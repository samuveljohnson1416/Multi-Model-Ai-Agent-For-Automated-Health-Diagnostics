#!/usr/bin/env python3
"""
Deployment Helper Script
Automates deployment to Hugging Face Spaces or Vercel
"""

import os
import sys
import subprocess
import argparse


def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result


def deploy_huggingface(space_name, token=None):
    """Deploy to Hugging Face Spaces"""
    print("\n🤗 Deploying to Hugging Face Spaces...")
    
    # Get token from env if not provided
    if not token:
        token = os.getenv("HF_TOKEN")
    
    if not token:
        print("❌ Error: HF_TOKEN not set. Set it via environment or --token flag")
        print("   Get your token at: https://huggingface.co/settings/tokens")
        sys.exit(1)
    
    if not space_name:
        print("❌ Error: Space name required. Use --space flag")
        print("   Example: --space username/blood-report-analyzer")
        sys.exit(1)
    
    # Check if remote exists
    result = run_command("git remote -v", check=False)
    
    if "hf" not in result.stdout:
        # Add HF remote
        run_command(f"git remote add hf https://huggingface.co/spaces/{space_name}")
    
    # Push to HF
    run_command(f"git push https://user:{token}@huggingface.co/spaces/{space_name} main --force")
    
    print(f"\n✅ Deployed to: https://huggingface.co/spaces/{space_name}")


def deploy_vercel(prod=True):
    """Deploy to Vercel"""
    print("\n▲ Deploying to Vercel...")
    
    # Check if Vercel CLI is installed
    result = run_command("vercel --version", check=False)
    if result.returncode != 0:
        print("❌ Vercel CLI not installed. Install with: npm install -g vercel")
        sys.exit(1)
    
    # Deploy
    cmd = "vercel --prod" if prod else "vercel"
    run_command(cmd)
    
    print("\n✅ Deployed to Vercel!")


def check_env():
    """Check environment configuration"""
    print("\n🔍 Checking environment configuration...\n")
    
    checks = [
        ("HF_API_TOKEN", os.getenv("HF_API_TOKEN"), "Hugging Face API Token"),
        ("OCR_SPACE_API_KEY", os.getenv("OCR_SPACE_API_KEY"), "OCR.space API Key"),
        ("HF_TOKEN", os.getenv("HF_TOKEN"), "HF Token (for deployment)"),
    ]
    
    all_good = True
    for env_var, value, description in checks:
        if value:
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"✅ {env_var}: {masked} ({description})")
        else:
            print(f"❌ {env_var}: Not set ({description})")
            all_good = False
    
    if all_good:
        print("\n✅ All environment variables are set!")
    else:
        print("\n⚠️  Some environment variables are missing.")
        print("   Copy .env.example to .env and fill in your values.")
    
    return all_good


def main():
    parser = argparse.ArgumentParser(description="Deploy Blood Report Analyzer")
    parser.add_argument("target", choices=["hf", "vercel", "check"], 
                       help="Deployment target: hf (Hugging Face), vercel, or check (env check)")
    parser.add_argument("--space", help="HF Space name (e.g., username/space-name)")
    parser.add_argument("--token", help="HF token (or set HF_TOKEN env var)")
    parser.add_argument("--preview", action="store_true", help="Vercel preview deployment")
    
    args = parser.parse_args()
    
    if args.target == "check":
        check_env()
    elif args.target == "hf":
        deploy_huggingface(args.space, args.token)
    elif args.target == "vercel":
        deploy_vercel(prod=not args.preview)


if __name__ == "__main__":
    main()
