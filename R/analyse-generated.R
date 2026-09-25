#!/usr/bin/env Rscript

# Study 2: does a model's default register resemble the American end of the
# national-variety spread Study 1 measured?
#
# Registered at https://osf.io/qjgtc. The protocol is in
# docs/generation-protocol.md and the counting layer in docs/frame-mapping.md.
#
# Inputs:
#   data/counts-combined.csv   Study 1, the countable frames, sections combined
#   data/corpus-sizes.csv      Study 1's component word counts
#   data/counts-generated.csv  written by python/count_generated.py
#
# Usage:
#   python python/count_generated.py data/generated
#   Rscript R/analyse-generated.R

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

# Run from the repository root, as R/analyse.R is.
source("R/model.R")

CONFIRMATORY <- "base-1.0"
VARIETIES <- c("US", "GB", "IE", "AU", "ZA")

frames <- read_csv("data/frames.csv", show_col_types = FALSE)
generated <- read_csv("data/counts-generated.csv", show_col_types = FALSE)
study1 <- read_csv("data/counts-combined.csv", show_col_types = FALSE) %>%
  inner_join(read_csv("data/corpus-sizes.csv", show_col_types = FALSE) %>%
               filter(section == "all") %>%
               select(variety, words),
             by = "variety") %>%
  transmute(source = variety, frame_id, hits, words)

conditions <- sort(unique(generated$source))
if (!CONFIRMATORY %in% conditions) {
  fail("the confirmatory condition %s is not in data/counts-generated.csv: %s",
       CONFIRMATORY, paste(conditions, collapse = ", "))
}

# Study 1 could not count F06 at all, so the comparison against it uses the
# frames both sides have. The comparisons among conditions use all fifteen.
shared_frames <- intersect(unique(study1$frame_id), unique(generated$frame_id))
message(sprintf("%d frames shared with Study 1; %d in the generated text",
                length(shared_frames), n_distinct(generated$frame_id)))

# --- descriptive -------------------------------------------------------------

rates <- bind_rows(study1, generated) %>%
  inner_join(select(frames, frame_id, gloss, family), by = "frame_id") %>%
  poisson_rates()

composite <- bind_rows(study1, generated) %>%
  group_by(source) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  poisson_rates()

# --- confirmatory: the model against the national varieties ------------------

against_varieties <- bind_rows(study1, generated) %>%
  filter(frame_id %in% shared_frames) %>%
  drop_empty_frames() %>%
  prepare(reference = CONFIRMATORY)

fit_varieties <- fit_frames_glmm(against_varieties)
df_varieties <- n_distinct(against_varieties$frame_id) - 1

# H1 is directional against the four non-American varieties. The comparison
# against US is reported with its interval and has no predicted direction, but
# it is corrected with the rest because it was registered as one of the five.
confirmatory <- contrasts_against(
  fit_varieties, targets = VARIETIES, reference = CONFIRMATORY,
  df = df_varieties, correct = TRUE) %>%
  mutate(supports_h1 = minus != "US" & ratio > 1 & p_holm < 0.05)

# --- registered comparisons among the conditions -----------------------------

among_conditions <- generated %>%
  drop_empty_frames() %>%
  prepare(reference = CONFIRMATORY)

fit_conditions <- fit_frames_glmm(among_conditions)
df_conditions <- n_distinct(among_conditions$frame_id) - 1

among <- contrasts_against(
  fit_conditions, targets = setdiff(conditions, CONFIRMATORY),
  reference = CONFIRMATORY, df = df_conditions, correct = TRUE)

# --- per-frame ratios, descriptive -------------------------------------------

per_frame <- rates %>%
  filter(source %in% c(CONFIRMATORY, VARIETIES), frame_id %in% shared_frames) %>%
  select(frame_id, gloss, family, source, hits, words, rate) %>%
  tidyr::pivot_wider(names_from = source, values_from = c(hits, words, rate))

write_csv(rates, "data/rates-generated.csv")
write_csv(composite, "data/composite-generated.csv")
write_csv(confirmatory, "data/generated-vs-varieties.csv")
write_csv(among, "data/generated-among-conditions.csv")
write_csv(per_frame, "data/generated-per-frame.csv")

message(sprintf(paste("\nCONFIRMATORY: %s against the national varieties,",
                      "%d frames.\nHolm across %d comparisons. Frame-by-source",
                      "SD %.3f on the log scale."),
                CONFIRMATORY, df_varieties + 1, nrow(confirmatory),
                random_effect_sd(fit_varieties)))
print(confirmatory, width = Inf)

message(sprintf(paste("\nREGISTERED COMPARISONS among the four conditions,",
                      "%d frames.\nHolm within this set of %d."),
                df_conditions + 1, nrow(among)))
print(among, width = Inf)

message("\ncomposite rate per million words, all sources")
print(composite %>% mutate(across(rate:upper, ~round(.x, 1))), n = Inf)

message("\nwrote data/rates-generated.csv, data/composite-generated.csv,\n  data/generated-vs-varieties.csv, data/generated-among-conditions.csv,\n  data/generated-per-frame.csv")
