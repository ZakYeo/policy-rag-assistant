import { createPolicyApi } from '../models/policyApi';
import { usePolicyDesk } from '../viewmodels/usePolicyDesk';
import { PolicyDesk } from '../views/PolicyDesk';

const client = createPolicyApi();
export function App() {
  const vm = usePolicyDesk(client);
  return <PolicyDesk vm={vm} />;
}
