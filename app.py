#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import urllib.request
import urllib.parse

# Your Courier API Key - Get from https://app.courier.com/settings/api-keys
COURIER_AUTH_TOKEN = "pk_prod_DQQ3R52PR44ZESGC7TCA1H8FRB0Q"  # Replace with your actual key
PORT = int(os.environ.get('PORT', 8000))

class CourierHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/api/generate-jwt':
            self.generate_jwt()
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/trigger-automation':
            self.trigger_automation()
        else:
            self.send_error(404, "Endpoint not found")
    
    def generate_jwt(self):
        try:
            # Call Courier API to generate JWT
            data = {
                "scope": "user_id:demo-user-123 inbox:read:messages inbox:write:events read:preferences",
                "expires_in": "30 days"
            }
            
            req = urllib.request.Request(
                'https://api.courier.com/auth/issue-token',
                data=json.dumps(data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {COURIER_AUTH_TOKEN}',
                    'Content-Type': 'application/json'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                jwt_token = result.get('token')
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'jwt': jwt_token}).encode())
                
        except Exception as e:
            self.send_error(500, f"Error generating JWT: {str(e)}")
    
    def trigger_automation(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            # Trigger a Courier Automation
            automation_data = {
                "automation": {
                    "steps": [
                        {
                            "action": "send",
                            "recipients": ["demo-user-123"],
                            "message": {
                                "to": {
                                    "user_id": "demo-user-123"
                                },
                                "content": {
                                    "title": data.get('title', 'Automation Triggered!'),
                                    "body": data.get('body', 'This came from a Courier Automation!')
                                },
                                "routing": {
                                    "method": "all",
                                    "channels": ["inbox"]
                                }
                            }
                        }
                    ]
                }
            }
            
            # Make request to Courier Automations API
            req = urllib.request.Request(
                'https://api.courier.com/automations/invoke',
                data=json.dumps(automation_data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {COURIER_AUTH_TOKEN}',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'runId': result.get('runId')
                }).encode())
                
        except Exception as e:
            self.send_error(500, f"Error triggering automation: {str(e)}")
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == '__main__':
    print(f"Starting Courier Demo server on http://localhost:{PORT}")
    print("Make sure to update COURIER_AUTH_TOKEN in app.py with your actual Courier API key!")
    
    with socketserver.TCPServer(("", PORT), CourierHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print("Open this URL in your browser to see the demo")
        httpd.serve_forever()
