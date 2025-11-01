"""Main CLI entry point for Reddit Auto Mod"""
import sys
import argparse
from cli.config import interactive_config, show_config, clear_config, ConfigManager, import_config_from_file
from cli.setup import interactive_setup, show_setup_status, build_indexes_for_subreddits
from cli.start import start_all, show_status


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        prog='reddit-auto-mod',
        description='Reddit Auto Mod - Automated moderation assistant for Reddit',
        epilog='For more information, visit: https://github.com/Bhavinrathava/reddit-auto-mod'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Configure Reddit and OpenAI credentials'
    )
    config_parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration (credentials masked)'
    )
    config_parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear all configuration'
    )
    config_parser.add_argument(
        '--file',
        type=str,
        metavar='PATH',
        help='Import configuration from a JSON file'
    )
    
    # Setup command
    setup_parser = subparsers.add_parser(
        'setup',
        help='Set up subreddits, MongoDB collections, and FAISS indexes'
    )
    setup_parser.add_argument(
        '--status',
        action='store_true',
        help='Show current setup status'
    )
    setup_parser.add_argument(
        '--build-indexes',
        action='store_true',
        help='Build FAISS indexes for configured subreddits'
    )
    
    # Start command
    start_parser = subparsers.add_parser(
        'start',
        help='Start all services (frontend, backend APIs, and scheduler)'
    )
    start_parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of all running services'
    )
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == 'config':
        if args.show:
            show_config()
        elif args.clear:
            clear_config()
        elif args.file:
            if not import_config_from_file(args.file):
                sys.exit(1)
        else:
            interactive_config()
    
    elif args.command == 'setup':
        if args.status:
            show_setup_status()
        elif args.build_indexes:
            # Build indexes for configured subreddits
            config_manager = ConfigManager()
            config = config_manager.load_config()
            
            if not config or 'subreddits' not in config:
                print("ERROR: No subreddits configured.")
                print("Run 'reddit-auto-mod setup' first to configure subreddits.")
                sys.exit(1)
            
            mongodb_uri = config.get('mongodb_uri')
            db_name = config.get('database_name', 'mainDB')
            subreddits = config['subreddits']
            
            if not mongodb_uri:
                print("ERROR: MongoDB URI not configured.")
                print("Run 'reddit-auto-mod setup' to configure MongoDB.")
                sys.exit(1)
            
            try:
                build_indexes_for_subreddits(subreddits, mongodb_uri, db_name)
            except Exception as e:
                print(f"Error building indexes: {e}")
                sys.exit(1)
        else:
            interactive_setup()
    
    elif args.command == 'start':
        if args.status:
            show_status()
        else:
            start_all()
    
    elif args.command == 'version':
        from cli import __version__
        print(f"reddit-auto-mod version {__version__}")
    
    elif args.command is None:
        # No command provided, show help
        parser.print_help()
        print()
        print("Quick start:")
        print("  1. Configure credentials: reddit-auto-mod config")
        print("  2. Set up subreddits and database: reddit-auto-mod setup")
        print("  3. Start the backend services and begin moderating")
        print()
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
