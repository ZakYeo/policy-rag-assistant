import { createPolicyApi } from '../models/policyApi';
import { usePolicyDesk } from '../viewmodels/usePolicyDesk';
import { PolicyDesk } from '../views/PolicyDesk';
import { createThemePreferences } from '../models/theme';
import { useTheme } from '../viewmodels/useTheme';

const client = createPolicyApi();
const preferences = createThemePreferences();
export function App() {
  const vm = usePolicyDesk(client);
  const theme = useTheme(preferences);
  return <PolicyDesk vm={vm} theme={theme} />;
}
