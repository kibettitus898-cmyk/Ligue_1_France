import { relations } from "drizzle-orm";
import { users, subscriptions, fixtures, predictions, odds, paymentTransactions } from "./schema";

export const usersRelations = relations(users, ({ many }) => ({
  subscriptions: many(subscriptions),
  paymentTransactions: many(paymentTransactions),
}));

export const subscriptionsRelations = relations(subscriptions, ({ one, many }) => ({
  user: one(users, {
    fields: [subscriptions.userId],
    references: [users.id],
  }),
  transactions: many(paymentTransactions),
}));

export const fixturesRelations = relations(fixtures, ({ many }) => ({
  predictions: many(predictions),
  odds: many(odds),
}));

export const predictionsRelations = relations(predictions, ({ one }) => ({
  fixture: one(fixtures, {
    fields: [predictions.fixtureId],
    references: [fixtures.id],
  }),
}));

export const oddsRelations = relations(odds, ({ one }) => ({
  fixture: one(fixtures, {
    fields: [odds.fixtureId],
    references: [fixtures.id],
  }),
}));

export const paymentTransactionsRelations = relations(paymentTransactions, ({ one }) => ({
  user: one(users, {
    fields: [paymentTransactions.userId],
    references: [users.id],
  }),
  subscription: one(subscriptions, {
    fields: [paymentTransactions.subscriptionId],
    references: [subscriptions.id],
  }),
}));
