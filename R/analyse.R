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
VARIETIES <- c("US", "GB", "IE", "AU", "ZA")
SECTIONS <- c("blog", "general")

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

# --- validation -------------------------------------------------------------
#
# 150 counts get typed in by hand from a rate-limited interface over several
# days, so every way that goes wrong is checked here. The omitted cell is the
# one to worry about. The composite is a sum of hits across frames, so a cell
# that never got entered lowers that variety's composite by however much the
# frame was worth, and the output carries no sign of it. Three missing ZA blog
# rows moved the ZA composite 16% in a fixture run.

fail <- function(...) stop(sprintf(...), call. = FALSE)

cells <- function(d) {
  paste0("  ", d$frame_id, " ", d$variety, "/", d$section, collapse = "\n")
}

if (any(is.na(sizes$words))) {
  fail("corpus sizes have blanks; a rate cannot be computed without them")
}

size_grid <- tidyr::expand_grid(variety = VARIETIES, section = SECTIONS)
size_gaps <- anti_join(size_grid, sizes, by = c("variety", "section"))
if (nrow(size_gaps) > 0) {
  fail("variety/section pairs with no corpus size (%d of %d):\n%s",
       nrow(size_gaps), nrow(size_grid),
       paste0("  ", size_gaps$variety, "/", size_gaps$section, collapse = "\n"))
}

# readr handles a pasted "1,234" on its own. This catches the other thing that
# ends up in a hit cell: a word - a note, a query caveat, a reminder to rerun.
if (!is.numeric(counts$hits)) {
  fail(paste("the hits column read as %s rather than a number, which means a",
             "word\nreached a hit cell. Notes belong in the notes column."),
       class(counts$hits)[1])
}

unusable <- counts %>% filter(is.na(hits) | hits < 0 | hits != floor(hits))
if (nrow(unusable) > 0) {
  fail("blank or non-integer hit counts (%d):\n%s",
       nrow(unusable),
       paste0("  ", unusable$frame_id, " ", unusable$variety, "/",
              unusable$section, " = ", unusable$hits, collapse = "\n"))
}

# A typo in a label gets dropped by the join rather than rejected, which lands
# in the same place as an omission.
unknown <- counts %>%
  filter(!frame_id %in% frames$frame_id | !variety %in% VARIETIES |
           !section %in% SECTIONS)
if (nrow(unknown) > 0) {
  fail("rows carrying an unrecognised frame, variety or section (%d):\n%s",
       nrow(unknown), cells(unknown))
}

repeated <- counts %>% count(frame_id, variety, section) %>% filter(n > 1)
if (nrow(repeated) > 0) {
  fail("cells entered more than once (%d):\n%s", nrow(repeated), cells(repeated))
}

expected <- tidyr::expand_grid(frame_id = frames$frame_id, variety = VARIETIES,
                               section = SECTIONS)
gaps <- anti_join(expected, counts, by = c("frame_id", "variety", "section"))
if (nrow(gaps) > 0) {
  fail(paste("cells with no count (%d of %d). The composite is a sum across",
             "frames, so\na partial grid understates whichever variety is",
             "short:\n%s"),
       nrow(gaps), nrow(expected), cells(gaps))
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
  rename(count_note = any_of("notes")) %>%
  inner_join(frames, by = "frame_id") %>%
  inner_join(select(sizes, -any_of("notes")), by = c("variety", "section")) %>%
  bind_cols(poisson_ci(.$hits, .$words)) %>%
  mutate(variety = factor(variety, levels = VARIETIES))

# --- the composite: the claim is about density, not any single frame --------
#
# No weighting. A weighted index would need a defensible reason for every
# weight, and there isn't one - so the index is a plain sum, and says so.
composite <- dat %>%
  group_by(variety, section) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  bind_cols(poisson_ci(.$hits, .$words))

# --- relative to US, which is the comparison the study is actually making ---
#
# A point ratio says nothing about whether a difference is real, and the
# variety comparison is the study's headline. These are exact conditional
# Poisson intervals on the rate ratio, so the comparison is held to the same
# standard as the rates rather than reported bare beside them.
rate_ratio <- function(hits, words, hits_ref, words_ref) {
  out <- vapply(seq_along(hits), function(i) {
    # Both counts zero leaves the ratio undefined; say so rather than
    # returning a number the interval cannot support.
    if (hits[i] + hits_ref[i] == 0) return(c(NA_real_, NA_real_, NA_real_))
    tt <- stats::poisson.test(c(hits[i], hits_ref[i]),
                              T = c(words[i], words_ref[i]))
    c(unname(tt$estimate), tt$conf.int[1], tt$conf.int[2])
  }, numeric(3))
  tibble(ratio = out[1, ], ratio_lower = out[2, ], ratio_upper = out[3, ])
}

reference <- dat %>%
  filter(variety == "US") %>%
  select(frame_id, section, hits_us = hits, words_us = words, rate_us = rate)

ratios <- dat %>%
  filter(variety != "US") %>%
  select(frame_id, gloss, family, variety, section, hits, words, rate) %>%
  inner_join(reference, by = c("frame_id", "section")) %>%
  bind_cols(rate_ratio(.$hits, .$words, .$hits_us, .$words_us)) %>%
  arrange(frame_id, section, variety)

# --- the composite, tested rather than asserted ------------------------------
#
# The composite claim is that a variety reaches for these frames more overall.
# The sum above answers it descriptively, and comparing those sums across
# varieties on a Poisson interval would be overconfident: fifteen frames whose
# base rates differ by two orders of magnitude are overdispersed by
# construction, and the frames a variety happens to favour vary too. Frame
# enters as a factor to absorb the first, and the quasi-Poisson dispersion
# carries what is left into the variety intervals.
fit <- stats::glm(hits ~ frame_id + variety + section,
                  family = stats::quasipoisson(), offset = log(words),
                  data = dat)

dispersion <- summary(fit)$dispersion

coefs <- summary(fit)$coefficients
variety_rows <- grep("^variety", rownames(coefs))
z <- stats::qnorm(0.975)
composite_ratios <- tibble(
  variety = sub("^variety", "", rownames(coefs)[variety_rows]),
  ratio = exp(coefs[variety_rows, "Estimate"]),
  ratio_lower = exp(coefs[variety_rows, "Estimate"] - z * coefs[variety_rows, "Std. Error"]),
  ratio_upper = exp(coefs[variety_rows, "Estimate"] + z * coefs[variety_rows, "Std. Error"]),
  p_value = coefs[variety_rows, "Pr(>|t|)"],
  dispersion = dispersion,
  reference = "US"
)

# The genre control the design leans on: if the variety effect differs between
# the blog and general sections, the common effect above hides it and the
# per-section ratios are what to report. F rather than chi-squared, because
# the dispersion is estimated.
fit_interaction <- stats::update(fit, . ~ . + variety:section)
genre_test <- stats::anova(fit, fit_interaction, test = "F")

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
write_csv(composite_ratios, "data/composite-ratios.csv")

message(sprintf("%d cells: %d frames x %d varieties x %d sections",
                nrow(dat), n_distinct(dat$frame_id), n_distinct(dat$variety),
                n_distinct(dat$section)))
message("wrote figures/frame-rates.png, data/rates.csv, data/composite.csv,\n  data/ratios-vs-us.csv, data/composite-ratios.csv")

message(sprintf("\nquasi-Poisson dispersion %.1f. A value near 1 would have meant the\nplain Poisson interval was adequate after all.", dispersion))
print(composite_ratios)

message(sprintf(
  "\nvariety x section interaction: F = %.2f on %d and %d df, p = %.3f.\n%s",
  genre_test$F[2], genre_test$Df[2], genre_test$`Resid. Df`[2],
  genre_test$`Pr(>F)`[2],
  if (isTRUE(genre_test$`Pr(>F)`[2] < 0.05)) {
    "The variety effect differs by section, so report the per-section ratios\nin data/ratios-vs-us.csv rather than the common effect above."
  } else {
    "No evidence the variety effect differs between blog and general."
  }
))
