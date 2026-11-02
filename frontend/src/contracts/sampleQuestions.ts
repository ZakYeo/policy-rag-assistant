export interface SampleQuestion {
  readonly id: string;
  readonly question: string;
  readonly policyIds: readonly string[];
}

export interface SampleQuestionGroup {
  readonly title: string;
  readonly questions: readonly SampleQuestion[];
}
