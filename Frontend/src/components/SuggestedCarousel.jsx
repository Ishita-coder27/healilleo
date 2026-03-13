import { useState, useEffect, useRef, useCallback } from "react";

const QUESTIONS = [
  { icon: "🩺", text: "What do my recent blood test results mean?" },
  { icon: "💊", text: "Are there side effects to my current medications?" },
  { icon: "😴", text: "How can I improve my sleep quality?" },
  { icon: "🍎", text: "What diet changes help with high blood pressure?" },
  { icon: "🏃", text: "How much exercise should I do per week?" },
  { icon: "🤒", text: "I have a persistent headache — what could it be?" },
];

const AUTO_DELAY   = 3000;
const ITEM_STAGGER = 180;  // ms between each row appearing/disappearing
const ITEM_DUR     = 500;  // ms per item animation

export default function SuggestedCarousel({ onSelect }) {
  const [current,   setCurrent]   = useState(0);
  const [direction, setDirection] = useState("next");
  const [animating, setAnimating] = useState(false);
  const [showAll,   setShowAll]   = useState(false);
  const [closing,   setClosing]   = useState(false);
  const timerRef   = useRef(null);
  const closeTimer = useRef(null);
  const gridRef    = useRef(null);

  /* ── Advance ── */
  const goTo = useCallback((next, dir) => {
    if (animating) return;
    setDirection(dir);
    setAnimating(true);
    setTimeout(() => { setCurrent(next); setAnimating(false); }, 380);
  }, [animating]);

  const goNext = useCallback(() => goTo((current + 1) % QUESTIONS.length, "next"), [current, goTo]);
  const goPrev = useCallback(() => goTo((current - 1 + QUESTIONS.length) % QUESTIONS.length, "prev"), [current, goTo]);

  /* ── Auto-advance ── */
  const resetTimer = useCallback(() => {
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(goNext, AUTO_DELAY);
  }, [goNext]);

  useEffect(() => {
    resetTimer();
    return () => clearTimeout(timerRef.current);
  }, [current, resetTimer]);

  const pauseTimer  = () => clearTimeout(timerRef.current);
  const resumeTimer = () => resetTimer();

  /* ── Toggle with retract ── */
  const toggleAll = () => {
    if (showAll && !closing) {
      setClosing(true);
      clearTimeout(closeTimer.current);
      // Wait for last item to finish retracting before unmounting
      const totalMs = (QUESTIONS.length - 1) * ITEM_STAGGER + ITEM_DUR + 40;
      closeTimer.current = setTimeout(() => {
        setShowAll(false);
        setClosing(false);
      }, totalMs);
    } else if (!showAll) {
      setClosing(false);
      setShowAll(true);
    }
  };

  useEffect(() => () => clearTimeout(closeTimer.current), []);

  /* ── Scroll page so grid bottom clears the floating chatbar ── */
  useEffect(() => {
    if (showAll && !closing && gridRef.current) {
      const t = setTimeout(() => {
        const grid = gridRef.current;
        if (!grid) return;

        // Measure where the grid bottom sits in the viewport
        const gridBottom = grid.getBoundingClientRect().bottom;

        // Find the chatbar height — it's the .floating-input-wrap fixed element
        const chatbar = document.querySelector(".floating-input-wrap");
        const chatbarHeight = chatbar ? chatbar.offsetHeight + 16 : 120; // 16px breathing room

        const viewportBottom = window.innerHeight;
        const overlap = gridBottom - (viewportBottom - chatbarHeight);

        if (overlap > 0) {
          window.scrollBy({ top: overlap + 48, behavior: "smooth" });
        }
      }, 80); // wait for grid to render and animate open
      return () => clearTimeout(t);
    }
  }, [showAll, closing]);

  const q = QUESTIONS[current];

  return (
    <div className="sc-wrapper">
      <p className="suggested-label">Try asking…</p>

      {/* Carousel row */}
      <div className="sc-stage" onMouseEnter={pauseTimer} onMouseLeave={resumeTimer}>
        <button className="sc-arrow" onClick={() => { goPrev(); resetTimer(); }} aria-label="Previous">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6"/>
          </svg>
        </button>

        <div className={`sc-card-wrap ${animating ? `sc-exit-${direction}` : "sc-enter"}`}>
          <button className="sc-chip" onClick={() => onSelect?.(q.text)}>
            <span className="sc-chip-icon">{q.icon}</span>
            <span className="sc-chip-text">{q.text}</span>
          </button>
        </div>

        <button className="sc-arrow" onClick={() => { goNext(); resetTimer(); }} aria-label="Next">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 18l6-6-6-6"/>
          </svg>
        </button>
      </div>

      {/* Dots + View all — always inside the same card */}
      <div className="sc-bottom-row">
        <div className="sc-dots">
          {QUESTIONS.map((_, i) => (
            <button
              key={i}
              className={`sc-dot ${i === current ? "sc-dot-active" : ""}`}
              onClick={() => { goTo(i, i > current ? "next" : "prev"); resetTimer(); }}
              aria-label={`Question ${i + 1}`}
            />
          ))}
        </div>
        <button className="sc-viewall-btn" onClick={toggleAll}>
          {showAll ? "Hide" : "View all"}
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4"
               strokeLinecap="round" strokeLinejoin="round"
               style={{ transform: showAll ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s ease" }}>
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>
      </div>

      {/* Inline question grid — part of the same card, no absolute positioning */}
      {showAll && (
        <div
          className="sc-all-grid"
          ref={gridRef}
        >
          {QUESTIONS.map((q, i) => {
            const row = Math.floor(i / 2);           // 0, 0, 1, 1, 2, 2
            const totalRows = Math.ceil(QUESTIONS.length / 2); // 3
            const enterDelay = row * ITEM_STAGGER;
            const exitDelay  = (totalRows - 1 - row) * ITEM_STAGGER; // row 2 exits first
            return (
              <button
                key={i}
                className={[
                  "sc-all-item",
                  i === current ? "sc-all-item-active" : "",
                  closing ? "sc-all-item-exit" : "sc-all-item-enter",
                ].join(" ")}
                style={{ animationDelay: `${closing ? exitDelay : enterDelay}ms` }}
                onClick={() => { onSelect?.(q.text); toggleAll(); }}
              >
                <span className="sc-all-icon">{q.icon}</span>
                <span className="sc-all-text">{q.text}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}