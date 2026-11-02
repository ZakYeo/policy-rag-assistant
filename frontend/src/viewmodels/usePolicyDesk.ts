import { useEffect, useReducer, useRef } from 'react';
import type { AnswerProvider, AskResponse, DeskState, DeskViewModel, PolicyClient } from '../contracts/policy';
import { sampleQuestionGroups } from '../models/sampleQuestions';
import { focusQuestionEditor } from '../models/questionEditor';

type Action = { type: 'question'; value: string } | { type: 'provider'; value: AnswerProvider }
  | { type: 'begin'; question: string } | { type: 'result'; value: AskResponse }
  | { type: 'delta'; text: string }
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
    case 'delta': return { ...state, status: 'streaming', answer: state.answer + action.text };
    case 'error': return { ...state, status: 'error', error: action.value };
  }
}

export function usePolicyDesk(client: PolicyClient, focusEditor = focusQuestionEditor): DeskViewModel {
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
      if (state.provider === 'openai') {
        let completed = false;
        for await (const event of client.stream(question, controller.signal)) {
          if (controller.signal.aborted) return;
          if (event.type === 'delta') dispatch({ type: 'delta', text: event.text });
          else { dispatch({ type: 'result', value: event.response }); completed = true; break; }
        }
        if (!completed && !controller.signal.aborted) throw new Error('The answer stream was interrupted. Please try again.');
      } else {
        const result = await client.ask(question, state.provider, controller.signal);
        if (!controller.signal.aborted) dispatch({ type: 'result', value: result });
      }
    } catch (error) {
      if (!controller.signal.aborted) dispatch({ type: 'error', value: error instanceof Error ? error.message : 'Unable to check policies. Please try again.' });
    } finally {
      if (pending.current === controller) pending.current = null;
    }
  }
  return {
    sampleQuestionGroups,
    selectSampleQuestion(id) {
      const sample = sampleQuestionGroups.flatMap((group) => group.questions).find((question) => question.id === id);
      if (!sample) return;
      dispatch({ type: 'question', value: sample.question });
      focusEditor();
    },
    ...state, busy: state.status === 'loading' || state.status === 'streaming',
    references: (state.response?.sources ?? []).map((item) => ({ ...item, title: title(item.document_name) })),
    passages: (state.response?.retrieved_chunks ?? []).map((item) => ({ ...item, title: title(item.document_name) })),
    setQuestion: (value) => dispatch({ type: 'question', value }),
    setProvider: (value) => dispatch({ type: 'provider', value }), ask,
  };
}
