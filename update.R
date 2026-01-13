pkgs <- c("tidyverse","lubridate","tidyquant","writexl","readr")
new_pkgs <- pkgs[!(pkgs %in% installed.packages()[, "Package"])]
if(length(new_pkgs)>0) install.packages(new_pkgs)

library(tidyverse)
library(lubridate)
library(tidyquant)
library(writexl)
library(readr)

# ---- Tickers ----
tickers <- tibble::tribble(
  ~name,                 ~symbol,
  "QSI (Quantum-Si)",    "QSI",
  "QBTS (D-Wave)",       "QBTS",
  "IONQ (IonQ)",         "IONQ",
  "RGTI (Rigetti)",      "RGTI",
  "QTUM (Quantum ETF)",  "QTUM"
)

# ---- Period: last 1 year ----
end_date   <- Sys.Date()
start_date <- end_date - 365

# ---- Get prices ----
prices_raw <- tq_get(
  x    = tickers$symbol,
  from = start_date,
  to   = end_date,
  get  = "stock.prices"
)

# ---- Fail-safe: keep previous files if Yahoo fails ----
if (is.null(prices_raw) || nrow(prices_raw) == 0) {
  message("⚠️ No data returned from Yahoo. Skipping update.")
  quit(save = "no", status = 0)
}

# ---- Clean data ----
prices <- prices_raw %>%
  select(symbol, date, open, high, low, close, volume) %>%
  left_join(tickers, by = "symbol") %>%
  arrange(date, name)

# ---- Pivot: close prices ----
close_pivot <- prices %>%
  select(date, name, close) %>%
  pivot_wider(names_from = name, values_from = close) %>%
  arrange(date)

# ---- Pivot: index (first day = 100) ----
index_pivot <- prices %>%
  group_by(name) %>%
  arrange(date) %>%
  mutate(index_100 = close / first(close) * 100) %>%
  ungroup() %>%
  select(date, name, index_100) %>%
  pivot_wider(names_from = name, values_from = index_100) %>%
  arrange(date)

# ---- Output folder for GitHub Pages ----
dir.create("docs", showWarnings = FALSE)

# ---- Write Excel ----
write_xlsx(
  list(
    close_pivot = close_pivot,
    index_pivot = index_pivot,
    prices_long = prices
  ),
  path = "docs/quantum_latest.xlsx"
)

# ---- Write CSV ----
write_csv(close_pivot, "docs/quantum_close_pivot.csv")

# ---- Last updated timestamp ----
writeLines(
  paste0("Last updated (UTC): ", format(Sys.time(), tz = "UTC")),
  "docs/last_updated.txt"
)

message("✅ Update completed successfully")
