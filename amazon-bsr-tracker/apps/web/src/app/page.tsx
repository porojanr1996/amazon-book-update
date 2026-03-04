'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';
import { BookCard } from '../components/BookCard';

interface Book {
  id: string;
  asin: string;
  title: string;
  url: string;
  currentRank: number | null;
  lastUpdated: string | null;
}

export default function DashboardPage() {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [newBookUrl, setNewBookUrl] = useState('');
  const [tracking, setTracking] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000';

  useEffect(() => {
    fetchBooks();
  }, []);

  const fetchBooks = async () => {
    try {
      const response = await axios.get(`${apiUrl}/api/books`);
      setBooks(response.data);
    } catch (error) {
      console.error('Failed to fetch books:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTrackBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBookUrl.trim()) return;

    setTracking(true);
    try {
      await axios.post(`${apiUrl}/api/books/track`, { url: newBookUrl });
      setNewBookUrl('');
      fetchBooks();
      alert('Book added successfully!');
    } catch (error) {
      console.error('Failed to track book:', error);
      alert('Failed to add book. Please check the URL and try again.');
    } finally {
      setTracking(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          📊 Amazon BSR Tracker
        </h1>

        {/* Add Book Form */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Track New Book</h2>
          <form onSubmit={handleTrackBook} className="flex gap-4">
            <input
              type="text"
              value={newBookUrl}
              onChange={(e) => setNewBookUrl(e.target.value)}
              placeholder="Amazon URL or ASIN (e.g., B0CSZHZRSR)"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={tracking}
            />
            <button
              type="submit"
              disabled={tracking}
              className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition"
            >
              {tracking ? 'Adding...' : 'Add Book'}
            </button>
          </form>
        </div>

        {/* Books List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-semibold mb-6">Tracked Books</h2>
          
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : books.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No books tracked yet. Add your first book above!
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {books.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
