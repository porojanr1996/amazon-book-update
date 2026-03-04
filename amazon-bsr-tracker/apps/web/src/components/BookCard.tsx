import Link from 'next/link';
import { format } from 'date-fns';

interface BookCardProps {
  book: {
    id: string;
    asin: string;
    title: string;
    url: string;
    currentRank: number | null;
    lastUpdated: string | null;
  };
}

export function BookCard({ book }: BookCardProps) {
  return (
    <Link href={`/books/${book.asin}`}>
      <div className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer">
        <h3 className="font-semibold text-lg mb-2 line-clamp-2">{book.title}</h3>
        <p className="text-gray-600 text-sm mb-4">ASIN: {book.asin}</p>
        
        {book.currentRank ? (
          <div className="mb-2">
            <div className="text-3xl font-bold text-blue-600">
              #{book.currentRank.toLocaleString()}
            </div>
            <div className="text-sm text-gray-500">Current Rank</div>
          </div>
        ) : (
          <div className="text-gray-400 mb-2">No ranking data yet</div>
        )}

        {book.lastUpdated && (
          <p className="text-xs text-gray-500">
            Updated: {format(new Date(book.lastUpdated), 'PPp')}
          </p>
        )}
      </div>
    </Link>
  );
}
