"""
Vercel Serverless Function Entry Point
Note: Streamlit doesn't work well on Vercel's serverless architecture.
For full Streamlit support, use Hugging Face Spaces instead.

This provides a simple API endpoint for Vercel deployment.
"""

from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "status": "ok",
            "message": "Blood Report Analysis API",
            "note": "For full UI, please use Hugging Face Spaces deployment",
            "endpoints": {
                "/": "This info page",
                "/api/health": "Health check"
            },
            "recommended_deployment": "Hugging Face Spaces (supports Streamlit UI)"
        }
        
        self.wfile.write(json.dumps(response, indent=2).encode())
        return


def main():
    """For local testing"""
    print("Vercel API endpoint - use 'vercel dev' to test locally")


if __name__ == "__main__":
    main()
