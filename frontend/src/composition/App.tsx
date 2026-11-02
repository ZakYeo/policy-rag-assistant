import { createPolicyApi } from '../models/policyApi';
import { usePolicyDesk } from '../viewmodels/usePolicyDesk';
import { PolicyDesk } from '../views/PolicyDesk';
import { createThemePreferences } from '../models/theme';
import { useTheme } from '../viewmodels/useTheme';

import { Header } from '../views/Header';
import { PolicyLibrary } from '../views/PolicyLibrary';
import { libraryClient } from '../models/libraryApi';
import { useLibrary } from '../viewmodels/useLibrary';
import { useNavigation } from '../viewmodels/useNavigation';

const client = createPolicyApi();
const preferences = createThemePreferences();
export function App() {
  const library = useLibrary(libraryClient);
  const vm = usePolicyDesk(client, undefined, library.policies.filter((policy) => policy.revision).map((policy) => policy.id));
  const theme = useTheme(preferences);
  const { page, navigate } = useNavigation();
  return <>
    <a href="#main" className="skip-link">Skip to content</a>
    <Header theme={theme} page={page} navigate={navigate} />
    {page === '/policies' ? <PolicyLibrary vm={library} /> : <PolicyDesk vm={vm} />}
    <footer className="mt-12 border-t border-line py-7 text-center text-sm text-muted">NorthStar Policy Desk · Internal Employee Guidance</footer>
  </>;
}
