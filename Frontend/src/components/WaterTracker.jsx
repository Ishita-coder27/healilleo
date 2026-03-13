import React, { useState } from "react";
import "./Tracker.css";

export default function WaterTracker({ open, onClose, onAskLLM }) {

  const [targetWater, setTargetWater] = useState(3);
  const [todayWater, setTodayWater] = useState(0);

  if (!open) return null;

    const askLLM = () => {
    onAskLLM("What should be my daily water intake in litres?");
    };

  return (
    <div className="tracker-overlay" onClick={onClose}>
      <div className="tracker-modal" onClick={(e)=>e.stopPropagation()}>

        <h2>💧 Water Tracker</h2>

        <label>Target Water Intake (Litres)</label>
        <input
          type="number"
          value={targetWater}
          onChange={(e)=>setTargetWater(e.target.value)}
        />

        <button className="ask-btn" onClick={askLLM}>
          Ask LLM what you should aim for
        </button>

        <div className="slider-section">

          <button onClick={()=>setTodayWater(Math.max(0,todayWater-0.25))}>-</button>

          <input
            type="range"
            min="0"
            max="5"
            step="0.25"
            value={todayWater}
            onChange={(e)=>setTodayWater(e.target.value)}
          />

          <button onClick={()=>setTodayWater(Number(todayWater)+0.25)}>+</button>

        </div>

        <p>Today's Intake: {todayWater} L</p>

        <button className="close-btn" onClick={onClose}>
          Close
        </button>

      </div>
    </div>
  );
}