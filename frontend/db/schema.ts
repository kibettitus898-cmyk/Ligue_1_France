import {
  mysqlTable,
  mysqlEnum,
  serial,
  varchar,
  text,
  timestamp,
  bigint,
  decimal,
  int,
  json,
} from "drizzle-orm/mysql-core";

export const users = mysqlTable("users", {
  id: serial("id").primaryKey(),
  unionId: varchar("unionId", { length: 255 }).notNull().unique(),
  name: varchar("name", { length: 255 }),
  email: varchar("email", { length: 320 }),
  avatar: text("avatar"),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  phone: varchar("phone", { length: 20 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt")
    .defaultNow()
    .notNull()
    .$onUpdate(() => new Date()),
  lastSignInAt: timestamp("lastSignInAt").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

export const subscriptions = mysqlTable("subscriptions", {
  id: serial("id").primaryKey(),
  userId: bigint("userId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  plan: mysqlEnum("plan", ["daily", "weekly", "monthly", "free"])
    .default("free")
    .notNull(),
  status: mysqlEnum("status", ["active", "expired", "cancelled", "pending"])
    .default("pending")
    .notNull(),
  startDate: timestamp("startDate").defaultNow().notNull(),
  endDate: timestamp("endDate"),
  amount: decimal("amount", { precision: 10, scale: 2 }),
  currency: varchar("currency", { length: 10 }).default("KES"),
  paymentMethod: varchar("paymentMethod", { length: 50 }).default("mpesa"),
  transactionId: varchar("transactionId", { length: 255 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().notNull(),
});

export type Subscription = typeof subscriptions.$inferSelect;
export type InsertSubscription = typeof subscriptions.$inferInsert;

export const fixtures = mysqlTable("fixtures", {
  id: serial("id").primaryKey(),
  fixtureId: varchar("fixtureId", { length: 100 }).notNull().unique(),
  homeTeam: varchar("homeTeam", { length: 255 }).notNull(),
  awayTeam: varchar("awayTeam", { length: 255 }).notNull(),
  homeTeamLogo: text("homeTeamLogo"),
  awayTeamLogo: text("awayTeamLogo"),
  matchDate: timestamp("matchDate").notNull(),
  venue: varchar("venue", { length: 255 }),
  season: varchar("season", { length: 50 }),
  league: varchar("league", { length: 100 }).default("Ligue 1"),
  status: mysqlEnum("status", ["scheduled", "live", "finished", "postponed"])
    .default("scheduled")
    .notNull(),
  homeScore: int("homeScore"),
  awayScore: int("awayScore"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().notNull(),
});

export type Fixture = typeof fixtures.$inferSelect;
export type InsertFixture = typeof fixtures.$inferInsert;

export const predictions = mysqlTable("predictions", {
  id: serial("id").primaryKey(),
  fixtureId: bigint("fixtureId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => fixtures.id, { onDelete: "cascade" }),
  homeWinProb: decimal("homeWinProb", { precision: 5, scale: 2 }),
  drawProb: decimal("drawProb", { precision: 5, scale: 2 }),
  awayWinProb: decimal("awayWinProb", { precision: 5, scale: 2 }),
  expectedGoalsHome: decimal("expectedGoalsHome", { precision: 4, scale: 2 }),
  expectedGoalsAway: decimal("expectedGoalsAway", { precision: 4, scale: 2 }),
  confidenceScore: decimal("confidenceScore", { precision: 5, scale: 2 }),
  recommendedBet: varchar("recommendedBet", { length: 50 }),
  evValue: decimal("evValue", { precision: 6, scale: 3 }),
  kellyFraction: decimal("kellyFraction", { precision: 5, scale: 2 }),
  modelVersion: varchar("modelVersion", { length: 50 }),
  featuresUsed: json("featuresUsed"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().notNull(),
});

export type Prediction = typeof predictions.$inferSelect;
export type InsertPrediction = typeof predictions.$inferInsert;

export const odds = mysqlTable("odds", {
  id: serial("id").primaryKey(),
  fixtureId: bigint("fixtureId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => fixtures.id, { onDelete: "cascade" }),
  bookmaker: varchar("bookmaker", { length: 100 }).notNull(),
  homeOdds: decimal("homeOdds", { precision: 6, scale: 2 }),
  drawOdds: decimal("drawOdds", { precision: 6, scale: 2 }),
  awayOdds: decimal("awayOdds", { precision: 6, scale: 2 }),
  over25Odds: decimal("over25Odds", { precision: 6, scale: 2 }),
  under25Odds: decimal("under25Odds", { precision: 6, scale: 2 }),
  bttsYesOdds: decimal("bttsYesOdds", { precision: 6, scale: 2 }),
  bttsNoOdds: decimal("bttsNoOdds", { precision: 6, scale: 2 }),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().notNull(),
});

export type Odds = typeof odds.$inferSelect;
export type InsertOdds = typeof odds.$inferInsert;

export const paymentTransactions = mysqlTable("payment_transactions", {
  id: serial("id").primaryKey(),
  userId: bigint("userId", { mode: "number", unsigned: true })
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  subscriptionId: bigint("subscriptionId", { mode: "number", unsigned: true })
    .references(() => subscriptions.id, { onDelete: "set null" }),
  amount: decimal("amount", { precision: 10, scale: 2 }).notNull(),
  currency: varchar("currency", { length: 10 }).default("KES"),
  plan: mysqlEnum("plan", ["daily", "weekly", "monthly"]).notNull(),
  status: mysqlEnum("status", ["pending", "success", "failed", "cancelled"])
    .default("pending")
    .notNull(),
  mpesaReceiptNumber: varchar("mpesaReceiptNumber", { length: 255 }),
  phoneNumber: varchar("phoneNumber", { length: 20 }),
  merchantRequestId: varchar("merchantRequestId", { length: 255 }),
  checkoutRequestId: varchar("checkoutRequestId", { length: 255 }),
  resultCode: int("resultCode"),
  resultDesc: text("resultDesc"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().notNull(),
});

export type PaymentTransaction = typeof paymentTransactions.$inferSelect;
export type InsertPaymentTransaction = typeof paymentTransactions.$inferInsert;
