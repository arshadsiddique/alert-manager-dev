#!/usr/bin/env python3
"""
Update JSM configuration from environment variables
Usage: python update_jsm_config.py
"""

import os
import sys

def update_env_file():
    """Update .env file with JSM-specific configuration"""
    
    # Check if .env.example exists
    if not os.path.exists('.env.example'):
        print("❌ .env.example file not found")
        return False
    
    # Read .env.example
    with open('.env.example', 'r') as f:
        example_content = f.read()
    
    # Get current .env content if it exists
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
    
    # Extract existing values
    existing_values = {}
    for line in env_content.split('\n'):
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            existing_values[key] = value.strip('"')
    
    # Prompt for JSM-specific values
    jsm_config = {}
    
    print("🔧 JSM Configuration Setup")
    print("=" * 30)
    
    # JSM Cloud ID
    current_cloud_id = existing_values.get('JSM_CLOUD_ID', '')
    if current_cloud_id and current_cloud_id != 'your_actual_cloud_id':
        jsm_config['JSM_CLOUD_ID'] = current_cloud_id
        print(f"✅ Using existing Cloud ID: {current_cloud_id}")
    else:
        cloud_id = input("Enter your JSM Cloud ID (from tenant_info API): ").strip()
        if cloud_id:
            jsm_config['JSM_CLOUD_ID'] = cloud_id
        else:
            print("❌ Cloud ID is required for JSM integration")
            return False
    
    # Jira URL
    current_jira_url = existing_values.get('JIRA_URL', '')
    if current_jira_url and 'atlassian.net' in current_jira_url:
        jsm_config['JIRA_URL'] = current_jira_url
        print(f"✅ Using existing Jira URL: {current_jira_url}")
    else:
        jira_url = input("Enter your Jira URL (e.g., https://yourcompany.atlassian.net): ").strip()
        if jira_url:
            jsm_config['JIRA_URL'] = jira_url
        else:
            print("❌ Jira URL is required")
            return False
    
    # Email
    current_email = existing_values.get('JIRA_USER_EMAIL', '')
    if current_email and '@' in current_email:
        jsm_config['JIRA_USER_EMAIL'] = current_email
        print(f"✅ Using existing email: {current_email}")
    else:
        email = input("Enter your Jira user email: ").strip()
        if email:
            jsm_config['JIRA_USER_EMAIL'] = email
        else:
            print("❌ User email is required")
            return False
    
    # API Token
    current_token = existing_values.get('JIRA_API_TOKEN', '')
    if current_token and len(current_token) > 10:
        choice = input(f"Use existing API token? (y/n): ").strip().lower()
        if choice == 'y':
            jsm_config['JIRA_API_TOKEN'] = current_token
            print("✅ Using existing API token")
        else:
            token = input("Enter your Jira API token: ").strip()
            if token:
                jsm_config['JIRA_API_TOKEN'] = token
            else:
                print("❌ API token is required")
                return False
    else:
        token = input("Enter your Jira API token: ").strip()
        if token:
            jsm_config['JIRA_API_TOKEN'] = token
        else:
            print("❌ API token is required")
            return False
    
    # Grafana API Key
    current_grafana_key = existing_values.get('GRAFANA_API_KEY', '')
    if current_grafana_key and len(current_grafana_key) > 10:
        choice = input(f"Use existing Grafana API key? (y/n): ").strip().lower()
        if choice == 'y':
            jsm_config['GRAFANA_API_KEY'] = current_grafana_key
            print("✅ Using existing Grafana API key")
        else:
            grafana_key = input("Enter your Grafana API key: ").strip()
            if grafana_key:
                jsm_config['GRAFANA_API_KEY'] = grafana_key
            else:
                print("❌ Grafana API key is required")
                return False
    else:
        grafana_key = input("Enter your Grafana API key: ").strip()
        if grafana_key:
            jsm_config['GRAFANA_API_KEY'] = grafana_key
        else:
            print("❌ Grafana API key is required")
            return False
    
    # Update other values with defaults
    jsm_config.update({
        'USE_JSM_MODE': 'true',
        'ENABLE_AUTO_CLOSE': 'true',
        'ALERT_MATCH_CONFIDENCE_THRESHOLD': '50.0',
        'ALERT_MATCH_TIME_WINDOW_MINUTES': '15',
        'GRAFANA_SYNC_INTERVAL_SECONDS': '300',
        'FILTER_NON_PROD_ALERTS': 'true'
    })
    
    # Create new .env content
    new_content = example_content
    
    for key, value in jsm_config.items():
        # Replace placeholder values with actual values
        new_content = new_content.replace(f'{key}="your_actual_{key.lower()}"', f'{key}="{value}"')
        new_content = new_content.replace(f'{key}=your_actual_{key.lower()}', f'{key}="{value}"')
        new_content = new_content.replace(f'{key}="cfe6e1fe-26bb-4354-9cf1-fffaf23319db"', f'{key}="{value}"')
        
        # Handle boolean and numeric values
        if key in ['USE_JSM_MODE', 'ENABLE_AUTO_CLOSE', 'FILTER_NON_PROD_ALERTS']:
            new_content = new_content.replace(f'{key}=true', f'{key}={value}')
        elif key in ['ALERT_MATCH_CONFIDENCE_THRESHOLD', 'ALERT_MATCH_TIME_WINDOW_MINUTES', 'GRAFANA_SYNC_INTERVAL_SECONDS']:
            # Replace any existing numeric values
            import re
            pattern = f'{key}=\\d+(\\.\\d+)?'
            new_content = re.sub(pattern, f'{key}={value}', new_content)
    
    # Write new .env file
    with open('.env', 'w') as f:
        f.write(new_content)
    
    print("\n✅ .env file updated successfully!")
    print("\n📋 Configuration Summary:")
    for key, value in jsm_config.items():
        if 'TOKEN' in key or 'KEY' in key:
            print(f"   {key}: {'*' * 8}...{value[-4:]}")
        else:
            print(f"   {key}: {value}")
    
    return True

if __name__ == "__main__":
    print("Devo Alert Manager - Configuration Setup")
    print("=" * 50)
    
    if update_env_file():
        print("\n🎉 Configuration complete! You can now run:")
        print("   docker-compose up -d")
    else:
        print("\n❌ Configuration failed. Please check your inputs and try again.")
        sys.exit(1)