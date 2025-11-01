const API_BASE_URL = 'http://127.0.0.1:8000';
const POST_PROCESSING_URL = `${API_BASE_URL}/post-processing`;

export const fetchQueueItems = async (queueType, subreddit, limit) => {
  try {
    // Remove r/ prefix if present
    const cleanSubreddit = subreddit.replace('r/', '');
    console.log('Making request with:', { cleanSubreddit, limit, queueType });
    const url = `${API_BASE_URL}/api/fetch/${encodeURIComponent(cleanSubreddit)}?queue_type=${encodeURIComponent(queueType)}${limit ? `&limit=${limit}` : ''}`;
    console.log('Request URL:', url);
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to fetch queue items');
    }
    const data = await response.json();
    console.log('Response data:', data);
    return data;
  } catch (error) {
    throw new Error('Failed to fetch queue items: ' + error.message);
  }
};

export const takePostAction = async (submissionId, approve, itemType) => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/post/action`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        submission_id: submissionId,
        approve: approve,
        item_type: itemType
      })
    });
    
    if (!response.ok) {
      throw new Error('Failed to take post action');
    }
    
    const data = await response.json();
    console.log('Action response:', data);
    return data;
  } catch (error) {
    throw new Error('Failed to take post action: ' + error.message);
  }
};

// Health Check Function
export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${POST_PROCESSING_URL}/health`);
    if (!response.ok) {
      throw new Error('API health check failed');
    }
    return await response.json();
  } catch (error) {
    throw new Error('API health check failed: ' + error.message);
  }
};
