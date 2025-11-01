import React, { useState, useEffect } from 'react';
import { fetchQueueItems } from '../services/api';
import { ChevronDown, ChevronUp, User } from 'lucide-react';
import { CheckCircle, Trash2 } from 'lucide-react';


const QueueItem = ({ item }) => {
  const [expanded, setExpanded] = useState(false);

  console.log('Rendering item:', item);

  const trimText = (text, maxLength = 150) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  // Format similarity score
  const similarityScore = item.similarity_data?.similarity_score;
  const formattedSimilarityScore = similarityScore 
    ? `${(similarityScore * 100).toFixed(1)}%`
    : 'N/A';

  console.log('Item fields:', {
    title: item.submission_title,
    text: item.submission_text,
    score: similarityScore,
    summary: item.post_summary,
    violations: item.rule_violations
  });

  return (
    <div className="bg-gray-800 rounded-lg mb-3 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="p-4">
        <div className="flex-1">
          {/* Type Badge */}
          <span className={`inline-block px-2 py-1 rounded text-xs font-medium mb-2 ${
            item.type === 'submission' ? 'bg-blue-900 text-blue-200' : 'bg-purple-900 text-purple-200'
          }`}>
            {item.type === 'submission' ? 'Post' : 'Comment'}
          </span>
          
          {/* Title */}
          <h3 className="text-white font-medium mb-2 text-lg">
            {item.submission_title || 'No title'}
          </h3>
          
          {/* Author and Time */}
          <div className="flex items-center gap-3 text-sm text-gray-400 mb-3">
            <span className="flex items-center gap-1">
              <User size={14} />
              u/{item.author || 'Unknown'}
            </span>
            <span>•</span>
            <span>{new Date(item.created_utc * 1000).toLocaleString()}</span>
          </div>
          
          {/* Post Text */}
          <div className="text-gray-300 text-sm mb-3 bg-gray-700/30 p-3 rounded">
            <p className="whitespace-pre-wrap">
              {expanded ? (item.submission_text || 'No content') : trimText(item.submission_text || 'No content')}
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

          {/* Action Buttons */}
          <div className="flex gap-2 flex-wrap">
            <button className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm transition-colors">
              <CheckCircle size={16} />
              Approve
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded text-sm transition-colors">
              <Trash2 size={16} />
              Remove
            </button>
          </div>
          
          {/* Expand Button */}
          <button 
            onClick={() => setExpanded(!expanded)}
            className="mt-3 text-gray-400 hover:text-white text-sm flex items-center gap-1"
          >
            {expanded ? (
              <>
                <ChevronUp size={16} />
                Show Less
              </>
            ) : (
              <>
                <ChevronDown size={16} />
                Show More
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const Home = () => {
  const [activeTab, setActiveTab] = useState('needs-review');
  const [queueItems, setQueueItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadQueueItems = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log('Loading queue for tab:', activeTab);
        const data = await fetchQueueItems(activeTab, 'devTestModPro', 10);
        console.log('Loaded queue items:', data);
        setQueueItems(data);
      } catch (err) {
        console.error('Error loading queue items:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadQueueItems();
  }, [activeTab]);

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
        <h1 className="text-2xl font-bold mb-4">Queue</h1>
        
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
        ) : error ? (
          <div className="text-center py-20">
            <div className="text-xl text-red-400">Error: {error}</div>
          </div>
        ) : queueItems.length > 0 ? (
          queueItems.map(item => (
            <QueueItem key={item._id} item={item} />
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

export default Home;
