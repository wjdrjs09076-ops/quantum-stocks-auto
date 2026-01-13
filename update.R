pkgs <- c("tidyverse","lubridate","tidyquant","writexl","readr")
new_pkgs <- pkgs[!(pkgs %in% installed.packages()[, "Package"])]
if(length(new_pkgs)>0) install.packages(new_pkgs)

library(tidyverse); library(lubridate); library(tidyquant); library(writexl); library(readr)

tickers <- tibble::tribble(
  ~name, ~symbol,
  "QSI (Quantum-Si)", "QSI",
  "QBTS (D-Wave)",    "QBTS",
  "IONQ (IonQ)",      "IONQ",
  "RGTI (Rigetti)",   "RGTI",
  "QTUM (Quantum ETF)","QTUM"
)

end_date   <- Sys.Date()
start_date <- end_date - 365

prices_raw <- tq_get(tickers$symbol, from=start_date, to=end_date, get="stock.prices")
stopifnot(!is.null(prices_raw), nrow(prices_raw) > 0)

prices <- prices_raw %>%
  select(symbol, date, open, high, low, close, volume) %>%
  left_join(tickers, by="symbol") %>%
  arrange(date, name)

close_pivot <- prices %>%
  select(date, name, close) %>%
  pivot_wider(names_from=name, values_from=close) %>%
  arrange(date)

index_pivot <- prices %>%
  group_by(name) %>% arrange(date) %>%
  mutate(index_100 = close/first(close)*100) %>%
  ungroup() %>%
  select(date, name, index_100) %>%
  pivot_wider(names_from=name, values_from=index_100) %>%
  arrange(date)

dir.create("public", showWarnings = FALSE)

write_xlsx(
  list(close_pivot=close_pivot, index_pivot=index_pivot, prices_long=prices),
  path = "public/quantum_latest.xlsx"
)
