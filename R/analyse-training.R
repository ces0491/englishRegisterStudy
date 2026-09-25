#!/usr/bin/env Rscript

# Study 3: does the model use these frames more often than the corpus it was
# trained on, or at the same rate?
#
# Registered at https://osf.io/ngt3m. The sampling frame is in
# docs/dolma-sampling-frame.md and the counting layer in docs/frame-mapping.md.
#
# A model producing American register proves nothing on its own. If the
# training data was full of these frames, a model reproducing them is a model
# working correctly. Equality is a result, and a duller one.
#
# Inputs:
#   data/counts-dolma.csv      written by python/count_generated.py --dolma
#   data/counts-generated.csv  written by python/count_generated.py
#
# Usage:
#   python python/count_generated.py --dolma data/dolma
#   Rscript R/analyse-training.R

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

# Run from the repository root, as R/analyse.R is.
source("R/model.R")

CONFIRMATORY <- "base-1.0"
PRIMARY_INPUT <- "common_crawl"

# The published token shares of the stage-1 mix, used only for the secondary
# whole-mix figure.
TOKEN_SHARES <- c(
  common_crawl = 0.7607, olmocr_science_pdfs = 0.1357, stack_edu = 0.0689,
  `finemath-3plus` = 0.0256, `rpj-proofpile-arxiv` = 0.0086,
  `dolma1_7-wiki-en` = 0.0004
)

frames <- read_csv("data/frames.csv", show_col_types = FALSE)
dolma <- read_csv("data/counts-dolma.csv", show_col_types = FALSE)
generated <- read_csv("data/counts-generated.csv", show_col_types = FALSE)

for (needed in c(CONFIRMATORY, PRIMARY_INPUT)) {
  if (!needed %in% c(dolma$source, generated$source)) {
    fail("%s is missing from the counts", needed)
  }
}

counts <- bind_rows(dolma, generated)
conditions <- sort(unique(generated$source))
subsets <- sort(unique(dolma$source))

# --- descriptive -------------------------------------------------------------

rates <- counts %>%
  inner_join(select(frames, frame_id, gloss, family), by = "frame_id") %>%
  poisson_rates()

composite <- counts %>%
  group_by(source) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  poisson_rates()

# --- the primary contrast ----------------------------------------------------
#
# One test: the confirmatory generated condition against the web portion of the
# training mix. Uncorrected, because it is one test.

fit_all <- counts %>%
  drop_empty_frames() %>%
  prepare(reference = CONFIRMATORY) %>%
  fit_frames_glmm()

df_frames <- n_distinct(drop_empty_frames(counts)$frame_id) - 1

primary <- contrast(fit_all, plus = CONFIRMATORY, minus = PRIMARY_INPUT,
                    df = df_frames) %>%
  mutate(comparison = "primary",
         supports_h1 = ratio > 1 & p_value < 0.05)

# Three secondary contrasts: the other conditions against the same input,
# Holm-corrected within that set.
secondary <- bind_rows(lapply(setdiff(conditions, CONFIRMATORY), function(cond)
  contrast(fit_all, plus = cond, minus = PRIMARY_INPUT, df = df_frames))) %>%
  mutate(p_holm = stats::p.adjust(p_value, "holm"), comparison = "secondary")

# Every subset against the primary input, so a reader can see how far the
# comparison depends on which part of the mix is called the input.
per_subset <- bind_rows(lapply(setdiff(subsets, PRIMARY_INPUT), function(s)
  contrast(fit_all, plus = CONFIRMATORY, minus = s, df = df_frames))) %>%
  mutate(comparison = "confirmatory condition against each subset")

# --- the whole mix, weighted by token share ----------------------------------
#
# The mix rate is the token-share-weighted average of the subset rates. Shares
# are in tokens and rates are per word, and tokens per word differ between
# prose and code, so this is an approximation and is reported as one.
#
# Its interval comes from the delta method: a Poisson count's rate has variance
# rate^2 / hits, so a weighted sum of rates has variance sum(w^2 * rate^2 /
# hits), and the ratio against the model's rate is taken on the log scale.

mix <- composite %>%
  filter(source %in% names(TOKEN_SHARES)) %>%
  mutate(share = TOKEN_SHARES[source])

if (!isTRUE(all.equal(sum(mix$share), 1, tolerance = 1e-3))) {
  message(sprintf("token shares present cover %.1f%% of the mix",
                  100 * sum(mix$share)))
}

mix_rate <- sum(mix$share * mix$rate)
mix_var <- sum((mix$share * mix$rate)^2 / mix$hits)
model_row <- composite %>% filter(source == CONFIRMATORY)
model_var <- model_row$rate^2 / model_row$hits

log_ratio <- log(model_row$rate / mix_rate)
log_se <- sqrt(model_var / model_row$rate^2 + mix_var / mix_rate^2)
whole_mix <- tibble(
  plus = CONFIRMATORY, minus = "whole mix (token-share weighted)",
  ratio = exp(log_ratio),
  ratio_lower = exp(log_ratio - 1.96 * log_se),
  ratio_upper = exp(log_ratio + 1.96 * log_se),
  p_value = 2 * stats::pnorm(-abs(log_ratio / log_se)),
  comparison = "secondary, approximate"
)

# --- robustness: without the partial frames ----------------------------------

partial <- frames$frame_id[frames$measurable != "yes"]
fit_without <- counts %>%
  filter(!frame_id %in% partial) %>%
  drop_empty_frames() %>%
  prepare(reference = CONFIRMATORY) %>%
  fit_frames_glmm()

without_partial <- contrast(
  fit_without, plus = CONFIRMATORY, minus = PRIMARY_INPUT,
  df = n_distinct(counts$frame_id[!counts$frame_id %in% partial]) - 1) %>%
  mutate(comparison = "primary, without the partial frames")

write_csv(rates, "data/rates-training.csv")
write_csv(composite, "data/composite-training.csv")
write_csv(bind_rows(primary, secondary, whole_mix, without_partial),
          "data/training-contrasts.csv")
write_csv(per_subset, "data/training-per-subset.csv")

message(sprintf(paste("\nPRIMARY: %s against %s, %d frames, one test,",
                      "uncorrected.\nFrame-by-source SD %.3f on the log scale."),
                CONFIRMATORY, PRIMARY_INPUT, df_frames + 1,
                random_effect_sd(fit_all)))
print(primary, width = Inf)
message(if (isTRUE(primary$supports_h1))
  "The model uses the frames more often than its training data: amplification."
  else
  "No evidence the model exceeds its training data's rate.")

message("\nSECONDARY: the other conditions against the same input, Holm within three")
print(secondary, width = Inf)

message("\nSECONDARY: the whole mix, token-share weighted and approximate")
print(whole_mix, width = Inf)

message("\nROBUSTNESS: the primary contrast without F10 and F13")
print(without_partial, width = Inf)

message("\nthe confirmatory condition against each subset")
print(per_subset, width = Inf)

message("\ncomposite rate per million words, all sources")
print(composite %>% mutate(across(rate:upper, ~round(.x, 1))), n = Inf)

message("\nwrote data/rates-training.csv, data/composite-training.csv,\n  data/training-contrasts.csv, data/training-per-subset.csv")
