import { useEffect, useReducer, useRef } from 'react';
import type { AnswerProvider, AskResponse, DeskState, DeskViewModel, PolicyClient } from '../contracts/policy';

type Action = { type: 'question'; value: string } | { type: 'provider'; value: AnswerProvider }
  | { type: 'begin'; question: string } | { type: 'result'; value: AskResponse }
  | { type: 'error'; value: string };
const initialState: DeskState = {
  question: '', provider: 'openai', submittedQuestion: '', status: 'idle', answer: '', response: null, error: null,
};
function reducer(state: DeskState, action: Action): DeskState {
  switch (action.type) {
    case 'question': return { ...state, question: action.value };
    case 'provider': return { ...state, provider: action.value };
    case 'begin': return { ...state, status: 'loading', submittedQuestion: action.question, answer: '', response: null, error: null };
    case 'result': return { ...state, status: 'success', response: action.value, answer: action.value.answer, error: null };
    case 'error': return { ...state, status: 'error', error: action.value };
  }
}

export function usePolicyDesk(client: PolicyClient): DeskViewModel {
  const [state, dispatch] = useReducer(reducer, initialState);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => { pending.current?.abort(); pending.current = null; }, []);
  const title = (name: string) => state.response?.routed_documents.find((doc) => doc.document_name === name)?.title
    ?? name.replace(/\.pdf$/i, '').replace(/^northstar-/, '').replaceAll('-', ' ');

  async function ask() {
    if (pending.current) return;
    const question = state.question.trim();
    if (!question) { dispatch({ type: 'error', value: 'Please enter a question.' }); return; }
    const controller = new AbortController();
    pending.current = controller;
    dispatch({ type: 'begin', question });
    try {
      const result = await client.ask(question, state.provider, controller.signal);
      if (!controller.signal.aborted) dispatch({ type: 'result', value: result });
    } catch (error) {
      if (!controller.signal.aborted) dispatch({ type: 'error', value: error instanceof Error ? error.message : 'Unable to check policies. Please try again.' });
    } finally {
      if (pending.current === controller) pending.current = null;
    }
  }
  return {
    ...state, busy: state.status === 'loading' || state.status === 'streaming',
    references: (state.response?.sources ?? []).map((item) => ({ ...item, title: title(item.document_name) })),
    passages: (state.response?.retrieved_chunks ?? []).map((item) => ({ ...item, title: title(item.document_name) })),
    setQuestion: (value) => dispatch({ type: 'question', value }),
    setProvider: (value) => dispatch({ type: 'provider', value }), ask,
  };
}
