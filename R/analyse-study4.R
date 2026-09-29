#!/usr/bin/env Rscript

# Study 4: where in Olmo 3's training does its excess of contrastive frames
# enter?
#
# Registered at https://osf.io/d79u4 and specified in docs/study4-protocol.md.
# Two co-primary outcomes, nine contrasts each, Holm across all eighteen:
#
#   family     F06 to F09 per unit of text, R/ratio.R's ratio estimator
#   composite  all fifteen frames, R/model.R's model over the fourteen sources,
#              as in Studies 2 and 3
#
# Inputs, all written by `python python/count_study4.py --collect data/study4`:
#   counts.csv                 hits and words per source and frame
#   units-generated.csv        one row per generated text
#   units-stage1.csv           Study 3's 200 common_crawl files
#   units-midtraining.csv      one row per midtraining file read
#   units-sft.csv.gz           one row per SFT conversation
#   units-dpo.csv.gz           one row per DPO pair
#
# Usage:
#   Rscript R/analyse-study4.R [data/study4]

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

source("R/model.R")
source("R/ratio.R")

args <- commandArgs(trailingOnly = TRUE)
DATA <- if (length(args) >= 1) args[1] else "data/study4"

FAMILY <- c("F06", "F07", "F08", "F09")
FAMILY_F10 <- c(FAMILY, "F10")

need <- c("counts.csv", "units-generated.csv", "units-stage1.csv",
          "units-midtraining.csv", "units-sft.csv.gz", "units-dpo.csv.gz")
missing <- need[!file.exists(file.path(DATA, need))]
if (length(missing) > 0) {
  fail("missing from %s: %s. Run the Study 4 counts and `python python/count_study4.py --collect %s` first.",
       DATA, paste(missing, collapse = ", "), DATA)
}
read <- function(name) read_csv(file.path(DATA, name), show_col_types = FALSE)
counts <- read("counts.csv")
generated <- read("units-generated.csv")
stage1 <- read("units-stage1.csv")
midtraining <- read("units-midtraining.csv")
sft <- read("units-sft.csv.gz")
dpo <- read("units-dpo.csv.gz")

ARMS <- c("B1", "B2", "B3", "N1", "N2", "N3", "P1", "P2", "P3")
SOURCES <- c(ARMS, "stage1", "midtraining", "sft", "dpo_chosen", "dpo_rejected")
absent <- setdiff(SOURCES, unique(counts$source))
if (length(absent) > 0) fail("counts.csv lacks sources: %s", paste(absent, collapse = ", "))
short <- generated %>% count(arm) %>% filter(n != 4000)
if (nrow(short) > 0) fail("arms without 4,000 texts: %s", paste(short$arm, collapse = ", "))

# --- the family: one rate per source, from its units -----------------------

hits_of <- function(d, frames, suffix = "") {
  rowSums(as.matrix(d[, paste0(frames, suffix)]))
}

family_rate <- function(source, frames = FAMILY) {
  d <- switch(source,
    stage1 = stage1, midtraining = midtraining, sft = sft,
    filter(generated, arm == source))
  ratio_rate(hits_of(d, frames), d$words)
}

# One contrast on the family. A contrast with no hits on either side has no
# log ratio: it is reported with its counts and enters Holm with p = 1.
family_contrast <- function(plus, minus, frames = FAMILY) {
  if (plus == "dpo_chosen" && minus == "dpo_rejected") {
    h1 <- hits_of(dpo, frames, "_chosen")
    h2 <- hits_of(dpo, frames, "_rejected")
    if (sum(h1) == 0 || sum(h2) == 0) {
      return(data.frame(ratio = NA, lower = NA, upper = NA, se_log = NA, p_value = 1))
    }
    return(compare_paired(h1, dpo$words_chosen, h2, dpo$words_rejected))
  }
  a <- family_rate(plus, frames)
  b <- family_rate(minus, frames)
  if (a$hits == 0 || b$hits == 0) {
    return(data.frame(ratio = NA, lower = NA, upper = NA, se_log = NA, p_value = 1))
  }
  compare_rates(a, b)
}

# --- the composite: Studies 2 and 3's model over the fourteen sources ------

composite_data <- counts %>%
  filter(source %in% SOURCES) %>%
  drop_empty_frames() %>%
  prepare(reference = "B3")
composite_fit <- fit_frames_glmm(composite_data)
composite_df <- n_distinct(composite_data$frame_id) - 1
composite_sd <- random_effect_sd(composite_fit)

composite_contrast <- function(plus, minus) {
  out <- contrast(composite_fit, plus = plus, minus = minus, df = composite_df)
  data.frame(ratio = out$ratio, lower = out$ratio_lower,
             upper = out$ratio_upper, p_value = out$p_value)
}

# --- the nine registered contrasts ------------------------------------------

CONFIRMATORY <- tribble(
  ~hypothesis, ~plus,         ~minus,         ~predicted,
  "H1",        "B1",          "stage1",       "plus",
  "H2",        "midtraining", "stage1",       "plus",
  "H3",        "B2",          "B1",           "plus",
  "H4",        "N1",          "N2",           "either",
  "H5",        "sft",         "B3",           "plus",
  "H6",        "P1",          "B3",           "plus",
  "H7",        "dpo_chosen",  "dpo_rejected", "plus",
  "H8",        "P2",          "P1",           "plus",
  "H9",        "P3",          "P2",           "plus"
)

run_contrasts <- function(spec, frames = FAMILY, with_composite = TRUE) {
  rows <- list()
  for (i in seq_len(nrow(spec))) {
    s <- spec[i, ]
    fam <- family_contrast(s$plus, s$minus, frames)
    rows[[length(rows) + 1]] <- cbind(s, outcome = "family",
                                      fam[, c("ratio", "lower", "upper", "p_value")])
    if (with_composite) {
      comp <- composite_contrast(s$plus, s$minus)
      rows[[length(rows) + 1]] <- cbind(s, outcome = "composite", comp)
    }
  }
  bind_rows(rows)
}

confirmatory <- run_contrasts(CONFIRMATORY) %>%
  mutate(p_holm = stats::p.adjust(p_value, "holm"),
         verdict = case_when(
           is.na(ratio) ~ "no hits on one side",
           p_holm >= 0.05 ~ "not supported",
           # N1's mix raises web, QA and instruction data together, and web
           # carries the family at the highest rate of the three, so the
           # verdict names the mix rather than one category in it.
           predicted == "either" & ratio > 1 ~ "favours the web, QA and instruction mix (N1)",
           predicted == "either" & ratio < 1 ~ "favours reasoning traces, math and code (N2)",
           ratio > 1 ~ "supported",
           TRUE ~ "evidence against"),
         sd_frame_source = ifelse(outcome == "composite", composite_sd,
                                  NA_real_))

# --- secondary, with intervals and no correction ------------------------------

SECONDARY <- tribble(
  ~hypothesis,                  ~plus,  ~minus,        ~predicted,
  "long-context stage",         "B3",   "B2",          "none",
  "Round 5 against Gen-QA",     "N3",   "N1",          "none",
  "Round 5 against math-code",  "N3",   "N2",          "none",
  "midtrained model vs its data", "B2", "midtraining",  "none",
  "SFT model vs its data",      "P1",   "sft",         "none"
)
secondary <- run_contrasts(SECONDARY)

# The family with the partial F10 added, for the nine registered contrasts.
sensitivity <- run_contrasts(CONFIRMATORY, frames = FAMILY_F10,
                             with_composite = FALSE) %>%
  mutate(outcome = "family with F10")

# Replication: this study's final base and final instruct text against
# Study 2's text from the same checkpoints, on the family.
study2 <- read_csv("data/counts-generated-by-text.csv", show_col_types = FALSE)
replication <- bind_rows(lapply(
  list(c("B3", "base-1.0"), c("P3", "instruct-1.0")), function(pair) {
    a <- family_rate(pair[1])
    d <- filter(study2, source == pair[2])
    b <- ratio_rate(hits_of(d, FAMILY), d$words)
    cbind(data.frame(hypothesis = "replication", plus = pair[1],
                     minus = paste("Study 2", pair[2]), predicted = "none",
                     outcome = "family"),
          compare_rates(a, b)[, c("ratio", "lower", "upper", "p_value")])
  }))

# Rates by midtraining category and source, SFT source dataset, and the models
# behind the DPO responses.
rate_table <- function(d, group, h, w) {
  d %>%
    mutate(.h = h, .w = w) %>%
    group_by(across(all_of(group))) %>%
    group_modify(function(g, key) {
      if (nrow(g) < 2) {
        return(tibble(units = nrow(g), words = sum(g$.w), hits = sum(g$.h),
                      per_million = sum(g$.h) / sum(g$.w) * 1e6,
                      lower = NA_real_, upper = NA_real_))
      }
      r <- ratio_rate(g$.h, g$.w)
      se <- sqrt(r$var)
      tibble(units = r$n, words = r$words, hits = r$hits,
             per_million = r$rate * 1e6,
             lower = max(0, r$rate - 1.96 * se) * 1e6,
             upper = (r$rate + 1.96 * se) * 1e6)
    }) %>%
    ungroup()
}

by_category <- rate_table(midtraining, "category", hits_of(midtraining, FAMILY),
                          midtraining$words)
by_source <- rate_table(midtraining, "source", hits_of(midtraining, FAMILY),
                        midtraining$words)
by_sft_dataset <- rate_table(sft, "source_dataset", hits_of(sft, FAMILY), sft$words)
by_dpo_model <- bind_rows(
  rate_table(dpo, "chosen_model", hits_of(dpo, FAMILY, "_chosen"),
             dpo$words_chosen) %>% rename(model = chosen_model) %>%
    mutate(side = "chosen"),
  rate_table(dpo, "rejected_model", hits_of(dpo, FAMILY, "_rejected"),
             dpo$words_rejected) %>% rename(model = rejected_model) %>%
    mutate(side = "rejected"))

# --- exploratory: per-frame rates, and length ----------------------------------

per_frame <- counts %>% poisson_rates()
by_length <- generated %>%
  mutate(family = hits_of(generated, FAMILY)) %>%
  group_by(arm, finish_reason) %>%
  summarise(texts = n(), words = sum(words), family = sum(family),
            .groups = "drop") %>%
  mutate(per_million = family / words * 1e6)

out <- function(table, name) write_csv(table, file.path(DATA, name))
out(confirmatory, "results-confirmatory.csv")
out(bind_rows(secondary, sensitivity, replication), "results-secondary.csv")
out(bind_rows(mutate(by_category, level = "category"),
              mutate(by_source, level = "source")), "results-midtraining.csv")
out(by_sft_dataset, "results-sft-datasets.csv")
out(by_dpo_model, "results-dpo-models.csv")
out(per_frame, "results-per-frame.csv")
out(by_length, "results-length.csv")

message(sprintf(paste("\nCONFIRMATORY: nine contrasts on two outcomes, Holm across",
                      "eighteen. Composite frame-by-source SD %.3f, %d frames."),
                composite_sd, composite_df + 1))
print(as_tibble(confirmatory) %>%
        mutate(across(c(ratio, lower, upper), ~ round(.x, 2)),
               across(c(p_value, p_holm), ~ signif(.x, 3))) %>%
        select(hypothesis, outcome, plus, minus, ratio, lower, upper, p_holm, verdict),
      n = Inf, width = Inf)
message(sprintf("\nwrote results to %s", DATA))
