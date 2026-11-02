import { useEffect, useReducer, useRef } from 'react';
import type { LibraryClient, PolicyOperation } from '../contracts/library';

type TrackingState =
  | { phase: 'idle'; operation: null; connectionError: null }
  | { phase: 'polling' | 'reconnecting' | 'finished'; operation: PolicyOperation; connectionError: string | null };
type Action = { type: 'track' | 'received'; operation: PolicyOperation } | { type: 'disconnected'; error: string } | { type: 'finished' };
function reducer(state: TrackingState, action: Action): TrackingState {
  if (action.type === 'track' || action.type === 'received') return { phase: 'polling', operation: action.operation, connectionError: null };
  if (!state.operation) return state;
  if (action.type === 'disconnected') return { ...state, phase: 'reconnecting', connectionError: action.error };
  return { ...state, phase: 'finished', connectionError: null };
}

export function usePolicyOperation(client: LibraryClient, onComplete: (operation: PolicyOperation) => Promise<void>) {
  const [state, dispatch] = useReducer(reducer, { phase: 'idle', operation: null, connectionError: null });
  const complete = useRef(onComplete);
  const trackedId = useRef<string | null>(null);
  useEffect(() => { complete.current = onComplete; }, [onComplete]);
  useEffect(() => {
    if (state.phase === 'idle' || state.phase === 'finished') return;
    let active = true;
    const operation = state.operation;
    if (operation.status === 'succeeded' || operation.status === 'failed') {
      void complete.current(operation).finally(() => { if (active) dispatch({ type: 'finished' }); });
      return () => { active = false; };
    }
    const timer = setTimeout(() => {
      void client.operation(operation.id).then((next) => {
        if (active) dispatch({ type: 'received', operation: next });
      }).catch((reason: unknown) => {
        if (active) dispatch({ type: 'disconnected', error: reason instanceof Error ? reason.message : 'Connection lost. Retrying processing status…' });
      });
    }, state.phase === 'reconnecting' ? 2000 : 700);
    return () => { active = false; clearTimeout(timer); };
  }, [client, state]);
  function track(operation: PolicyOperation) {
    trackedId.current = operation.id;
    dispatch({ type: 'track', operation });
  }
  return { track, trackedId, operation: state.operation, pending: state.phase === 'polling' || state.phase === 'reconnecting', connectionError: state.connectionError };
}
