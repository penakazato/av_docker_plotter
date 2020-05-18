#!/bin/bash
sqlite3 fin_app.db <<EOF
CREATE TABLE "daily_data" (
"date" TEXT,
  "open" TEXT,
  "high" TEXT,
  "low" TEXT,
  "close" TEXT,
  "volume" TEXT,
  "ticker" TEXT
);
EOF
