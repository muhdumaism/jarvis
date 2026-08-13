import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  danger?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  active = false,
  danger = false,
  children,
  className = '',
  ...props
}) => {
  let buttonStyle = 'btn-neo';
  if (active) {
    buttonStyle = 'btn-neo-active';
  } else if (danger) {
    buttonStyle = 'btn-neo-danger';
  }

  return (
    <button className={`${buttonStyle} ${className}`} {...props}>
      {children}
    </button>
  );
};
