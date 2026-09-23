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
# Two analyses, because the interface will not split every frame by section
# (deviation D2 in docs/deviations.md):
#
#   primary    14 frames, both sections combined, from data/counts-combined.csv
#   secondary   8 frames, blog and general apart, from data/counts.csv
#
# The primary answers the hypothesis on nearly the whole frame set. The
# secondary is the registered per-section model, and carries the genre control
# on the frames that allow it.
#
# Usage:
#   Rscript R/analyse.R
#   Rscript R/analyse.R path/to/counts.csv path/to/corpus-sizes.csv path/to/counts-combined.csv

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)
COUNTS <- if (length(args) >= 1) args[1] else "data/counts.csv"
SIZES <- if (length(args) >= 2) args[2] else "data/corpus-sizes.csv"
COMBINED <- if (length(args) >= 3) args[3] else "data/counts-combined.csv"
FRAMES <- "data/frames.csv"
VARIETIES <- c("US", "GB", "IE", "AU", "ZA")
SECTIONS <- c("blog", "general")

for (f in c(FRAMES, COUNTS, SIZES, COMBINED)) {
  if (!file.exists(f)) {
    stop(sprintf(
      "%s is missing. Copy the template beside it and fill it in from GloWbE;\nnothing here estimates a count.", f
    ), call. = FALSE)
  }
}

frames <- read_csv(FRAMES, show_col_types = FALSE)
counts <- read_csv(COUNTS, show_col_types = FALSE)
combined <- read_csv(COMBINED, show_col_types = FALSE)
sizes <- read_csv(SIZES, show_col_types = FALSE)

# What the interface allows per frame, recorded in frames.csv during
# collection: `split` counts in each section, `combined_only` refused a
# section-restricted search, `uncountable` could not be searched at all.
split_frames <- frames$frame_id[frames$interface == "split"]
countable <- frames$frame_id[frames$interface != "uncountable"]

# --- validation -------------------------------------------------------------
#
# Counts get typed in by hand from a rate-limited interface over several days,
# so every way that goes wrong is checked here. The omitted cell is the one to
# worry about: a cell that never got entered lowers that variety's summed rate
# and the output carries no sign of it.

fail <- function(...) stop(sprintf(...), call. = FALSE)

cells <- function(d) {
  section <- if ("section" %in% names(d)) paste0("/", d$section) else ""
  paste0("  ", d$frame_id, " ", d$variety, section, collapse = "\n")
}

check_counts <- function(d, label, frame_ids, sections) {
  if (!is.numeric(d$hits)) {
    fail(paste("%s: the hits column read as %s rather than a number, which",
               "means a word\nreached a hit cell. Notes belong in the notes",
               "column."), label, class(d$hits)[1])
  }

  unusable <- d %>% filter(is.na(hits) | hits < 0 | hits != floor(hits))
  if (nrow(unusable) > 0) {
    fail("%s: blank or non-integer hit counts (%d):\n%s", label,
         nrow(unusable), cells(unusable))
  }

  # A typo in a label gets dropped by the join rather than rejected, which
  # lands in the same place as an omission.
  known <- d %>% filter(!frame_id %in% frame_ids | !variety %in% VARIETIES)
  if (!is.null(sections)) {
    known <- d %>% filter(!frame_id %in% frame_ids | !variety %in% VARIETIES |
                            !section %in% sections)
  }
  if (nrow(known) > 0) {
    fail("%s: rows carrying an unrecognised frame, variety or section (%d):\n%s",
         label, nrow(known), cells(known))
  }

  by <- if (is.null(sections)) c("frame_id", "variety") else
    c("frame_id", "variety", "section")
  repeated <- d %>% count(across(all_of(by))) %>% filter(n > 1)
  if (nrow(repeated) > 0) {
    fail("%s: cells entered more than once (%d):\n%s", label, nrow(repeated),
         cells(repeated))
  }

  expected <- if (is.null(sections)) {
    tidyr::expand_grid(frame_id = frame_ids, variety = VARIETIES)
  } else {
    tidyr::expand_grid(frame_id = frame_ids, variety = VARIETIES,
                       section = sections)
  }
  gaps <- anti_join(expected, d, by = by)
  if (nrow(gaps) > 0) {
    fail(paste("%s: cells with no count (%d of %d). A partial grid understates",
               "whichever\nvariety is short:\n%s"),
         label, nrow(gaps), nrow(expected), cells(gaps))
  }
}

if (any(is.na(sizes$words))) {
  fail("corpus sizes have blanks; a rate cannot be computed without them")
}

size_grid <- tidyr::expand_grid(variety = VARIETIES,
                                section = c(SECTIONS, "all"))
size_gaps <- anti_join(size_grid, sizes, by = c("variety", "section"))
if (nrow(size_gaps) > 0) {
  fail("variety/section pairs with no corpus size (%d of %d):\n%s",
       nrow(size_gaps), nrow(size_grid),
       paste0("  ", size_gaps$variety, "/", size_gaps$section, collapse = "\n"))
}

check_counts(counts, COUNTS, split_frames, SECTIONS)
check_counts(combined, COMBINED, countable, NULL)

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

join_sizes <- function(d, section_value = NULL) {
  if (!is.null(section_value)) d$section <- section_value
  d %>%
    rename(count_note = any_of("notes")) %>%
    inner_join(frames, by = "frame_id") %>%
    inner_join(select(sizes, -any_of("notes")), by = c("variety", "section")) %>%
    bind_cols(poisson_ci(.$hits, .$words)) %>%
    mutate(variety = factor(variety, levels = VARIETIES))
}

dat <- join_sizes(counts) %>%
  mutate(section = factor(section, levels = SECTIONS))
dat_all <- join_sizes(combined, section_value = "all")

# --- the composite: the claim is about density, not any single frame --------
#
# No weighting. A weighted index would need a defensible reason for every
# weight, and there isn't one.
composite <- dat %>%
  group_by(variety, section) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  bind_cols(poisson_ci(.$hits, .$words))

composite_all <- dat_all %>%
  group_by(variety) %>%
  summarise(hits = sum(hits), words = first(words), .groups = "drop") %>%
  bind_cols(poisson_ci(.$hits, .$words))

# --- relative to US, which is the comparison the study is actually making ---
#
# A point ratio says nothing about whether a difference is real. These are
# exact conditional Poisson intervals on the rate ratio, so the comparison is
# held to the same standard as the rates rather than reported bare beside them.
# They are registered as descriptive: uncorrected, and no claim rests on one.
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

per_frame_ratios <- function(d, by) {
  reference <- d %>%
    filter(variety == "US") %>%
    select(all_of(c("frame_id", by)), hits_us = hits, words_us = words,
           rate_us = rate)
  d %>%
    filter(variety != "US") %>%
    select(all_of(c("frame_id", "gloss", "family", "variety", by)),
           hits, words, rate) %>%
    inner_join(reference, by = c("frame_id", by)) %>%
    bind_cols(rate_ratio(.$hits, .$words, .$hits_us, .$words_us)) %>%
    arrange(frame_id, variety)
}

ratios_all <- per_frame_ratios(dat_all, character(0))
ratios <- per_frame_ratios(dat, "section") %>% arrange(frame_id, section, variety)

# --- the composite, tested rather than asserted ------------------------------
#
# The composite claim is that a variety reaches for these frames more overall.
# The sums above answer it descriptively, and comparing those sums across
# varieties on a Poisson interval would be overconfident. Fifteen frames with
# base rates orders of magnitude apart need frame as a factor, and the frames a
# variety happens to favour vary too - a frame Irish writers avoid is likely
# avoided in blogs and general pages alike. That preference is a
# frame-by-variety random effect, and a cell-level random effect takes whatever
# noise is left in each count. So the variety ratio is an average over frames
# of this kind, not a count-weighted total dominated by the commonest frame.
#
# Quasi-Poisson and negative binomial were both tried against synthetic data
# first. With frame preferences shared across sections, quasi-Poisson intervals
# covered a known ratio 15-16% of the time and negative binomial 77-79%; this
# model covered it 93%. See R/calibrate-composite.R.
#
# The hypothesis is directional: each other variety uses the frames less than
# US, so a ratio below 1. Tests are two-sided at 0.05 with Holm's correction
# across the confirmatory set, and a variety supports the hypothesis only when
# its ratio is below 1 and its Holm-adjusted p is under 0.05.

# A frame with no hits in any cell says nothing about varieties, and left in the
# model its coefficient runs off to minus infinity. It leaves the model and is
# reported; it stays in the rates above.
empty_frames <- function(d) {
  d %>%
    group_by(frame_id) %>%
    summarise(hits = sum(hits), .groups = "drop") %>%
    filter(hits == 0) %>%
    pull(frame_id)
}

# Variety-vs-US ratios from a fitted model: one per variety for the common
# effect, or one per variety and section from the interaction model. Wald
# intervals and p-values on the same normal reference, so an interval that
# excludes 1 and p < 0.05 always agree.
variety_ratios <- function(model, by_section, df = NULL) {
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
  # The registered per-section model uses the normal reference. The combined
  # model uses a t reference with one degree of freedom per frame less one,
  # because the variety effect is replicated across frames rather than across
  # cells, and there are only fourteen frames. On synthetic data the normal
  # reference covered a known ratio 88-90% of the time; the t reference covered
  # it 92%. See R/calibrate-composite.R, which reruns both.
  q <- if (is.null(df)) stats::qnorm(0.975) else stats::qt(0.975, df)
  p <- if (is.null(df)) 2 * stats::pnorm(-abs(est / se)) else
    2 * stats::pt(-abs(est / se), df)
  sds <- as.data.frame(lme4::VarCorr(model))
  out <- grid %>%
    mutate(
      ratio = exp(est),
      ratio_lower = exp(est - q * se),
      ratio_upper = exp(est + q * se),
      p_value = p,
      p_holm = stats::p.adjust(p, method = "holm"),
      supports_hypothesis = ratio < 1 & p_holm < 0.05,
      sd_frame_variety = sds$sdcor[sds$grp == "frame_variety"],
      sd_cell = if (any(sds$grp == "cell")) sds$sdcor[sds$grp == "cell"] else NA_real_,
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
#
# lme4 may also warn "nearly unidentifiable: large eigenvalue ratio" here. That
# comes from the offset spanning orders of magnitude, not from a failure: it is
# not recorded among the fit's convergence messages, and rescaling a word count
# would not change the model.
fit_glmm <- function(formula, d) {
  # lme4 reports two kinds of thing here. "Model is nearly unidentifiable:
  # large eigenvalue ratio" is an advisory about scaling, which the offset
  # makes unavoidable: word counts run to hundreds of millions and rescaling
  # one would not change the model. It is noted and accepted. Anything else -
  # a failed gradient, a degenerate Hessian, max|grad| too large - is the
  # convergence failure the registration means, and triggers the refit.
  advisory <- "nearly unidentifiable"
  notes <- character(0)
  for (opt in c("bobyqa", "Nelder_Mead")) {
    m <- suppressWarnings(
      lme4::glmer(formula, data = d, family = stats::poisson(),
                  offset = log(words),
                  control = lme4::glmerControl(
                    optimizer = opt, check.conv.singular = "ignore")))
    msg <- unlist(m@optinfo$conv$lme4$messages)
    failures <- msg[!grepl(advisory, msg)]
    if (length(failures) == 0) {
      if (length(msg) > 0 || length(notes) > 0) {
        message(sprintf("  %s
    %s reported: %s", deparse1(formula), opt,
                        paste(c(msg, notes), collapse = "; ")))
      }
      return(m)
    }
    notes <- c(notes, sprintf("%s: %s", opt, paste(failures, collapse = "; ")))
  }
  fail("%s did not converge with bobyqa or Nelder-Mead:
  %s",
       deparse1(formula), paste(notes, collapse = "
  "))
}

with_ids <- function(d) {
  d %>% mutate(frame_variety = interaction(frame_id, variety, drop = TRUE),
               cell = factor(seq_len(n())))
}

# Primary: both sections combined, every countable frame. One random effect,
# not two: with the sections combined there is a single observation per frame
# and variety, so the frame-by-variety effect and a cell-level effect are the
# same grouping and only their sum is identified. Fitting both gives a
# degenerate Hessian. This term therefore carries both the frame's preference
# for a variety and the overdispersion of that count.
combined_analysis <- function(d) {
  d <- with_ids(d)
  fit <- fit_glmm(hits ~ frame_id + variety + (1 | frame_variety), d)
  list(ratios = variety_ratios(fit, by_section = FALSE,
                               df = n_distinct(d$frame_id) - 1),
       singular = lme4::isSingular(fit))
}

# Secondary: the registered per-section model on the frames that split. The
# genre control the design leans on: if the variety effect differs between the
# blog and general sections, the common effect hides it, and the per-section
# ratios from the interaction model are what to report. A likelihood-ratio
# test, since both models are fitted by maximum likelihood.
section_analysis <- function(d) {
  d <- with_ids(d)
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

empty_all <- empty_frames(dat_all)
empty_split <- empty_frames(dat)

primary <- combined_analysis(filter(dat_all, !frame_id %in% empty_all))
secondary <- section_analysis(filter(dat, !frame_id %in% empty_split))

genre_test <- secondary$genre_test
split_by_section <- isTRUE(genre_test$`Pr(>Chisq)`[2] < 0.05)
secondary_set <- if (split_by_section) secondary$by_section else secondary$common

# Robustness: the primary without the frames marked partial in frames.csv. A
# partial frame such as "and that 's" matches far more than the construction it
# stands for, so this checks the result does not rest on what those patterns
# are really counting. Both partial frames are combined-only, so the secondary
# analysis never contains one and needs no sensitivity rerun.
partial <- frames$frame_id[frames$measurable != "yes"]
sensitivity <- combined_analysis(
  filter(dat_all, !frame_id %in% empty_all, !frame_id %in% partial))

dir.create("figures", showWarnings = FALSE)

p <- ggplot(dat_all, aes(x = rate, y = reorder(gloss, rate), colour = variety)) +
  geom_errorbar(aes(xmin = lower, xmax = upper), orientation = "y", width = 0, alpha = 0.5) +
  geom_point(size = 2) +
  labs(
    title = "Rhetorical frames per million words, by variety of English",
    subtitle = "GloWbE, both sections. Bars are exact Poisson intervals on the underlying count.",
    x = "Occurrences per million words", y = NULL, colour = NULL
  ) +
  theme_minimal(base_size = 11) +
  theme(panel.grid.minor = element_blank())

ggsave("figures/frame-rates.png", p, width = 10, height = 7, dpi = 150)

ggsave("figures/frame-rates-by-section.png",
       p + dat + facet_wrap(~section) +
         labs(subtitle = "GloWbE, the frames the interface splits by section."),
       width = 10, height = 7, dpi = 150)

write_csv(dat_all, "data/rates-combined.csv")
write_csv(dat, "data/rates.csv")
write_csv(composite_all, "data/composite-combined.csv")
write_csv(composite, "data/composite.csv")
write_csv(ratios_all, "data/ratios-vs-us.csv")
write_csv(ratios, "data/ratios-vs-us-by-section.csv")
write_csv(primary$ratios, "data/composite-ratios.csv")
write_csv(sensitivity$ratios, "data/composite-ratios-sensitivity.csv")
write_csv(bind_rows(common = secondary$common,
                    by_section = secondary$by_section, .id = "model"),
          "data/composite-ratios-by-section.csv")

message(sprintf("primary: %d frames x %d varieties, both sections combined",
                n_distinct(dat_all$frame_id), n_distinct(dat_all$variety)))
message(sprintf("secondary: %d frames x %d varieties x %d sections",
                n_distinct(dat$frame_id), n_distinct(dat$variety),
                n_distinct(dat$section)))

for (e in list(list(empty_all, "primary"), list(empty_split, "secondary"))) {
  if (length(e[[1]]) > 0) {
    message(sprintf("\nno hits in any cell, so left out of the %s model: %s",
                    e[[2]], paste(e[[1]], collapse = ", ")))
  }
}
if (primary$singular || secondary$singular) {
  message(paste("\nsingular fit: a random-effect variance was estimated at zero.",
                "That source of\nvariation is not detectable here; see",
                "sd_frame_variety and sd_cell below."))
}

message(sprintf(paste("\nPRIMARY (confirmatory), Holm across %d ratios.",
                      "Random-effect SDs on the log scale:\nframe x variety",
                      "%.3f, cell %.3f."),
                nrow(primary$ratios), primary$ratios$sd_frame_variety[1],
                primary$ratios$sd_cell[1]))
print(primary$ratios, width = Inf)

message("\nrobustness: the primary without the frames marked partial in frames.csv")
print(sensitivity$ratios, width = Inf)

message(sprintf(
  "\nSECONDARY, the registered per-section model on the frames that split.\nvariety x section interaction: likelihood ratio %.2f on %d df, p = %.3f.\n%s",
  genre_test$Chisq[2], genre_test$Df[2], genre_test$`Pr(>Chisq)`[2],
  if (split_by_section) {
    "The variety effect differs by section, so the per-section ratios below are\nwhat to report from the secondary analysis."
  } else {
    "No evidence the variety effect differs between blog and general."
  }
))
print(secondary_set, width = Inf)

message("\nwrote figures/frame-rates.png, figures/frame-rates-by-section.png,\n  data/rates-combined.csv, data/rates.csv, data/composite-combined.csv,\n  data/composite.csv, data/ratios-vs-us.csv, data/ratios-vs-us-by-section.csv,\n  data/composite-ratios.csv, data/composite-ratios-sensitivity.csv,\n  data/composite-ratios-by-section.csv")
