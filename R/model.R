#!/usr/bin/env Rscript

# The model Studies 2 and 3 share, and the contrasts they take from it.
#
#   hits ~ frame_id + source + (1 | frame_source)
#          offset: log(words)
#
# It is Study 1's combined-sections model with `source` in place of `variety`:
# national varieties, generated conditions and corpus subsets are all sources
# of text, counted the same way. Frame enters as a fixed factor because base
# rates differ by orders of magnitude between frames, and the frame-by-source
# random effect carries each frame's own preference for each source, so a
# source effect is an average over frames and its interval reflects how much
# frames disagree.
#
# One observation per frame and source, so no separate cell-level effect: it
# would be the same grouping twice, and fitting both gives a degenerate
# Hessian.
#
# Intervals and p-values use a t reference with one degree of freedom per frame
# less one, because a source effect is replicated across frames rather than
# across cells. On synthetic grids the normal reference covered a known ratio
# 88-90% of the time against a nominal 95%; the t reference covered it 92%.
#
# `R/analyse.R` deliberately does not source this file. It is Study 1's
# registered analysis, it ran and produced results, and leaving it untouched
# is worth more than removing the duplication.

suppressPackageStartupMessages({
  library(dplyr)
})

fail <- function(...) stop(sprintf(...), call. = FALSE)

# Fit with bobyqa, and if lme4 reports a convergence failure, refit with
# Nelder-Mead. "Nearly unidentifiable: large eigenvalue ratio" is an advisory
# about scaling that the offset makes unavoidable, not a failure, so it is
# noted and accepted. Anything else is the convergence failure the
# registrations mean.
fit_frames_glmm <- function(d) {
  formula <- hits ~ frame_id + source + (1 | frame_source)
  advisory <- "nearly unidentifiable"
  notes <- character(0)
  for (opt in c("bobyqa", "Nelder_Mead")) {
    model <- suppressWarnings(
      lme4::glmer(formula, data = d, family = stats::poisson(),
                  offset = log(words),
                  control = lme4::glmerControl(
                    optimizer = opt, check.conv.singular = "ignore")))
    messages <- unlist(model@optinfo$conv$lme4$messages)
    failures <- messages[!grepl(advisory, messages)]
    if (length(failures) == 0) {
      if (length(messages) > 0) {
        message(sprintf("  %s reported: %s", opt,
                        paste(messages, collapse = "; ")))
      }
      return(model)
    }
    notes <- c(notes, sprintf("%s: %s", opt, paste(failures, collapse = "; ")))
  }
  fail("the composite model did not converge with bobyqa or Nelder-Mead:\n  %s",
       paste(notes, collapse = "\n  "))
}

# A frame with no hits in any source says nothing about sources, and left in
# the model its coefficient runs off to minus infinity.
drop_empty_frames <- function(d) {
  empty <- d %>%
    group_by(frame_id) %>%
    summarise(hits = sum(hits), .groups = "drop") %>%
    filter(hits == 0) %>%
    pull(frame_id)
  if (length(empty) > 0) {
    message(sprintf("no hits in any source, so left out of the model: %s",
                    paste(empty, collapse = ", ")))
  }
  filter(d, !frame_id %in% empty)
}

prepare <- function(d, reference) {
  levels_present <- unique(as.character(d$source))
  if (!reference %in% levels_present) {
    fail("the reference source %s is not in the data: %s", reference,
         paste(levels_present, collapse = ", "))
  }
  d %>%
    mutate(source = factor(source, levels = c(reference,
                                              setdiff(levels_present, reference))),
           frame_id = factor(frame_id),
           frame_source = interaction(frame_id, source, drop = TRUE))
}

# One contrast: the rate in `plus` against the rate in `minus`, as a ratio.
# Either may be the model's reference level, whose coefficient is zero.
contrast <- function(model, plus, minus, df) {
  b <- lme4::fixef(model)
  v <- as.matrix(stats::vcov(model))
  weights <- numeric(length(b))
  names(weights) <- names(b)
  for (term in c(plus = plus, minus = minus)) {
    name <- paste0("source", term)
    if (name %in% names(weights)) {
      weights[name] <- if (identical(term, plus)) 1 else -1
    } else if (!term %in% c(levels(model@frame$source)[1])) {
      fail("no coefficient for source %s", term)
    }
  }
  est <- sum(weights * b)
  se <- sqrt(drop(weights %*% v %*% weights))
  q <- stats::qt(0.975, df)
  tibble(
    plus = plus, minus = minus,
    ratio = exp(est),
    ratio_lower = exp(est - q * se),
    ratio_upper = exp(est + q * se),
    p_value = 2 * stats::pt(-abs(est / se), df)
  )
}

# A set of contrasts, Holm-corrected within the set when asked. Registrations
# say which sets are corrected together; nothing here decides that.
contrasts_against <- function(model, targets, reference, df, correct = TRUE) {
  out <- bind_rows(lapply(targets, function(target)
    contrast(model, plus = reference, minus = target, df = df)))
  out$p_holm <- if (correct) stats::p.adjust(out$p_value, "holm") else out$p_value
  out$correction <- if (correct) "holm" else "none"
  out
}

random_effect_sd <- function(model) {
  as.data.frame(lme4::VarCorr(model))$sdcor[1]
}

# Rates per million with exact Poisson intervals, for the descriptive tables.
poisson_rates <- function(d, per = 1e6) {
  out <- vapply(seq_len(nrow(d)), function(i) {
    ci <- stats::poisson.test(d$hits[i])$conf.int
    c(ci[1], ci[2])
  }, numeric(2))
  d %>%
    mutate(rate = hits / words * per,
           lower = out[1, ] / words * per,
           upper = out[2, ] / words * per)
}
