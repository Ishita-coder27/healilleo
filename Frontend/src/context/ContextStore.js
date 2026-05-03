// src/context/ContextStore.js

export const createInitialState = () => ({
  contextMap: new Map(),
  contextVitals: {},
  contextSummary: {
    issues: [],
    advice_given: [],
    observations: []
  }
})