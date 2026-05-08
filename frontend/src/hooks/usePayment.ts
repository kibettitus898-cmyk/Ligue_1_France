import { useCallback } from "react";
import { trpc } from "@/lib/trpc";

export function usePayment() {
  const utils = trpc.useUtils();

  const mockStkPush = trpc.payments.mockStkPush.useMutation();

  const getSubscription = trpc.payments.getSubscription.useQuery(
    { user_id: "mock" },
    { enabled: false }
  );

  const myTransactions = trpc.payments.myTransactions.useQuery(undefined, {
    staleTime: 1000 * 60,
  });

  const createTransaction = trpc.payments.createTransaction.useMutation({
    onSuccess: () => {
      utils.payments.myTransactions.invalidate();
    },
  });

  const pay = useCallback(
    async (plan: "daily" | "weekly" | "monthly", userId: string, phone?: string) => {
      return mockStkPush.mutateAsync({ user_id: userId, plan, phone });
    },
    [mockStkPush]
  );

  return {
    pay,
    isPaying: mockStkPush.isPending,
    payError: mockStkPush.error,
    getSubscription,
    myTransactions,
    createTransaction,
  };
}
