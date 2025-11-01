from pymongo import MongoClient
from typing import Optional
from pymongo.database import Database

class MongoWrapper:
    """Manages MongoDB connection and provides shared connection pool"""
    
    _instance = None
    _mongo_client = None
    _mongo_db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoWrapper, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        import os
        import sys
        from pathlib import Path
        
        # Try to load from CLI config first
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))
            from config import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            if config and 'mongodb_uri' in config:
                self.uri = config['mongodb_uri']
                
                # Check if certificate path is in config
                if 'mongodb_cert_path' in config:
                    cert_path = config['mongodb_cert_path']
                else:
                    # Fallback to default location
                    current_dir = os.path.dirname(os.path.abspath(__file__))
                    cert_path = os.path.join(current_dir, "Config", "X509-cert-3753233507821277243.pem")
            else:
                # Use hardcoded defaults
                current_dir = os.path.dirname(os.path.abspath(__file__))
                self.uri = "mongodb+srv://X509:@bhavinmongocluster.5t6smyb.mongodb.net/?authSource=$external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=BhavinMongoCluster"
                cert_path = os.path.join(current_dir, "Config", "X509-cert-3753233507821277243.pem")
        except Exception:
            # Fallback to defaults if config loading fails
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.uri = "mongodb+srv://X509:@bhavinmongocluster.5t6smyb.mongodb.net/?authSource=$external&authMechanism=MONGODB-X509&retryWrites=true&w=majority&appName=BhavinMongoCluster"
            cert_path = os.path.join(current_dir, "Config", "X509-cert-3753233507821277243.pem")
        
        self.config = {
            'tls': True,
            'tlsCertificateKeyFile': cert_path,
            'serverSelectionTimeoutMS': 30000,
            'socketTimeoutMS': 30000,
            'connectTimeoutMS': 30000,
            'maxPoolSize': 10,
            'minPoolSize': 2,
            'maxIdleTimeMS': 30000,
        }
    
    def get_connection(self) -> Optional[Database]:
        """Get or create a shared MongoDB connection"""
        if self._mongo_client is None:
            try:
                self._mongo_client = MongoClient(
                    self.uri,
                    **self.config
                )
                # Test the connection
                self._mongo_client.admin.command('ping')
                self._mongo_db = self._mongo_client['mainDB']
            except Exception as e:
                print(f"Failed to connect to MongoDB: {str(e)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                self._mongo_client = None
                self._mongo_db = None
                return None
                
        return self._mongo_db
    
    def close_connection(self):
        """Close the MongoDB connection if it exists"""
        if self._mongo_client:
            try:
                self._mongo_client.close()
            finally:
                self._mongo_client = None
                self._mongo_db = None
    
    def is_connected(self) -> bool:
        """Check if the database connection is active"""
        if self._mongo_client is None or self._mongo_db is None:
            return False
            
        try:
            # Test the connection
            self._mongo_client.admin.command('ping')
            return True
        except Exception:
            self._mongo_client = None
            self._mongo_db = None
            return False
