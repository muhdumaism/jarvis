import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  inset?: boolean;
  children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ inset = false, children, className = '', ...props }) => {
  return (
    <div
      className={`${inset ? 'card-neo-inset' : 'card-neo'} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};
