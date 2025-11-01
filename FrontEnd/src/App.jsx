import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp, User, MessageSquare, Home, Settings } from 'lucide-react';
import { CheckCircle, Trash2 } from 'lucide-react';

import { fetchQueueItems, takePostAction } from './services/api';
import Configure from './components/Configure';


const QueueItem = ({ item, onAction }) => {
  const [expanded, setExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleAction = async (approve) => {
    setIsProcessing(true);
    try {
      await takePostAction(item.id, approve, item.type);
      if (onAction) {
        onAction(item._id);
      }
    } catch (error) {
      console.error('Error taking action:', error);
      alert(`Failed to ${approve ? 'approve' : 'remove'} post: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const trimText = (text, maxLength = 150) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  const similarityScore = item.similarity_data?.similarity_score;
  const formattedSimilarityScore = similarityScore 
    ? `${(similarityScore * 100).toFixed(1)}%`
    : 'N/A';

  return (
    <div className="bg-gray-800 rounded-lg mb-3 border border-gray-700 hover:border-gray-600 transition-colors">
      {/* Collapsed View */}
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex gap-4">
          {/* Main Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                {/* Type Badge */}
                <span className={`inline-block px-2 py-1 rounded text-xs font-medium mb-2 ${
                  item.type === 'submission' ? 'bg-blue-900 text-blue-200' : 'bg-purple-900 text-purple-200'
                }`}>
                  {item.type === 'submission' ? 'Post' : 'Comment'}
                </span>

                {/* Title */}
                <h3 className="text-white font-medium mb-2 text-lg">{item.submission_title}</h3>
                
                {/* Author and Time */}
                <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
                  <span className="flex items-center gap-1">
                    <User size={14} />
                    u/{item.author}
                  </span>
                  <span>•</span>
                  <span>{new Date(item.created_utc * 1000).toLocaleString()}</span>
                </div>
                
                {/* Trimmed Text */}
                <div className="text-gray-300 text-sm mb-3 bg-gray-700/30 p-3 rounded">
                  <p className="whitespace-pre-wrap">
                    {expanded ? item.submission_text : trimText(item.submission_text)}
                  </p>
                </div>
                
                {/* Similarity Score */}
                <div className="mb-2">
                  <span className="px-3 py-1 bg-blue-900 text-blue-200 rounded text-sm">
                    Similarity: {formattedSimilarityScore}
                  </span>
                </div>

                {/* Post Summary */}
                {item.post_summary && (
                  <div className="text-sm text-gray-300 bg-gray-700/50 p-3 rounded mb-2">
                    <span className="font-medium text-gray-400">Summary:</span> {item.post_summary}
                  </div>
                )}

                {/* Rule Violations */}
                <div className="text-sm text-gray-300 bg-gray-700/50 p-3 rounded mb-3">
                  <span className="font-medium text-gray-400">Rule Violations:</span> {item.rule_violations?.error || 'No violations found'}
                </div>
              </div>
              
              {/* Expand Button */}
              <button className="text-gray-400 hover:text-white flex-shrink-0">
                {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Expanded View */}
      {expanded && (
        <div className="border-t border-gray-700 p-4 bg-gray-850">
          {/* Full Post Text */}
          <div className="mb-4">
            <h4 className="text-white font-medium mb-2 text-sm">Full Post Text:</h4>
            <p className="text-gray-300 text-sm whitespace-pre-wrap bg-gray-700/30 p-3 rounded">{item.submission_text}</p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 flex-wrap">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleAction(true);
              }}
              disabled={isProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <CheckCircle size={16} />
              {isProcessing ? 'Processing...' : 'Approve'}
            </button>
            <button 
              onClick={(e) => {
                e.stopPropagation();
                handleAction(false);
              }}
              disabled={isProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Trash2 size={16} />
              {isProcessing ? 'Processing...' : 'Remove'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const ModQueue = ({ selectedSubreddit, limit }) => {
  const [activeTab, setActiveTab] = useState('needs-review');
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await fetchQueueItems(activeTab, selectedSubreddit, limit);
        console.log('Received data:', data);
        // Ensure we're setting the state with the array of items
        setQueueItems(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching queue items:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [activeTab, selectedSubreddit, limit]);

  const handleItemAction = (itemId) => {
    // Remove the item from the list after action
    setQueueItems(prevItems => prevItems.filter(item => item._id !== itemId));
  };

  const tabs = [
    { id: 'needs-review', label: 'Needs Review' },
    { id: 'reported', label: 'Reported' },
    { id: 'removed', label: 'Removed' },
    { id: 'edited', label: 'Edited' },
    { id: 'unmoderated', label: 'Unmoderated' }
  ];

  return (
    <div>
      {/* Header */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">Queue</h1>
          <div className="text-gray-400 text-sm">
            <span className="mr-4">{selectedSubreddit}</span>
            <span>{limit} posts</span>
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-2 overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'bg-gray-900 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Queue Items */}
      <div className="p-4">
        {loading ? (
          <div className="text-center py-20">
            <div className="text-xl text-gray-400">Loading...</div>
          </div>
        ) : queueItems && queueItems.length > 0 ? (
          queueItems.map((item, index) => (
            <QueueItem key={index} item={item} onAction={handleItemAction} />
          ))
        ) : (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🐱</div>
            <h2 className="text-xl font-bold mb-2">Queue is clean.</h2>
            <p className="text-gray-400">Kitteh is pleased.</p>
          </div>
        )}
      </div>
    </div>
  );
};

const App = () => {
  const [currentPage, setCurrentPage] = useState('home');
  const [selectedSubreddit, setSelectedSubreddit] = useState('r/devTestModPro');
  const [limit, setLimit] = useState(10);

  return (
    <div className="flex min-h-screen bg-gray-900 text-white">
      {/* Left Sidebar */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex-shrink-0">
        <div className="p-4">
          <h2 className="text-xl font-bold mb-6">Mod Tools</h2>
          
          <nav className="space-y-2">
            <button
              onClick={() => setCurrentPage('home')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                currentPage === 'home'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Home size={20} />
              <span className="font-medium">Home</span>
            </button>
            
            <button
              onClick={() => setCurrentPage('configure')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                currentPage === 'configure'
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Settings size={20} />
              <span className="font-medium">Configure</span>
            </button>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {currentPage === 'home' ? (
          <ModQueue selectedSubreddit={selectedSubreddit} limit={limit} />
        ) : (
          <Configure 
            selectedSubreddit={selectedSubreddit}
            setSelectedSubreddit={setSelectedSubreddit}
            limit={limit}
            setLimit={setLimit}
          />
        )}
      </div>
    </div>
  );
};

export default App;
