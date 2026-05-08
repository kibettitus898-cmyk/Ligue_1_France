import { trpc } from "@/lib/trpc";

export function useSubscription() {
  const mySubscription = trpc.payments.mySubscription.useQuery(undefined, {
    staleTime: 1000 * 60 * 2,
  });

  const createSubscription = trpc.payments.createSubscription.useMutation({
    onSuccess: () => {
      mySubscription.refetch();
    },
  });

  return {
    subscription: mySubscription.data,
    isLoading: mySubscription.isLoading,
    createSubscription,
  };
}
