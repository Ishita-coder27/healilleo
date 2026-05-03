// src/context/ContextActions.js

export function getMissingVitals(state, requiredVitals) {
  return requiredVitals.filter(v => !state.contextMap.has(v))
}

export function updateContext(state, fetchedVitals) {
  const newMap = new Map(state.contextMap)
  const newVitals = { ...state.contextVitals }

  for (const vital in fetchedVitals) {
    newMap.set(vital, true)
    newVitals[vital] = fetchedVitals[vital]
  }

  return {
    ...state,
    contextMap: newMap,
    contextVitals: newVitals
  }
}

export function updateSummary(state, newSummary) {
  const merge = (oldArr, newArr) =>
    [...new Set([...oldArr, ...(newArr || [])])]

  return {
    ...state,
    contextSummary: {
      issues: merge(state.contextSummary.issues, newSummary.issues),
      advice_given: merge(state.contextSummary.advice_given, newSummary.advice_given),
      observations: merge(state.contextSummary.observations, newSummary.observations)
    }
  }
}