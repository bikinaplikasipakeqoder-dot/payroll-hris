import { ReactNode } from 'react';

interface CardProps {
  className?: string;
  children: ReactNode;
  title?: string;
}

export default function Card({ className = '', children, title }: CardProps) {
  return (
    <div className={`bg-white shadow-sm rounded-xl p-6 ${className}`}>
      {title && (
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      )}
      {children}
    </div>
  );
}
