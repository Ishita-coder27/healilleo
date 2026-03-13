import React, { useState } from "react";
import "./Tracker.css";

export default function SleepTracker({ open, onClose, onAskLLM }) {

  const [targetSleep, setTargetSleep] = useState(8);
  const [todaySleep, setTodaySleep] = useState(0);

  if (!open) return null;

    const askLLM = () => {
    onAskLLM("What should be my daily sleep intake in hours?");
    };

  return (
    <div className="tracker-overlay" onClick={onClose}>
      <div className="tracker-modal" onClick={(e)=>e.stopPropagation()}>

        <h2>😴 Sleep Tracker</h2>

        <label>Target Sleep (hours)</label>
        <input
          type="number"
          value={targetSleep}
          onChange={(e)=>setTargetSleep(e.target.value)}
        />

        <button className="ask-btn" onClick={askLLM}>
          Ask LLM what you should aim for
        </button>

        <div className="slider-section">

          <button onClick={()=>setTodaySleep(Math.max(0,todaySleep-1))}>-</button>

          <input
            type="range"
            min="0"
            max="12"
            value={todaySleep}
            onChange={(e)=>setTodaySleep(e.target.value)}
          />

          <button onClick={()=>setTodaySleep(Number(todaySleep)+1)}>+</button>

        </div>

        <p>Today's Sleep: {todaySleep} hrs</p>

        <button className="close-btn" onClick={onClose}>
          Close
        </button>

      </div>
    </div>
  );
}