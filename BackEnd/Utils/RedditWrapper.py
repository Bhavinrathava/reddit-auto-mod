import praw

class RedditWrapper:

    def __init__(self, credentials, subreddits):
        self.credentials = credentials
        self.subreddits = subreddits
        
        # Initialize the Reddit instance using PRAW
        self.reddit = praw.Reddit(
            client_id=credentials['client_id'],
            client_secret=credentials['client_secret'],
            user_agent=credentials['user_agent'],
            username=credentials['username'],
            password=credentials['password']
        )

    def _process_queue_item(self, item, itemtype = 'modqueue'):
        """
        Process a single queue item and return its data in a standardized format
        
        Args:
            item: A PRAW item object (submission or comment)
            
        Returns:
            dict: Processed item data if not clicked, None if already clicked
        """
        if item.clicked:
            return None
            
        item_data = {
            'id': item.id,
            'type': 'submission' if hasattr(item, 'title') else 'comment',
            'author': str(item.author) if item.author else '[deleted]',
            'created_utc': item.created_utc,
            'permalink': item.permalink,
            'itemType': itemtype,
        }
        
        if hasattr(item, 'title'):  # Submission
            item_data['submission_title'] = item.title
            item_data['url'] = item.url
            item_data['submission_text'] = item.selftext
        else:  # Comment
            item_data['body'] = item.body
        
        item.clicked = True
        return item_data

    def getQueueItems(self, subreddit):
        """
        Get all items from various moderation queues for a subreddit
        
        Args:
            subreddit (str): Name of the subreddit
            
        Returns:
            list: List of processed queue items
        """
        subreddit = self.reddit.subreddit(subreddit)
        modqueue_data = []

        # Define queue types to process
        queues = [
            (subreddit.mod.modqueue,"modqueue"),
            (subreddit.mod.unmoderated,"unmoderated"),
            (subreddit.mod.reports,"reported"),
            (subreddit.mod.edited, "edited"),
        ]
        
        # Process each queue
        for queue, queueType in queues:
            for item in queue(limit=None):
                item_data = self._process_queue_item(item,queueType )
                if item_data:
                    modqueue_data.append(item_data)
        
        return modqueue_data
    

    def takeAction(self, itemDetails, approve):
        """
        Take moderation action (approve/remove) on a Reddit item
        
        Args:
            itemDetails (dict): Dictionary containing item details (id and type)
            approve (bool): True to approve, False to remove
            
        Raises:
            Exception: If item type is invalid or action fails
        """
        try:
            # Get the item from Reddit
            if itemDetails['type'] == 'submission':
                item = self.reddit.submission(id=itemDetails['id'])
            elif itemDetails['type'] == 'comment':
                item = self.reddit.comment(id=itemDetails['id'])
            else:
                raise ValueError(f"Invalid item type: {itemDetails['type']}")
            
            # Take the action
            if approve:
                item.mod.approve()
            else:
                item.mod.remove()
                
            return True
            
        except Exception as e:
            print(f"Error taking action on Reddit item: {str(e)}")
            raise

        

if __name__ == "__main__":
    # Load credentials from config file instead of hardcoding
    try:
        from cli.config import ConfigManager
        config_manager = ConfigManager()
        credentials = config_manager.get_reddit_credentials()
        
        if not credentials:
            print("No credentials found. Please run 'reddit-auto-mod config' to set up credentials.")
            exit(1)
        
        redditWrapper = RedditWrapper(credentials=credentials, subreddits=["devTestModPro"])
        print(redditWrapper.getQueueItems("devTestModPro"))
    except Exception as e:
        print(f"Error loading credentials: {e}")
        print("Please run 'reddit-auto-mod config' to set up credentials.")
        exit(1)
