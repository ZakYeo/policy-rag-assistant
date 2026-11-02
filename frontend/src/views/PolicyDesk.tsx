import type { DeskViewModel } from '../contracts/policy';
import { PageIntro } from './PageIntro';
import { QuestionForm } from './QuestionForm';
import { Results } from './Results';
import { SampleQuestions } from './SampleQuestions';

export function PolicyDesk({ vm }: { vm: DeskViewModel }) {
  return <>
    <main id="main" className="page-width flex-1 py-10 min-[640px]:py-12">
      <PageIntro title="Ask about NorthStar policies" description="Search workplace standards across information security, acceptable AI use, confidentiality, and data handling." />
      <QuestionForm vm={vm} />
      <SampleQuestions groups={vm.sampleQuestionGroups} onSelect={vm.selectSampleQuestion} />
      {vm.error && <p role="alert" className="mb-6 rounded border border-error bg-error-surface p-4 text-error">{vm.error}</p>}
      <p role="status" className="sr-only">{vm.status === 'loading' ? 'Searching NorthStar policies.' : vm.status === 'streaming' ? 'Receiving the answer.' : vm.status === 'success' ? 'Answer and policy references are ready.' : ''}</p>
      <Results vm={vm} />
    </main>
  </>;
}
