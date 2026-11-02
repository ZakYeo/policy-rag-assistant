import { useSyncExternalStore } from 'react';
import { navigation } from '../models/navigation';
export function useNavigation() {
  const page = useSyncExternalStore(navigation.subscribe, navigation.snapshot);
  return { page, navigate: navigation.go };
}
