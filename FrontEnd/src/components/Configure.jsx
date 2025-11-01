import React from 'react';

const Configure = ({ selectedSubreddit, setSelectedSubreddit, limit, setLimit }) => {
  const subreddits = [
    'r/devTestModPro',
    'r/explainlikeimfive',
    'r/programming',
    'r/technology'
  ];
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Configure</h1>
      
      <div className="bg-gray-800 rounded-lg p-6 max-w-2xl">
        <h2 className="text-xl font-semibold mb-4">Subreddit Selection</h2>
        
        <div className="mb-4">
          <label htmlFor="subreddit" className="block text-sm font-medium text-gray-400 mb-2">
            Select Subreddit
          </label>
          <select
            id="subreddit"
            value={selectedSubreddit}
            onChange={(e) => setSelectedSubreddit(e.target.value)}
            className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {subreddits.map(subreddit => (
              <option key={subreddit} value={subreddit}>
                {subreddit}
              </option>
            ))}
          </select>
          <p className="mt-2 text-sm text-gray-400">
            Choose the subreddit you want to moderate. This will filter the queue to show only posts and comments from the selected subreddit.
          </p>
        </div>

        <div className="mb-4">
          <label htmlFor="limit" className="block text-sm font-medium text-gray-400 mb-2">
            Post Limit
          </label>
          <select
            id="limit"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="w-full bg-gray-700 text-white border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {[10, 20, 30, 40, 50].map(value => (
              <option key={value} value={value}>
                {value} posts
              </option>
            ))}
          </select>
          <p className="mt-2 text-sm text-gray-400">
            Choose how many posts to fetch at a time. A lower limit means faster loading times.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Configure;
