// src/context/ContextProvider.jsx

import { createContext, useReducer } from "react"
import { createInitialState } from "./ContextStore"
import { updateContext, updateSummary } from "./ContextActions"

export const Context = createContext()

function reducer(state, action) {
  switch (action.type) {
    case "UPDATE_CONTEXT":
      return updateContext(state, action.payload)

    case "UPDATE_SUMMARY":
      return updateSummary(state, action.payload)

    case "RESET":
      return createInitialState()

    default:
      return state
  }
}

export const ContextProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, createInitialState())

  return (
    <Context.Provider value={{ state, dispatch }}>
      {children}
    </Context.Provider>
  )
}