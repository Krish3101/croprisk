import { QueryClient } from '@tanstack/react-query';
import { QUERY_CONFIG } from '../config/query.config';

export const queryClient = new QueryClient(QUERY_CONFIG);

// Export stale times and query keys for use in hooks
export { STALE_TIME, QUERY_KEYS } from '../config/query.config';
