#!/usr/bin/env Rscript

# Does Study 4's estimator (R/ratio.R) cover a known ratio 95% of the time?
#
# Every population here is data Studies 2 and 3 already counted: Study 2's
# per-text counts and Study 3's per-file counts for common_crawl. None of
# Study 4's data is used. Each scenario resamples units from a population, as
# a study would draw them, and sets a known true ratio by thinning one arm's
# hits binomially, so the rate in that arm is exactly p times its population's.
#
# The scenarios follow Study 4's contrasts:
#   texts         4,000 generated texts against 4,000, at the populations'
#                 own rates and at a fifth of them, as a stage-1 checkpoint
#                 might write
#   texts-files   4,000 texts against 200 stage-1 files, as the stage-1
#                 checkpoint is set against its input
#   files         40 drawn files against 40, as a small midtraining source or
#                 category is compared in the secondary analysis
#   pooled        960 files against 200, as the midtraining sample, drawn in
#                 proportion to its sources' token shares, is set against the
#                 stage-1 input
#   paired        4,000 pairs of responses to the same prompt, as chosen and
#                 rejected responses are compared
# The estimator serves Study 4's contrastive-family outcome (F06 to F09),
# which is checked first. A fifteen-frame summed rate is checked as a harder
# case, with the commonest frames dominating the counts; Study 4's composite
# outcome itself uses R/model.R, whose t intervals Study 1's calibration
# checked.
#
# Usage:
#   Rscript R/calibrate-ratio.R

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

source("R/ratio.R")

REPS <- 2000
set.seed(20260929)

FAMILY <- c("F06", "F07", "F08", "F09")
COMPOSITE <- sprintf("F%02d", 1:15)

texts <- read_csv("data/counts-generated-by-text.csv", show_col_types = FALSE)
files_raw <- jsonlite::fromJSON("data/dolma/common_crawl.json")$per_file
files <- tibble(words = files_raw$words) %>% bind_cols(as_tibble(files_raw$hits))

population <- function(d, outcome) {
  cols <- if (outcome == "family") FAMILY else COMPOSITE
  list(h = rowSums(as.matrix(d[, cols])), w = d$words)
}

draw <- function(pop, n, p = 1) {
  i <- sample.int(length(pop$h), n, replace = TRUE)
  h <- pop$h[i]
  if (p < 1) h <- stats::rbinom(n, h, p)
  list(h = h, w = pop$w[i])
}

pop_rate <- function(pop) sum(pop$h) / sum(pop$w)

# One scenario: `one_rep` returns the interval, `truth` the ratio it targets.
coverage <- function(label, outcome, truth, one_rep) {
  hits <- 0L
  widths <- numeric(REPS)
  for (r in seq_len(REPS)) {
    ci <- one_rep()
    hits <- hits + (ci$lower <= truth && truth <= ci$upper)
    widths[r] <- log(ci$upper / ci$lower)
  }
  tibble(scenario = label, outcome = outcome, true_ratio = round(truth, 3),
         coverage = hits / REPS,
         mc_se = sqrt(hits / REPS * (1 - hits / REPS) / REPS),
         median_width_log = round(stats::median(widths), 3))
}

results <- list()
for (outcome in c("family", "composite")) {
  base <- population(filter(texts, source == "base-1.0"), outcome)
  instruct <- population(filter(texts, source == "instruct-1.0"), outcome)
  crawl <- population(files, outcome)

  for (pop_name in c("base-1.0", "instruct-1.0")) {
    pop <- if (pop_name == "base-1.0") base else instruct
    for (scale in c(1, 0.2)) {
      for (p in c(1, 0.5)) {
        label <- sprintf("texts: %s at %s of its rate", pop_name,
                         if (scale == 1) "all" else "a fifth")
        results[[length(results) + 1]] <- coverage(
          label, outcome, p, function() {
            a <- draw(pop, 4000, scale * p)
            b <- draw(pop, 4000, scale)
            compare_rates(ratio_rate(a$h, a$w), ratio_rate(b$h, b$w))
          })
      }
    }
  }

  results[[length(results) + 1]] <- coverage(
    "texts-files: base-1.0 against 200 common_crawl files", outcome,
    pop_rate(base) / pop_rate(crawl), function() {
      a <- draw(base, 4000)
      b <- draw(crawl, 200)
      compare_rates(ratio_rate(a$h, a$w), ratio_rate(b$h, b$w))
    })

  for (p in c(1, 0.5)) {
    results[[length(results) + 1]] <- coverage(
      "files: 40 common_crawl files against 40", outcome, p, function() {
        a <- draw(crawl, 40, p)
        b <- draw(crawl, 40)
        compare_rates(ratio_rate(a$h, a$w), ratio_rate(b$h, b$w))
      })
  }

  for (p in c(1, 0.5)) {
    results[[length(results) + 1]] <- coverage(
      "pooled: 960 common_crawl files against 200", outcome, p, function() {
        a <- draw(crawl, 960, p)
        b <- draw(crawl, 200)
        compare_rates(ratio_rate(a$h, a$w), ratio_rate(b$h, b$w))
      })
  }

  # Pairs: base-1.0 and base-0.7 texts on the same topic stand in for chosen
  # and rejected responses to the same prompt.
  pairs <- inner_join(
    filter(texts, source == "base-1.0"), filter(texts, source == "base-0.7"),
    by = "topic_id", suffix = c("_1", "_2"))
  cols <- if (outcome == "family") FAMILY else COMPOSITE
  h1 <- rowSums(as.matrix(pairs[, paste0(cols, "_1")]))
  h2 <- rowSums(as.matrix(pairs[, paste0(cols, "_2")]))
  w1 <- pairs$words_1
  w2 <- pairs$words_2
  for (p in c(1, 0.5)) {
    results[[length(results) + 1]] <- coverage(
      "paired: 4,000 pairs of texts on the same topic", outcome,
      p * (sum(h1) / sum(w1)) / (sum(h2) / sum(w2)), function() {
        i <- sample.int(length(h1), length(h1), replace = TRUE)
        a <- if (p < 1) stats::rbinom(length(i), h1[i], p) else h1[i]
        compare_paired(a, w1[i], h2[i], w2[i])
      })
  }
}

out <- bind_rows(results)
message(sprintf("%d reps per scenario; nominal coverage 95%%", REPS))
print(out %>% mutate(coverage = sprintf("%.1f%%", 100 * coverage),
                     mc_se = sprintf("%.1f", 100 * mc_se)),
      n = Inf, width = Inf)
message(sprintf("lowest coverage %.1f%%, highest %.1f%%",
                100 * min(out$coverage), 100 * max(out$coverage)))
