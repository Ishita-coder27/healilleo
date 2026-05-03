// src/hooks/useChatPipeline.js
import { useContext } from "react"
import { Context } from "../context/ContextProvider"
import { getMissingVitals } from "../context/ContextActions"
import { sendChatMessage, clearChatSession } from "../services/api"

export function useChatPipeline(userId) {
  const { state, dispatch } = useContext(Context)

  /**
   * Send a query. Backend classifies buckets and fetches only missing vitals.
   * Frontend context tracks summary for display; backend session is the
   * authoritative cache for vitals.
   */
  const processQuery = async (message) => {
    const data = await sendChatMessage({
      userId,
      message,
      contextSummary: state.contextSummary,  // send accumulated summary
    })

    // Update frontend context: merge any newly seen vitals into local map
    if (data.vitals && Object.keys(data.vitals).length > 0) {
      dispatch({ type: "UPDATE_CONTEXT", payload: data.vitals })
    }

    // Merge new summary observations
    if (data.summary && Object.keys(data.summary).length > 0) {
      dispatch({ type: "UPDATE_SUMMARY", payload: data.summary })
    }

    return {
      answer: data.reply,
      buckets: data.buckets,
      vitals: data.vitals,
    }
  }

  const clearContext = async () => {
    await clearChatSession(userId)
    dispatch({ type: "RESET" })
  }

  return { processQuery, clearContext }
}