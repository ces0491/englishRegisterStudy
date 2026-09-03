#!/usr/bin/env Rscript

# Rates per million words for a fixed set of rhetorical frames, by national
# variety of English.
#
# The frames are frozen in `data/frames.csv` before any querying, because the
# temptation in a study like this is to notice which frames separate and then
# decide those were the ones you meant. Adding a frame after seeing results is
# a different study and should say so.
#
# Counts are hand-entered from the GloWbE web interface, which has no API. Raw
# hits and corpus sizes are both recorded rather than the interface's own
# per-million figure, so the normalisation can be checked and recomputed.
#
# Usage:
#   Rscript R/analyse.R                       # data/counts.csv
#   Rscript R/analyse.R path/to/counts.csv    # anything else, for testing

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)
COUNTS <- if (length(args) >= 1) args[1] else "data/counts.csv"
SIZES <- if (length(args) >= 2) args[2] else "data/corpus-sizes.csv"
FRAMES <- "data/frames.csv"

for (f in c(FRAMES, COUNTS, SIZES)) {
  if (!file.exists(f)) {
    stop(sprintf(
      "%s is missing. Copy the template beside it and fill it in from GloWbE;\nnothing here estimates a count.", f
    ), call. = FALSE)
  }
}

frames <- read_csv(FRAMES, show_col_types = FALSE)
counts <- read_csv(COUNTS, show_col_types = FALSE)
sizes <- read_csv(SIZES, show_col_types = FALSE)

if (any(is.na(sizes$words))) {
  stop("corpus sizes have blanks; a rate cannot be computed without them", call. = FALSE)
}

# --- rates, with an interval that reflects how few hits some frames get ------
#
# A frame appearing 4 times in 180 million words and one appearing 4,000 times
# are not equally well measured, and a bare per-million figure hides that. The
# exact Poisson interval on the count carries it through to the rate.
poisson_ci <- function(hits, words, per = 1e6) {
  out <- vapply(seq_along(hits), function(i) {
    ci <- stats::poisson.test(hits[i])$conf.int
    c(lower = ci[1], upper = ci[2])
  }, numeric(2))
  tibble(
    rate  = hits / words * per,
    lower = out["lower", ] / words * per,
    upper = out["upper", ] / words * per
  )
}

dat <- counts %>%
  inner_join(frames, by = "frame_id") %>%
  inner_join(sizes, by = c("variety", "section")) %>%
  bind_cols(poisson_ci(.$hits, .$words)) %>%
  mutate(variety = factor(variety, levels = c("US", "GB", "IE", "AU", "ZA")))

# --- the composite: the claim is about density, not any single frame --------
#
# No weighting. A weighted index would need a defensible reason for every
# weight, and there isn't one - so the index is a plain sum, and says so.
composite <- dat %>%
  group_by(variety, section) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  bind_cols(poisson_ci(.$hits, .$words))

# --- relative to US, which is the comparison the study is actually making ---
ratios <- dat %>%
  select(frame_id, gloss, family, variety, section, rate) %>%
  tidyr::pivot_wider(names_from = variety, values_from = rate) %>%
  mutate(across(c(GB, IE, AU, ZA), ~ .x / US, .names = "{.col}_vs_US"))

dir.create("figures", showWarnings = FALSE)

p <- ggplot(dat, aes(x = rate, y = reorder(gloss, rate), colour = variety)) +
  geom_errorbar(aes(xmin = lower, xmax = upper), orientation = "y", width = 0, alpha = 0.5) +
  geom_point(size = 2) +
  facet_wrap(~section) +
  labs(
    title = "Rhetorical frames per million words, by variety of English",
    subtitle = "GloWbE. Bars are exact Poisson intervals on the underlying count.",
    x = "Occurrences per million words", y = NULL, colour = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank())

ggsave("figures/frame-rates.png", p, width = 10, height = 7, dpi = 150)

write_csv(dat, "data/rates.csv")
write_csv(composite, "data/composite.csv")
write_csv(ratios, "data/ratios-vs-us.csv")

message(sprintf("%d frames x %d varieties x %d sections",
                n_distinct(dat$frame_id), n_distinct(dat$variety), n_distinct(dat$section)))
message("wrote figures/frame-rates.png, data/rates.csv, data/composite.csv, data/ratios-vs-us.csv")
print(composite)
