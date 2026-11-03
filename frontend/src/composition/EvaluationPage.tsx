import { evaluationClient } from '../models/evaluationApi';
import { useEvaluation } from '../viewmodels/useEvaluation';
import { Evaluation } from '../views/Evaluation';

export function EvaluationPage() {
  return <Evaluation vm={useEvaluation(evaluationClient)} />;
}
