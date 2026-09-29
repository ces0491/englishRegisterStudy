#!/usr/bin/env Rscript

# Study 4's estimator: a rate as a ratio of totals, with a standard error taken
# from the variation between the units the totals are made of.
#
#   rate     R = sum(h) / sum(w)          h hits, w words, one pair per unit
#   Var(R)     = n / (n - 1) * sum((h - R * w)^2) / sum(w)^2
#
# A unit is a generated text, a training document, a preference pair or, for
# the stage-1 data Study 3 recorded per file, a drawn file. The variance is the
# ratio estimator's linearisation, so it assumes nothing about how hits are
# distributed within a unit or across units; it does assume units are
# independent draws.
#
# Two arms are compared on the log scale, with a Wald interval:
#
#   log(R_a / R_b),  SE^2 = Var(R_a) / R_a^2 + Var(R_b) / R_b^2
#
# Chosen and rejected responses to the same prompt are not independent, so the
# paired comparison takes each pair's linearised contribution to both rates.
#
# This serves the contrastive-family outcome. Study 4's composite outcome uses
# the model Studies 2 and 3 share, in R/model.R, so that it means the same
# thing in all four studies.
#
# R/calibrate-ratio.R checks the intervals' coverage on the counts Studies 2
# and 3 already hold.

fail <- function(...) stop(sprintf(...), call. = FALSE)

ratio_rate <- function(hits, words) {
  n <- length(hits)
  if (n < 2) fail("a rate needs at least two units, got %d", n)
  if (length(words) != n) fail("hits and words differ in length")
  total_words <- sum(words)
  rate <- sum(hits) / total_words
  list(rate = rate,
       var = n / (n - 1) * sum((hits - rate * words)^2) / total_words^2,
       n = n, hits = sum(hits), words = total_words)
}

wald <- function(est, se, level) {
  z <- stats::qnorm(1 - (1 - level) / 2)
  data.frame(ratio = exp(est), lower = exp(est - z * se),
             upper = exp(est + z * se), se_log = se,
             p_value = 2 * stats::pnorm(-abs(est / se)))
}

# Two independent arms: the rate in `a` over the rate in `b`.
compare_rates <- function(a, b, level = 0.95) {
  if (a$hits == 0 || b$hits == 0) fail("a log ratio needs hits in both arms")
  wald(log(a$rate / b$rate),
       sqrt(a$var / a$rate^2 + b$var / b$rate^2), level)
}

# Paired arms: member 1 over member 2, one row per pair.
compare_paired <- function(h1, w1, h2, w2, level = 0.95) {
  n <- length(h1)
  if (n < 2 || any(lengths(list(w1, h2, w2)) != n)) {
    fail("paired arms need the same number of pairs, at least two")
  }
  r1 <- sum(h1) / sum(w1)
  r2 <- sum(h2) / sum(w2)
  if (r1 == 0 || r2 == 0) fail("a log ratio needs hits in both arms")
  u <- (h1 - r1 * w1) / (r1 * sum(w1)) - (h2 - r2 * w2) / (r2 * sum(w2))
  wald(log(r1 / r2), sqrt(n / (n - 1) * sum(u^2)), level)
}
