"""Configuration management for Reddit Auto Mod CLI"""
import os
import json
import getpass
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Manages configuration and credentials for Reddit Auto Mod"""
    
    def __init__(self):
        # Use user's home directory for config storage
        self.config_dir = Path.home() / '.reddit-auto-mod'
        self.config_file = self.config_dir / 'config.json'
        
    def ensure_config_dir(self):
        """Create config directory if it doesn't exist"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        # Set restrictive permissions on the directory (owner only)
        if os.name != 'nt':  # Unix-like systems
            os.chmod(self.config_dir, 0o700)
    
    def save_config(self, config: Dict) -> bool:
        """
        Save configuration to file
        
        Args:
            config: Dictionary containing configuration data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.ensure_config_dir()
            
            # Write config to file
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set restrictive permissions (owner only)
            if os.name != 'nt':  # Unix-like systems
                os.chmod(self.config_file, 0o600)
            
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def load_config(self) -> Optional[Dict]:
        """
        Load configuration from file
        
        Returns:
            Dict: Configuration dictionary or None if not found
        """
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return None
    
    def config_exists(self) -> bool:
        """Check if configuration file exists"""
        return self.config_file.exists()
    
    def get_reddit_credentials(self) -> Optional[Dict]:
        """Get Reddit credentials from config"""
        config = self.load_config()
        if config:
            return config.get('reddit_credentials')
        return None
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from config"""
        config = self.load_config()
        if config:
            return config.get('openai_api_key')
        return None
    
    def get_mongodb_uri(self) -> Optional[str]:
        """Get MongoDB URI from config"""
        config = self.load_config()
        if config:
            return config.get('mongodb_uri')
        return None


def import_config_from_file(file_path: str) -> bool:
    """
    Import configuration from a JSON file
    
    Args:
        file_path: Path to the config JSON file
        
    Returns:
        bool: True if successful
    """
    try:
        import json
        from pathlib import Path
        
        # Expand user path
        config_file = Path(file_path).expanduser()
        
        if not config_file.exists():
            print(f"Error: Config file not found: {config_file}")
            return False
        
        # Load the config file
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['reddit_credentials', 'openai_api_key']
        for field in required_fields:
            if field not in config:
                print(f"Error: Missing required field '{field}' in config file")
                return False
        
        # Validate reddit_credentials subfields
        reddit_fields = ['client_id', 'client_secret', 'user_agent', 'username', 'password']
        reddit_creds = config['reddit_credentials']
        for field in reddit_fields:
            if field not in reddit_creds:
                print(f"Error: Missing required field 'reddit_credentials.{field}' in config file")
                return False
        
        # Expand paths if present
        if 'mongodb_cert_path' in config:
            config['mongodb_cert_path'] = str(Path(config['mongodb_cert_path']).expanduser())
        
        # Save the config
        config_manager = ConfigManager()
        
        if config_manager.config_exists():
            response = input("Configuration already exists. Do you want to overwrite it? (y/n): ").strip().lower()
            if response != 'y':
                print("Import cancelled.")
                return False
        
        if config_manager.save_config(config):
            print()
            print("=" * 60)
            print("✓ Configuration imported successfully!")
            print("=" * 60)
            print()
            print(f"Config saved to: {config_manager.config_file}")
            print()
            return True
        else:
            print("Error: Failed to save configuration")
            return False
            
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        print(f"Error importing config: {e}")
        return False


def interactive_config():
    """Interactive configuration setup"""
    print("=" * 60)
    print("Reddit Auto Mod - Configuration Setup")
    print("=" * 60)
    print()
    print("This wizard will help you configure your credentials.")
    print("All credentials are stored locally in: ~/.reddit-auto-mod/config.json")
    print()
    
    config_manager = ConfigManager()
    
    # Check if config already exists
    if config_manager.config_exists():
        response = input("Configuration already exists. Do you want to overwrite it? (y/n): ").strip().lower()
        if response != 'y':
            print("Configuration cancelled.")
            return
        print()
    
    config = {}
    
    # Reddit credentials
    print("-" * 60)
    print("REDDIT API CREDENTIALS")
    print("-" * 60)
    print("You can obtain these from: https://www.reddit.com/prefs/apps")
    print()
    
    reddit_creds = {}
    reddit_creds['client_id'] = input("Reddit Client ID: ").strip()
    reddit_creds['client_secret'] = getpass.getpass("Reddit Client Secret: ").strip()
    reddit_creds['user_agent'] = input("Reddit User Agent (e.g., 'MyBot/1.0'): ").strip()
    reddit_creds['username'] = input("Reddit Username: ").strip()
    reddit_creds['password'] = getpass.getpass("Reddit Password: ").strip()
    
    config['reddit_credentials'] = reddit_creds
    
    print()
    print("-" * 60)
    print("OPENAI API KEY")
    print("-" * 60)
    print("You can obtain this from: https://platform.openai.com/api-keys")
    print()
    
    config['openai_api_key'] = getpass.getpass("OpenAI API Key: ").strip()
    
    print()
    print("-" * 60)
    print("MONGODB CONNECTION (Optional)")
    print("-" * 60)
    print("Leave blank to skip MongoDB configuration")
    print()
    
    mongodb_uri = input("MongoDB Connection URI: ").strip()
    if mongodb_uri:
        config['mongodb_uri'] = mongodb_uri
        
        # Ask for certificate path if using X.509 authentication
        if "MONGODB-X509" in mongodb_uri or "X509" in mongodb_uri:
            print()
            print("X.509 authentication detected. Please provide certificate path.")
            cert_path = input("Path to X.509 certificate file (.pem): ").strip()
            if cert_path:
                # Expand user home directory if present
                from pathlib import Path
                cert_path = str(Path(cert_path).expanduser())
                config['mongodb_cert_path'] = cert_path
    
    # Save configuration
    print()
    print("Saving configuration...")
    
    if config_manager.save_config(config):
        print()
        print("=" * 60)
        print("✓ Configuration saved successfully!")
        print("=" * 60)
        print()
        print(f"Config file location: {config_manager.config_file}")
        print()
        print("You can now use the reddit-auto-mod commands.")
        print()
    else:
        print()
        print("=" * 60)
        print("✗ Failed to save configuration")
        print("=" * 60)
        print()


def show_config():
    """Display current configuration (without sensitive data)"""
    config_manager = ConfigManager()
    
    if not config_manager.config_exists():
        print("No configuration found. Run 'reddit-auto-mod config' to set up.")
        return
    
    config = config_manager.load_config()
    if not config:
        print("Error loading configuration.")
        return
    
    print()
    print("=" * 60)
    print("Current Configuration")
    print("=" * 60)
    print()
    
    # Show Reddit credentials (masked)
    if 'reddit_credentials' in config:
        reddit = config['reddit_credentials']
        print("Reddit Credentials:")
        print(f"  Client ID: {reddit.get('client_id', 'Not set')[:8]}...")
        print(f"  Client Secret: {'*' * 8}...")
        print(f"  User Agent: {reddit.get('user_agent', 'Not set')}")
        print(f"  Username: {reddit.get('username', 'Not set')}")
        print(f"  Password: {'*' * 8}")
    else:
        print("Reddit Credentials: Not configured")
    
    print()
    
    # Show OpenAI key (masked)
    if 'openai_api_key' in config:
        key = config['openai_api_key']
        print(f"OpenAI API Key: {key[:8]}...{key[-4:]}")
    else:
        print("OpenAI API Key: Not configured")
    
    print()
    
    # Show MongoDB URI (masked)
    if 'mongodb_uri' in config:
        uri = config['mongodb_uri']
        # Mask password in URI if present
        if '@' in uri:
            parts = uri.split('@')
            masked = parts[0].split('://')[0] + '://***:***@' + parts[1]
        else:
            masked = uri
        print(f"MongoDB URI: {masked}")
        
        # Show certificate path if configured
        if 'mongodb_cert_path' in config:
            print(f"MongoDB Certificate: {config['mongodb_cert_path']}")
    else:
        print("MongoDB URI: Not configured")
    
    print()
    print(f"Config file location: {config_manager.config_file}")
    print()


def clear_config():
    """Clear the configuration"""
    config_manager = ConfigManager()
    
    if not config_manager.config_exists():
        print("No configuration found to clear.")
        return
    
    response = input("Are you sure you want to delete your configuration? (y/n): ").strip().lower()
    if response != 'y':
        print("Operation cancelled.")
        return
    
    try:
        config_manager.config_file.unlink()
        print("Configuration cleared successfully.")
    except Exception as e:
        print(f"Error clearing configuration: {e}")
