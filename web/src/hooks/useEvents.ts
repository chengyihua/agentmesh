import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useEvents() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Determine the correct API base URL for SSE
    // Use the same default as useRegistry: http://localhost:8000/api/v1
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    const eventSource = new EventSource(`${apiBase}/events`);

    eventSource.onopen = () => {
      console.log('SSE connected');
    };

    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      eventSource.close();
    };

    // Debounce invalidation to prevent thrashing
    let timeoutId: NodeJS.Timeout;
    const debouncedInvalidate = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['agents'] });
        queryClient.invalidateQueries({ queryKey: ['leaderboard'] });
        queryClient.invalidateQueries({ queryKey: ['stats'] });
      }, 1000); // 1 second debounce
    };

    const handleUpdate = (event: MessageEvent) => {
      // console.log('Received event:', event.type);
      debouncedInvalidate();
    };

    eventSource.addEventListener('agent_registered', handleUpdate);
    eventSource.addEventListener('agent_updated', handleUpdate);
    eventSource.addEventListener('agent_health_changed', handleUpdate);
    eventSource.addEventListener('trust_score_changed', handleUpdate);

    return () => {
      eventSource.close();
    };
  }, [queryClient]);
}
