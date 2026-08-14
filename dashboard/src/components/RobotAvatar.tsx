import React from 'react';

interface RobotAvatarProps {
  state: 'idle' | 'listening' | 'thinking' | 'speaking' | 'music' | 'alarm';
}

export const RobotAvatar: React.FC<RobotAvatarProps> = ({ state }) => {
  // Determine animation classes based on state
  const bodyAnimationClass = 
    state === 'listening' ? 'animate-pulse' :
    state === 'thinking' ? 'animate-bounce [animation-duration:1s]' :
    state === 'speaking' ? 'animate-bounce [animation-duration:0.8s]' :
    state === 'music' ? 'animate-bounce [animation-duration:0.5s]' :
    state === 'alarm' ? 'animate-ping [animation-duration:2s]' :
    'animate-none';

  // Floating ears animation offset
  const earAnimationClass =
    state === 'music' ? 'animate-bounce [animation-duration:0.25s]' :
    state === 'listening' ? 'translate-y-[-4px] scale-105 transition-all duration-200' :
    'animate-pulse [animation-duration:3s]';

  return (
    <div className="flex flex-col items-center justify-center select-none p-4">
      {/* SVG Container for the high-fidelity robot character */}
      <svg 
        width="220" 
        height="220" 
        viewBox="0 0 220 220" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        className="drop-shadow-[0_10px_20px_rgba(230,168,23,0.15)] dark:drop-shadow-[0_10px_25px_rgba(0,0,0,0.5)] transition-all duration-300"
      >
        <defs>
          {/* Metallic Gold radial gradient */}
          <radialGradient id="goldSphere" cx="35%" cy="30%" r="70%" fx="35%" fy="30%">
            <stop offset="0%" stopColor="#FFF2B2" />
            <stop offset="35%" stopColor="#F5D061" />
            <stop offset="75%" stopColor="#E6A817" />
            <stop offset="100%" stopColor="#B37800" />
          </radialGradient>

          {/* Glowing visor radial gradient */}
          <radialGradient id="visorGrad" cx="50%" cy="30%" r="70%">
            <stop offset="0%" stopColor="#2D2D2D" />
            <stop offset="100%" stopColor="#0F0F0F" />
          </radialGradient>

          {/* Mint green metallic reflection linear gradient */}
          <linearGradient id="mintReflection" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#39E5A3" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#39E5A3" stopOpacity="0" />
            <stop offset="100%" stopColor="#39E5A3" stopOpacity="0.4" />
          </linearGradient>

          {/* Shadow filters for 3D depth */}
          <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="6" stdDeviation="5" floodColor="#4A2306" floodOpacity="0.3" />
          </filter>
        </defs>

        {/* -------------------- FLOATING EARS -------------------- */}
        <g className={`transition-all duration-300 ${earAnimationClass}`} transform-origin="110px 115px">
          {/* Left Ear */}
          <g transform="translate(0, 0)">
            {/* Base shadow */}
            <path d="M 52,80 C 47,60 56,32 76,32 C 86,32 86,57 81,72 C 79,78 69,82 52,80 Z" fill="#4A2306" />
            {/* Gold Ear Body */}
            <path d="M 53,78 C 49,60 57,34 75,34 C 84,34 84,57 80,71 C 78,76 69,80 53,78 Z" fill="url(#goldSphere)" />
            {/* Mint Green Bottom Highlight */}
            <path d="M 53,78 C 58,74 68,76 72,71" stroke="#39E5A3" strokeWidth="3" strokeLinecap="round" />
            {/* Inner Ear shadow detail */}
            <path d="M 62,68 C 60,58 65,48 72,46" stroke="#B37800" strokeWidth="2.5" strokeLinecap="round" />
          </g>

          {/* Right Ear */}
          <g transform="translate(0, 0)">
            {/* Base shadow */}
            <path d="M 168,80 C 173,60 164,32 144,32 C 134,32 134,57 139,72 C 141,78 151,82 168,80 Z" fill="#4A2306" />
            {/* Gold Ear Body */}
            <path d="M 167,78 C 171,60 163,34 145,34 C 136,34 136,57 140,71 C 142,76 151,80 167,78 Z" fill="url(#goldSphere)" />
            {/* Mint Green Bottom Highlight */}
            <path d="M 167,78 C 162,74 152,76 148,71" stroke="#39E5A3" strokeWidth="3" strokeLinecap="round" />
            {/* Inner Ear shadow detail */}
            <path d="M 158,68 C 160,58 155,48 148,46" stroke="#B37800" strokeWidth="2.5" strokeLinecap="round" />
          </g>
        </g>

        {/* -------------------- HEADPHONES (MUSIC STATE) -------------------- */}
        {state === 'music' && (
          <g className="animate-pulse">
            {/* Headphone Arc */}
            <path d="M 55,100 A 55,55 0 0,1 165,100" fill="none" stroke="#2A2A2A" strokeWidth="6" />
            {/* Left Ear Cup */}
            <rect x="42" y="98" width="16" height="32" rx="8" fill="#FF3366" stroke="#1F1F1F" strokeWidth="3" />
            <circle cx="50" cy="114" r="4" fill="#E6A817" />
            {/* Right Ear Cup */}
            <rect x="162" y="98" width="16" height="32" rx="8" fill="#FF3366" stroke="#1F1F1F" strokeWidth="3" />
            <circle cx="170" cy="114" r="4" fill="#E6A817" />
          </g>
        )}

        {/* -------------------- ROBOT BODY -------------------- */}
        <g className={`transition-all duration-300 ${bodyAnimationClass}`} transform-origin="110px 135px">
          {/* Main sphere shadow */}
          <circle cx="110" cy="135" r="54" fill="#4A2306" />

          {/* Main Gold Sphere Body */}
          <circle cx="110" cy="135" r="52" fill="url(#goldSphere)" />

          {/* Mint Green Bottom Reflective highlights */}
          <path d="M 70,168 C 80,182 100,187 120,186 C 140,185 150,172 150,172" stroke="#39E5A3" strokeWidth="5" fill="none" strokeLinecap="round" opacity="0.9" />

          {/* White top light highlight */}
          <ellipse cx="90" cy="98" rx="20" ry="8" fill="#FFFFFF" opacity="0.3" transform="rotate(-15 90 98)" />

          {/* Side ear-piece circles */}
          <circle cx="58" cy="135" r="8" fill="#4A2306" />
          <circle cx="58" cy="135" r="6" fill="#1A1A1A" />
          <circle cx="162" cy="135" r="8" fill="#4A2306" />
          <circle cx="162" cy="135" r="6" fill="#1A1A1A" />

          {/* -------------------- BLACK VISOR -------------------- */}
          {/* Visor Bezel */}
          <path d="M 73,130 C 67,112 153,112 147,130 C 153,148 67,148 73,130 Z" fill="#4A2306" />
          {/* Visor Screen */}
          <path 
            d="M 75,130 C 70,115 150,115 145,130 C 150,145 70,145 75,130 Z" 
            fill={state === 'alarm' ? '#3B0000' : 'url(#visorGrad)'} 
            className="transition-colors duration-300"
          />

          {/* -------------------- VISOR SCREEN TEXT / FACE -------------------- */}
          {/* Cyan Glow Eyes */}
          <g className="transition-all duration-350">
            {state === 'thinking' ? (
              // Loading/Thinking eyes
              <g className="animate-spin" transform-origin="110px 130px">
                <circle cx="92" cy="128" r="5" fill="none" stroke="#00D2FF" strokeWidth="2.5" strokeDasharray="6 3" />
                <circle cx="128" cy="128" r="5" fill="none" stroke="#00D2FF" strokeWidth="2.5" strokeDasharray="6 3" />
              </g>
            ) : state === 'listening' ? (
              // Listening wide/perked eyes
              <g>
                <circle cx="94" cy="128" r="7" fill="#00D2FF" className="animate-pulse" />
                <circle cx="126" cy="128" r="7" fill="#00D2FF" className="animate-pulse" />
                {/* Pupil details */}
                <circle cx="94" cy="128" r="2.5" fill="#1A1A1A" />
                <circle cx="126" cy="128" r="2.5" fill="#1A1A1A" />
              </g>
            ) : state === 'alarm' ? (
              // Sad/flashing alarm eyes
              <g>
                <path d="M 88,131 L 98,125" stroke="#FF3366" strokeWidth="3.5" strokeLinecap="round" />
                <path d="M 132,131 L 122,125" stroke="#FF3366" strokeWidth="3.5" strokeLinecap="round" />
              </g>
            ) : (
              // Default/Idle/Speaking eyes (Cute square-ish pixel style)
              <g>
                <rect x="89" y="123" width="9" height="9" rx="2" fill="#00D2FF" />
                <rect x="122" y="123" width="9" height="9" rx="2" fill="#00D2FF" />
              </g>
            )}
          </g>

          {/* Cute Cat Mouth "w" or state-specific mouth */}
          <g className="transition-all duration-300">
            {state === 'alarm' ? (
              // Sad mouth "n"
              <path d="M 106,138 Q 110,134 114,138" fill="none" stroke="#FF3366" strokeWidth="2.5" strokeLinecap="round" />
            ) : state === 'speaking' ? (
              // Animating speaking oval mouth
              <ellipse cx="110" cy="136" rx="4" ry="4" fill="#00D2FF" className="animate-ping [animation-duration:0.2s]" />
            ) : state === 'listening' ? (
              // Surprised open mouth "o"
              <circle cx="110" cy="136" r="3" fill="#00D2FF" />
            ) : (
              // Cute cat mouth "w"
              <path d="M 104,135 Q 107,138 110,135 Q 113,138 116,135" fill="none" stroke="#00D2FF" strokeWidth="2.5" strokeLinecap="round" />
            )}
          </g>

          {/* -------------------- CRYING TEARS (ALARM STATE) -------------------- */}
          {state === 'alarm' && (
            <g className="animate-bounce [animation-duration:1s]">
              {/* Left Tear */}
              <path d="M 94,132 C 94,142 90,148 90,154" fill="none" stroke="#00D2FF" strokeWidth="2.5" strokeLinecap="round" />
              {/* Right Tear */}
              <path d="M 126,132 C 126,142 130,148 130,154" fill="none" stroke="#00D2FF" strokeWidth="2.5" strokeLinecap="round" />
            </g>
          )}
        </g>
      </svg>

      {/* Decorative floating platform shadow underneath */}
      <div 
        className={`w-24 h-3 bg-black/10 dark:bg-black/35 rounded-full blur-[2px] transition-all duration-300 ${
          state === 'music' ? 'scale-75 opacity-70 animate-pulse' :
          state === 'speaking' ? 'scale-90 opacity-80' :
          state === 'listening' ? 'scale-95 opacity-90' :
          'scale-100 opacity-100 animate-pulse [animation-duration:2.5s]'
        }`}
      />
    </div>
  );
};
