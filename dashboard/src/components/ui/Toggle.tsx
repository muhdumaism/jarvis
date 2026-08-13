import React from 'react';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export const Toggle: React.FC<ToggleProps> = ({ checked, onChange, disabled = false }) => {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`${
        checked ? 'switch-neo-active' : 'switch-neo'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span className="switch-thumb-neo" />
    </button>
  );
};
