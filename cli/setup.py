"""Setup module for Reddit Auto Mod - handles subreddit configuration and index creation"""
import os
import sys
from pathlib import Path
from typing import List

# Add BackEnd to path for imports
backend_path = Path(__file__).parent.parent / "BackEnd"
sys.path.insert(0, str(backend_path))

from cli.config import ConfigManager


def interactive_setup():
    """Interactive setup wizard for subreddit configuration and index creation"""
    print("=" * 60)
    print("Reddit Auto Mod - Setup Wizard")
    print("=" * 60)
    print()
    print("This wizard will help you:")
    print("1. Configure subreddits to moderate")
    print("2. Set up MongoDB database and collections")
    print("3. Build FAISS indexes for similarity detection")
    print()
    
    # Check if credentials are configured
    config_manager = ConfigManager()
    if not config_manager.config_exists():
        print("ERROR: No credentials found.")
        print("Please run 'reddit-auto-mod config' first to set up credentials.")
        print()
        return False
    
    config = config_manager.load_config()
    
    # Step 1: Get subreddits from config
    print("-" * 60)
    print("STEP 1: SUBREDDIT CONFIGURATION")
    print("-" * 60)
    
    if 'subreddits' in config and config['subreddits']:
        subreddits = config['subreddits']
        print(f"Using subreddits from config: {', '.join(subreddits)}")
        print()
    else:
        print("ERROR: No subreddits found in config.")
        print("Please ensure your config file includes a 'subreddits' array.")
        print()
        return False
    
    # Step 2: MongoDB setup
    print("-" * 60)
    print("STEP 2: MONGODB CONFIGURATION")
    print("-" * 60)
    
    # Check if MongoDB URI exists
    if 'mongodb_uri' not in config or not config['mongodb_uri']:
        print("MongoDB URI not found in configuration.")
        mongodb_uri = input("Enter MongoDB Connection URI: ").strip()
        config['mongodb_uri'] = mongodb_uri
    else:
        print(f"Using existing MongoDB URI from config.")
        mongodb_uri = config['mongodb_uri']
    
    print()
    db_name = input("Enter database name to use (default: mainDB): ").strip()
    if not db_name:
        db_name = "mainDB"
    
    config['database_name'] = db_name
    config['subreddits'] = subreddits
    
    print()
    print("Setting up MongoDB collections...")
    
    try:
        success = setup_mongodb_collections(mongodb_uri, db_name)
        if success:
            print("✓ MongoDB collections created successfully!")
        else:
            print("✗ Failed to create MongoDB collections")
            return False
    except Exception as e:
        print(f"✗ Error setting up MongoDB: {e}")
        return False
    
    print()
    print("Fetching and importing subreddit rules...")
    
    try:
        # Get Reddit credentials from config
        reddit_creds = config_manager.get_reddit_credentials()
        if not reddit_creds:
            print("✗ Reddit credentials not found in config")
            return False
        
        success = import_subreddit_rules(subreddits, mongodb_uri, db_name, reddit_creds)
        if success:
            print("✓ Subreddit rules imported successfully!")
        else:
            print("⚠ Some subreddit rules could not be imported (check warnings above)")
    except Exception as e:
        print(f"✗ Error importing subreddit rules: {e}")
        print("You can add rules manually to the RedditRules collection")
    
    print()
    print("Fetching recent posts from subreddits...")
    
    try:
        fetch_and_store_posts(subreddits, mongodb_uri, db_name, reddit_creds, limit=100)
    except Exception as e:
        print(f"✗ Error fetching posts: {e}")
        print("You can fetch posts manually or skip index creation")
    
    print()
    
    # Step 3: Build indexes
    print("-" * 60)
    print("STEP 3: FAISS INDEX CREATION")
    print("-" * 60)
    print()
    print("Building FAISS indexes for similarity detection...")
    print("This may take some time depending on the amount of data.")
    print()
    
    response = input("Do you want to build indexes now? (y/n): ").strip().lower()
    
    if response == 'y':
        try:
            build_indexes_for_subreddits(subreddits, mongodb_uri, db_name)
            print()
            print("✓ Indexes built successfully!")
        except Exception as e:
            print(f"✗ Error building indexes: {e}")
            print()
            print("You can build indexes later by running:")
            print("  reddit-auto-mod setup --build-indexes")
    else:
        print()
        print("Skipping index creation. You can build them later by running:")
        print("  reddit-auto-mod setup --build-indexes")
    
    # Save updated config
    config_manager.save_config(config)
    
    print()
    print("=" * 60)
    print("✓ Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Add subreddit rules to MongoDB (RedditRules collection)")
    print("2. Start the backend services")
    print("3. Begin moderating!")
    print()
    
    return True


def setup_mongodb_collections(mongodb_uri: str, db_name: str) -> bool:
    """
    Create MongoDB collections for the application
    
    Args:
        mongodb_uri: MongoDB connection URI
        db_name: Database name
    
    Returns:
        bool: True if successful
    """
    try:
        from pymongo import MongoClient
        
        # Get certificate path from config if needed
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Prepare connection parameters
        connection_params = {}
        if 'mongodb_cert_path' in config and config['mongodb_cert_path']:
            cert_path = config['mongodb_cert_path']
            connection_params = {
                'tls': True,
                'tlsCertificateKeyFile': cert_path,
                'serverSelectionTimeoutMS': 30000,
                'socketTimeoutMS': 30000,
                'connectTimeoutMS': 30000
            }
        
        # Connect to MongoDB
        client = MongoClient(mongodb_uri, **connection_params)
        db = client[db_name]
        
        # Test connection
        client.admin.command('ping')
        
        # Create collections if they don't exist
        existing_collections = db.list_collection_names()
        
        collections_to_create = [
            'RedditRules',
            'RedditSubmissions',
            'ProcessedRedditSubmissions'
        ]
        
        for collection_name in collections_to_create:
            if collection_name not in existing_collections:
                db.create_collection(collection_name)
                print(f"  Created collection: {collection_name}")
            else:
                print(f"  Collection already exists: {collection_name}")
        
        # Create indexes for better performance
        print("\nCreating indexes...")
        
        # Index on RedditRules
        db['RedditRules'].create_index('subreddit')
        print("  Created index on RedditRules.subreddit")
        
        # Index on RedditSubmissions
        db['RedditSubmissions'].create_index('subreddit')
        db['RedditSubmissions'].create_index('submission_id')
        print("  Created index on RedditSubmissions.subreddit")
        print("  Created index on RedditSubmissions.submission_id")
        
        # Index on ProcessedRedditSubmissions
        db['ProcessedRedditSubmissions'].create_index('subreddit')
        db['ProcessedRedditSubmissions'].create_index('id')
        print("  Created index on ProcessedRedditSubmissions.subreddit")
        print("  Created index on ProcessedRedditSubmissions.id")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"Error setting up MongoDB collections: {e}")
        return False


def fetch_and_store_posts(subreddits: List[str], mongodb_uri: str, db_name: str, reddit_creds: dict, limit: int = 100):
    """
    Fetch recent posts from Reddit and store in MongoDB
    
    Args:
        subreddits: List of subreddit names
        mongodb_uri: MongoDB connection URI
        db_name: Database name
        reddit_creds: Reddit API credentials
        limit: Number of posts to fetch per subreddit
    """
    try:
        import praw
        from pymongo import MongoClient
        
        print()
        print("Fetching recent posts from Reddit...")
        
        # Create Reddit instance
        reddit = praw.Reddit(
            client_id=reddit_creds['client_id'],
            client_secret=reddit_creds['client_secret'],
            user_agent=reddit_creds['user_agent'],
            username=reddit_creds['username'],
            password=reddit_creds['password']
        )
        
        print("Connecting to MongoDB...")
        
        # Get certificate path from config if needed
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Prepare connection parameters
        connection_params = {}
        if 'mongodb_cert_path' in config and config['mongodb_cert_path']:
            cert_path = config['mongodb_cert_path']
            connection_params = {
                'tls': True,
                'tlsCertificateKeyFile': cert_path,
                'serverSelectionTimeoutMS': 30000,
                'socketTimeoutMS': 30000,
                'connectTimeoutMS': 30000
            }
        
        client = MongoClient(mongodb_uri, **connection_params)
        db = client[db_name]
        collection = db['RedditSubmissions']
        
        for subreddit_name in subreddits:
            try:
                print(f"\nFetching posts from r/{subreddit_name}...")
                
                subreddit = reddit.subreddit(subreddit_name)
                posts_added = 0
                
                # Fetch recent posts
                for submission in subreddit.hot(limit=limit):
                    # Check if post already exists
                    if collection.find_one({'submission_id': submission.id}):
                        continue
                    
                    # Store post in required format
                    post_doc = {
                        'subreddit': subreddit_name,
                        'submission_id': submission.id,
                        'submission_name': submission.name,  # Full name like "t3_1bkakb2"
                        'submission_title': submission.title,
                        'submission_text': submission.selftext
                    }
                    
                    collection.insert_one(post_doc)
                    posts_added += 1
                
                print(f"  ✓ Added {posts_added} new posts")
                
            except Exception as e:
                print(f"  ✗ Error fetching posts from r/{subreddit_name}: {e}")
                continue
        
        client.close()
        print("\n✓ Posts fetched and stored successfully!")
        
    except Exception as e:
        print(f"Error fetching posts: {e}")
        raise


def import_subreddit_rules(subreddits: List[str], mongodb_uri: str, db_name: str, reddit_creds: dict) -> bool:
    """
    Fetch and import subreddit rules from Reddit into MongoDB
    
    Args:
        subreddits: List of subreddit names
        mongodb_uri: MongoDB connection URI
        db_name: Database name
        reddit_creds: Reddit API credentials
        
    Returns:
        bool: True if all successful, False if any failures
    """
    try:
        import praw
        from pymongo import MongoClient
        
        print()
        print("Connecting to Reddit...")
        
        # Create Reddit instance
        reddit = praw.Reddit(
            client_id=reddit_creds['client_id'],
            client_secret=reddit_creds['client_secret'],
            user_agent=reddit_creds['user_agent'],
            username=reddit_creds['username'],
            password=reddit_creds['password']
        )
        
        print("Connecting to MongoDB...")
        
        # Get certificate path from config if needed
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Prepare connection parameters
        connection_params = {}
        if 'mongodb_cert_path' in config and config['mongodb_cert_path']:
            cert_path = config['mongodb_cert_path']
            connection_params = {
                'tls': True,
                'tlsCertificateKeyFile': cert_path,
                'serverSelectionTimeoutMS': 30000,
                'socketTimeoutMS': 30000,
                'connectTimeoutMS': 30000
            }
        
        client = MongoClient(mongodb_uri, **connection_params)
        db = client[db_name]
        rules_collection = db['RedditRules']
        
        all_successful = True
        
        for subreddit_name in subreddits:
            try:
                print(f"\nFetching rules for r/{subreddit_name}...")
                
                # Get subreddit
                subreddit = reddit.subreddit(subreddit_name)
                
                # Fetch rules
                rules = list(subreddit.rules)
                
                if not rules:
                    print(f"  ⚠ No rules found for r/{subreddit_name}")
                    continue
                
                print(f"  Found {len(rules)} rules")
                
                # Prepare rules documents - simple format: subreddit and rule description
                rules_docs = []
                for rule in rules:
                    # Use description if available, otherwise fall back to short_name
                    rule_text = rule.description if hasattr(rule, 'description') and rule.description else rule.short_name
                    rule_doc = {
                        'subreddit': subreddit_name,
                        'rule': rule_text
                    }
                    rules_docs.append(rule_doc)
                
                # Delete existing rules for this subreddit
                rules_collection.delete_many({'subreddit': subreddit_name})
                
                # Insert new rules
                if rules_docs:
                    rules_collection.insert_many(rules_docs)
                    print(f"  ✓ Imported {len(rules_docs)} rules")
                    
                    # Display rules
                    for i, rule_doc in enumerate(rules_docs, 1):
                        print(f"    {i}. {rule_doc['rule']}")
                
            except Exception as e:
                print(f"  ✗ Error fetching rules for r/{subreddit_name}: {e}")
                all_successful = False
                continue
        
        client.close()
        return all_successful
        
    except ImportError:
        print("Error: PRAW not installed. Install with: pip install praw")
        return False
    except Exception as e:
        print(f"Error importing subreddit rules: {e}")
        return False


def build_indexes_for_subreddits(subreddits: List[str], mongodb_uri: str, db_name: str):
    """
    Build FAISS indexes for specified subreddits
    
    Args:
        subreddits: List of subreddit names
        mongodb_uri: MongoDB connection URI
        db_name: Database name
    """
    try:
        from pymongo import MongoClient
        from sentence_transformers import SentenceTransformer
        import faiss
        import numpy as np
        import pickle
        from collections import defaultdict
        from tqdm import tqdm
        
        print("Loading sentence transformer model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print("Connecting to MongoDB...")
        
        # Get certificate path from config if needed
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Prepare connection parameters
        connection_params = {}
        if 'mongodb_cert_path' in config and config['mongodb_cert_path']:
            cert_path = config['mongodb_cert_path']
            connection_params = {
                'tls': True,
                'tlsCertificateKeyFile': cert_path,
                'serverSelectionTimeoutMS': 30000,
                'socketTimeoutMS': 30000,
                'connectTimeoutMS': 30000
            }
        
        client = MongoClient(mongodb_uri, **connection_params)
        db = client[db_name]
        collection = db['RedditSubmissions']
        
        # Get index output directory - use user's home directory for installed packages
        index_dir = Path.home() / ".reddit-auto-mod" / "indexes"
        index_dir.mkdir(parents=True, exist_ok=True)
        print(f"Index directory: {index_dir}")
        
        for subreddit in subreddits:
            print()
            print(f"Processing subreddit: {subreddit}")
            
            # Fetch posts for this subreddit
            posts = list(collection.find({"subreddit": subreddit}))
            
            if len(posts) == 0:
                print(f"  WARNING: No posts found for r/{subreddit}")
                print(f"  Skipping index creation. Add posts to RedditSubmissions collection first.")
                continue
            
            print(f"  Found {len(posts)} posts")
            print(f"  Generating embeddings...")
            
            # Generate embeddings
            embeddings_list = []
            doc_ids = []
            
            for post in tqdm(posts, desc=f"  Embedding"):
                text_content = post.get('submission_text', '') + " " + post.get('submission_title', '')
                embedding = model.encode(text_content)
                embedding = embedding.astype('float32')
                embeddings_list.append(embedding)
                doc_ids.append(str(post['submission_id']))
            
            # Convert to numpy array
            embeddings = np.array(embeddings_list, dtype='float32')
            dimension = embeddings.shape[1]
            
            print(f"  Building FAISS index...")
            
            # Create FAISS index
            nlist = min(100, len(posts))  # Number of clusters
            quantizer = faiss.IndexFlatL2(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
            
            # Train and add embeddings
            index.train(embeddings)
            index.add(embeddings)
            
            # Save index
            index_path = index_dir / f"{subreddit}.faiss"
            ids_path = index_dir / f"{subreddit}_ids.pkl"
            
            faiss.write_index(index, str(index_path))
            with open(ids_path, "wb") as f:
                pickle.dump(doc_ids, f)
            
            print(f"  ✓ Index saved: {index_path}")
            print(f"  ✓ IDs saved: {ids_path}")
        
        client.close()
        print()
        print("All indexes built successfully!")
        
    except ImportError as e:
        print(f"Error: Missing required packages: {e}")
        print("Install with: pip install sentence-transformers faiss-cpu tqdm")
        raise
    except Exception as e:
        print(f"Error building indexes: {e}")
        raise


def show_setup_status():
    """Display current setup status"""
    config_manager = ConfigManager()
    
    if not config_manager.config_exists():
        print("Setup not completed. Run 'reddit-auto-mod setup' to begin.")
        return
    
    config = config_manager.load_config()
    
    print()
    print("=" * 60)
    print("Setup Status")
    print("=" * 60)
    print()
    
    # Credentials
    if config_manager.get_reddit_credentials():
        print("✓ Reddit credentials configured")
    else:
        print("✗ Reddit credentials not configured")
    
    if config_manager.get_openai_key():
        print("✓ OpenAI API key configured")
    else:
        print("✗ OpenAI API key not configured")
    
    # Subreddits
    if 'subreddits' in config and config['subreddits']:
        print(f"✓ Subreddits configured: {', '.join(config['subreddits'])}")
    else:
        print("✗ No subreddits configured")
    
    # Database
    if 'database_name' in config:
        print(f"✓ Database configured: {config['database_name']}")
    else:
        print("✗ Database not configured")
    
    # MongoDB
    if config_manager.get_mongodb_uri():
        print("✓ MongoDB URI configured")
    else:
        print("✗ MongoDB URI not configured")
    
    # Check for index files
    if 'subreddits' in config and config['subreddits']:
        index_dir = Path.home() / ".reddit-auto-mod" / "indexes"
        print()
        print("Index Files:")
        for subreddit in config['subreddits']:
            index_file = index_dir / f"{subreddit}.faiss"
            ids_file = index_dir / f"{subreddit}_ids.pkl"
            if index_file.exists() and ids_file.exists():
                print(f"  ✓ {subreddit}: Index files present")
            else:
                print(f"  ✗ {subreddit}: Index files missing")
    
    print()
