'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { format } from 'date-fns';

interface RankData {
  rank: number;
  category: string;
  timestamp: string;
}

interface BookData {
  book: {
    id: string;
    asin: string;
    title: string;
    url: string;
  };
  history: RankData[];
}

export default function BookDetailPage() {
  const params = useParams();
  const asin = params?.asin as string;
  const [bookData, setBookData] = useState<BookData | null>(null);
  const [loading, setLoading] = useState(true);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

  useEffect(() => {
    if (asin) {
      fetchBookData();
    }
  }, [asin]);

  const fetchBookData = async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/books/${asin}/history`);
      setBookData(response.data);
    } catch (error) {
      console.error('Failed to fetch book data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-gray-50 p-8">Loading...</div>;
  }

  if (!bookData) {
    return <div className="min-h-screen bg-gray-50 p-8">Book not found</div>;
  }

  const chartData = bookData.history
    .slice()
    .reverse()
    .map(item => ({
      date: format(new Date(item.timestamp), 'MMM dd'),
      rank: item.rank,
    }));

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link href="/" className="text-blue-600 hover:underline mb-4 inline-block">
          ← Back to Dashboard
        </Link>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {bookData.book.title}
        </h1>
        <p className="text-gray-600 mb-8">ASIN: {bookData.book.asin}</p>

        {/* Current Rank */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Current Rank</h2>
          <div className="text-5xl font-bold text-blue-600">
            #{bookData.history[0]?.rank.toLocaleString()}
          </div>
          <p className="text-gray-500 mt-2">
            Last updated: {format(new Date(bookData.history[0]?.timestamp), 'PPp')}
          </p>
        </div>

        {/* Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Ranking History</h2>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis reversed domain={['auto', 'auto']} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="rank" 
                stroke="#2563eb" 
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* History Table */}
        <div className="bg-white rounded-lg shadow-md p-6 mt-8">
          <h2 className="text-xl font-semibold mb-4">All Data Points</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date & Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {bookData.history.map((item, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {format(new Date(item.timestamp), 'PPp')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-blue-600">
                      #{item.rank.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {item.category}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
