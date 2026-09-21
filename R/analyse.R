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
  mutate(variety = factor(variety, levels = VARIETIES),
         section = factor(section, levels = SECTIONS))

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
# standard as the rates rather than reported bare beside them. They are
# registered as descriptive: 120 of them, uncorrected, and no claim rests on one.
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
# varieties on a Poisson interval would be overconfident. Fifteen frames with
# base rates orders of magnitude apart need frame as a factor, and the frames a
# variety happens to favour vary too - a frame Irish writers avoid is likely
# avoided in blogs and general pages alike. That preference is a
# frame-by-variety random effect, shared across sections, and a cell-level
# random effect takes whatever noise is left in each count. So the variety
# ratio is an average over frames of this kind, not a count-weighted total
# dominated by the commonest frame.
#
# Quasi-Poisson and negative binomial were both tried against synthetic data
# first. With frame preferences shared across sections, quasi-Poisson intervals
# covered a known ratio 15-16% of the time and negative binomial 77-79%; this
# model covered it 93%.
#
# The hypothesis is directional: each other variety uses the frames less than
# US, so a ratio below 1. Tests are two-sided at 0.05 with Holm's correction
# across the confirmatory set, and a variety supports the hypothesis only when
# its ratio is below 1 and its Holm-adjusted p is under 0.05.

# A frame with no hits in any cell says nothing about varieties, and left in the
# model its coefficient runs off to minus infinity. It leaves the model and is
# reported; it stays in the rates above.
empty_frames <- dat %>%
  group_by(frame_id) %>%
  summarise(hits = sum(hits), .groups = "drop") %>%
  filter(hits == 0) %>%
  pull(frame_id)
modelled <- dat %>% filter(!frame_id %in% empty_frames)

# Variety-vs-US ratios from a fitted model: one per variety for the common
# effect, or one per variety and section from the interaction model. Wald
# intervals and p-values on the same normal reference, so an interval that
# excludes 1 and p < 0.05 always agree.
variety_ratios <- function(model, by_section) {
  b <- lme4::fixef(model)
  v <- as.matrix(stats::vcov(model))
  grid <- tidyr::expand_grid(
    variety = setdiff(VARIETIES, "US"),
    section = if (by_section) SECTIONS else NA_character_
  )
  est <- se <- numeric(nrow(grid))
  for (i in seq_len(nrow(grid))) {
    # Treatment contrasts with blog as the reference section: the general-
    # section effect is the main effect plus the interaction term.
    terms <- paste0("variety", grid$variety[i])
    if (by_section && grid$section[i] != SECTIONS[1]) {
      terms <- c(terms, paste0(terms, ":section", grid$section[i]))
    }
    stopifnot(all(terms %in% names(b)))
    L <- as.numeric(names(b) %in% terms)
    est[i] <- sum(L * b)
    se[i] <- sqrt(drop(L %*% v %*% L))
  }
  z <- stats::qnorm(0.975)
  p <- 2 * stats::pnorm(-abs(est / se))
  sds <- as.data.frame(lme4::VarCorr(model))
  out <- grid %>%
    mutate(
      ratio = exp(est),
      ratio_lower = exp(est - z * se),
      ratio_upper = exp(est + z * se),
      p_value = p,
      p_holm = stats::p.adjust(p, method = "holm"),
      supports_hypothesis = ratio < 1 & p_holm < 0.05,
      sd_frame_variety = sds$sdcor[sds$grp == "frame_variety"],
      sd_cell = sds$sdcor[sds$grp == "cell"],
      reference = "US"
    )
  if (by_section) out else select(out, -section)
}

# Fit with bobyqa, and if lme4 reports a convergence failure, refit with
# Nelder-Mead. If both fail the script stops rather than reporting estimates
# from a model that did not converge; working around that is a declared
# deviation. A singular fit, where a random-effect variance is estimated at
# zero, is a legitimate answer rather than a failure: it means that source of
# variation is not detectable, and the model reduces to the simpler one.
fit_glmm <- function(formula, d) {
  for (opt in c("bobyqa", "Nelder_Mead")) {
    m <- lme4::glmer(formula, data = d, family = stats::poisson(),
                     offset = log(words),
                     control = lme4::glmerControl(
                       optimizer = opt, check.conv.singular = "ignore"))
    if (length(m@optinfo$conv$lme4$messages) == 0) return(m)
  }
  fail("the composite model did not converge with bobyqa or Nelder-Mead:\n  %s",
       paste(m@optinfo$conv$lme4$messages, collapse = "\n  "))
}

# The genre control the design leans on: if the variety effect differs between
# the blog and general sections, the common effect hides it, and the
# per-section ratios from the interaction model become the confirmatory set.
# A likelihood-ratio test, since both models are fitted by maximum likelihood.
composite_analysis <- function(d) {
  d <- d %>%
    mutate(frame_variety = interaction(frame_id, variety, drop = TRUE),
           cell = factor(seq_len(n())))
  fit <- fit_glmm(hits ~ frame_id + variety + section +
                    (1 | frame_variety) + (1 | cell), d)
  fit_interaction <- fit_glmm(hits ~ frame_id + variety * section +
                                (1 | frame_variety) + (1 | cell), d)
  list(
    common = variety_ratios(fit, by_section = FALSE),
    by_section = variety_ratios(fit_interaction, by_section = TRUE),
    genre_test = stats::anova(fit, fit_interaction),
    singular = lme4::isSingular(fit) || lme4::isSingular(fit_interaction)
  )
}

primary <- composite_analysis(modelled)
genre_test <- primary$genre_test
split_by_section <- isTRUE(genre_test$`Pr(>Chisq)`[2] < 0.05)
confirmatory <- if (split_by_section) primary$by_section else primary$common

# Robustness: the same analysis without the frames marked partial in
# frames.csv. A partial frame such as "and that 's" matches far more than the
# construction it stands for, so this checks the result does not rest on what
# those two frames are really counting. It follows the primary analysis's
# choice of common or per-section effect rather than making its own.
sensitivity <- composite_analysis(filter(modelled, measurable == "yes"))
sensitivity_set <- if (split_by_section) sensitivity$by_section else sensitivity$common

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
write_csv(primary$common, "data/composite-ratios.csv")
write_csv(primary$by_section, "data/composite-ratios-by-section.csv")
write_csv(bind_rows(common = sensitivity$common,
                    by_section = sensitivity$by_section, .id = "model"),
          "data/composite-ratios-sensitivity.csv")

message(sprintf("%d cells: %d frames x %d varieties x %d sections",
                nrow(dat), n_distinct(dat$frame_id), n_distinct(dat$variety),
                n_distinct(dat$section)))
message(paste("wrote figures/frame-rates.png, data/rates.csv, data/composite.csv,",
              "\n  data/ratios-vs-us.csv, data/composite-ratios.csv,",
              "\n  data/composite-ratios-by-section.csv,",
              "data/composite-ratios-sensitivity.csv"))

if (length(empty_frames) > 0) {
  message(sprintf("\nno hits in any cell, so left out of the composite model: %s",
                  paste(empty_frames, collapse = ", ")))
}

if (primary$singular) {
  message(paste("\nsingular fit: a random-effect variance was estimated at zero.",
                "That source of\nvariation is not detectable here; see",
                "sd_frame_variety and sd_cell below."))
}

message(sprintf(
  "\nvariety x section interaction: likelihood ratio %.2f on %d df, p = %.3f.\n%s",
  genre_test$Chisq[2], genre_test$Df[2], genre_test$`Pr(>Chisq)`[2],
  if (split_by_section) {
    "The variety effect differs by section, so the per-section ratios are the\nconfirmatory result and the common effect is set aside."
  } else {
    "No evidence the variety effect differs between blog and general, so the\ncommon effect is the confirmatory result."
  }
))

message(sprintf(paste("\nconfirmatory set, Holm across %d ratios. Random-effect SDs on the",
                      "log scale:\nframe x variety %.3f, cell %.3f."),
                nrow(confirmatory), confirmatory$sd_frame_variety[1],
                confirmatory$sd_cell[1]))
print(confirmatory, width = Inf)

message("\nrobustness: the same, without the frames marked partial in frames.csv")
print(sensitivity_set, width = Inf)
