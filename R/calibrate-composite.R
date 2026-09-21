#!/usr/bin/env Rscript

# Why the composite in R/analyse.R is a GLMM. Simulates the Study 1 grid with a
# known GB/US ratio of 0.7 and no variety x section interaction, fits four
# candidate models, and reports how often each one's 95% interval covers the
# truth and how often its genre test falsely splits by section.
#
# Two data-generating processes:
#   cell: independent multiplicative noise in every frame x variety x section cell
#   fv:   a frame x variety effect shared by both sections, plus small cell noise
# Models: quasi-Poisson, negative binomial, Poisson GLMM with an
# observation-level random effect, and the Poisson GLMM with
# (1 | frame:variety) + (1 | cell) that analyse.R uses.
#
# Component totals are near the published GB and ZA sizes; the blog/general
# split, the other totals and every base rate are invented. No GloWbE count was
# looked at. The run takes around half an hour.
#
# Usage:
#   Rscript R/calibrate-composite.R

suppressPackageStartupMessages({ library(dplyr); library(MASS); library(lme4) })
set.seed(2)

frames <- readr::read_csv("data/frames.csv", show_col_types = FALSE)
V <- c("US", "GB", "IE", "AU", "ZA"); S <- c("blog", "general")
sizes <- tidyr::expand_grid(variety = V, section = S) %>%
  mutate(words = c(130, 250, 130, 257, 30, 70, 50, 100, 15, 30) * 1e6)
base <- setNames(c(2, 0.3, 40, 20, 0.5, 0.4, 3, 15, 1, 25, 0.2, 0.3, 300, 30, 0.6),
                 frames$frame_id)
truth <- c(US = 1, GB = 0.7, IE = 0.8, AU = 0.9, ZA = 1)
ctrl <- glmerControl(optimizer = "bobyqa", check.conv.singular = "ignore")

sim <- function(sd_fv, sd_cell) {
  fv <- tidyr::expand_grid(frame_id = frames$frame_id, variety = V) %>%
    mutate(u = rnorm(n(), 0, sd_fv))
  d <- tidyr::expand_grid(frame_id = frames$frame_id, variety = V, section = S) %>%
    left_join(sizes, by = c("variety", "section")) %>%
    left_join(fv, by = c("frame_id", "variety")) %>%
    mutate(mu = base[frame_id] * words / 1e6 * truth[variety] *
             exp(u + rnorm(n(), 0, sd_cell)),
           hits = rpois(n(), mu),
           variety = factor(variety, V), section = factor(section, S),
           fv = interaction(frame_id, variety), obs = factor(seq_len(n())),
           lw = log(words))

  covers <- function(est, se) abs(est - log(0.7)) < 1.96 * se
  out <- c()

  qp <- glm(hits ~ frame_id + variety + section, quasipoisson(), offset = lw, data = d)
  qpi <- update(qp, . ~ . + variety:section)
  s <- summary(qp)$coefficients["varietyGB", ]
  out[c("QP_cov", "QP_split", "QP_est")] <-
    c(covers(s[1], s[2]), anova(qp, qpi, test = "F")$`Pr(>F)`[2] < .05, s[1])

  nb <- suppressWarnings(glm.nb(hits ~ frame_id + variety + section + offset(lw), data = d))
  nbi <- suppressWarnings(update(nb, . ~ . + variety:section))
  s <- summary(nb)$coefficients["varietyGB", ]
  out[c("NB_cov", "NB_split", "NB_est")] <-
    c(covers(s[1], s[2]), anova(nb, nbi)$`Pr(Chi)`[2] < .05, s[1])

  ol <- glmer(hits ~ frame_id + variety + section + (1 | obs), poisson, offset = lw,
              data = d, control = ctrl)
  oli <- update(ol, . ~ . + variety:section)
  s <- summary(ol)$coefficients["varietyGB", ]
  out[c("OLRE_cov", "OLRE_split", "OLRE_est")] <-
    c(covers(s[1], s[2]), suppressMessages(anova(ol, oli))$`Pr(>Chisq)`[2] < .05, s[1])

  fm <- glmer(hits ~ frame_id + variety + section + (1 | fv) + (1 | obs), poisson,
              offset = lw, data = d, control = ctrl)
  fmi <- update(fm, . ~ . + variety:section)
  s <- summary(fm)$coefficients["varietyGB", ]
  out[c("FV_cov", "FV_split", "FV_est")] <-
    c(covers(s[1], s[2]), suppressMessages(anova(fm, fmi))$`Pr(>Chisq)`[2] < .05, s[1])
  out
}

conds <- list(c("cell", 0, 0.15), c("cell", 0, 0.30),
              c("fv", 0.2, 0.05), c("fv", 0.4, 0.05))
for (cnd in conds) {
  r <- t(replicate(150, suppressWarnings(suppressMessages(
    sim(as.numeric(cnd[2]), as.numeric(cnd[3]))))))
  cat(sprintf("\n%s  sd_fv=%s sd_cell=%s\n", cnd[1], cnd[2], cnd[3]))
  for (m in c("QP", "NB", "OLRE", "FV")) {
    cat(sprintf("  %-5s coverage %.2f   false split %.2f   GB est sd %.3f\n", m,
                mean(r[, paste0(m, "_cov")]), mean(r[, paste0(m, "_split")]),
                sd(exp(r[, paste0(m, "_est")]))))
  }
}
