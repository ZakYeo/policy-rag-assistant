import type { DeskViewModel } from '../contracts/policy';
import type { ThemeViewModel } from '../contracts/theme';
import { Header } from './Header';
import { QuestionForm } from './QuestionForm';
import { Results } from './Results';

export function PolicyDesk({ vm, theme }: { vm: DeskViewModel; theme: ThemeViewModel }) {
  return <>
    <a href="#main" className="skip-link">Skip to content</a>
    <Header theme={theme} />
    <main id="main" className="page-width flex-1 py-10 min-[640px]:py-12">
      <div className="mb-9">
        <h1 className="text-[1.8rem] leading-tight font-bold tracking-tight">Ask about NorthStar policies</h1>
        <p className="mt-2 text-lg leading-relaxed text-muted">Search workplace standards across information security, acceptable AI use, confidentiality, and data handling.</p>
      </div>
      <QuestionForm vm={vm} />
      {vm.error && <p role="alert" className="mb-6 rounded border border-error bg-error-surface p-4 text-error">{vm.error}</p>}
      <Results vm={vm} />
    </main>
    <footer className="mt-12 border-t border-line py-7 text-center text-sm text-muted">NorthStar Policy Desk · Internal Employee Guidance</footer>
  </>;
}
