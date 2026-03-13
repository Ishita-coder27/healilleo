import { useState } from "react";
import "./BMICalculator.css";

export default function BMICalculator({ open, onClose }) {
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [bmi, setBmi] = useState(null);
  const [category, setCategory] = useState("");

  if (!open) return null;

  const calculateBMI = () => {
    if (!height || !weight) return;

    const h = height / 100;
    const value = (weight / (h * h)).toFixed(1);

    let cat = "";
    if (value < 18.5) cat = "Underweight";
    else if (value < 25) cat = "Normal";
    else if (value < 30) cat = "Overweight";
    else cat = "Obese";

    setBmi(value);
    setCategory(cat);
  };

  return (
    <div className="bmi-overlay">
      <div className="bmi-modal">
        <div className="bmi-header">
          <h2>BMI Calculator</h2>
          <button className="bmi-close" onClick={onClose}>✕</button>
        </div>

        <div className="bmi-body">
          <div className="bmi-field">
            <label>Height (cm)</label>
            <input
              type="number"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              placeholder="170"
            />
          </div>

          <div className="bmi-field">
            <label>Weight (kg)</label>
            <input
              type="number"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="70"
            />
          </div>

          <button className="bmi-calc-btn" onClick={calculateBMI}>
            Calculate
          </button>

          {bmi && (
            <div className="bmi-result">
              <div className="bmi-value">{bmi}</div>
              <div className="bmi-category">{category}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}