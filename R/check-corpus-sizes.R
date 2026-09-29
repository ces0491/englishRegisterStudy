#!/usr/bin/env Rscript

# Recomputes the word counts in data/corpus-sizes.csv from GloWbE's
# downloadable metadata, and fails if any of them differs.
#
# Two rules, because the file holds two kinds of row. The blog and general
# rows come from the TEXTS page's section columns and have to match the
# metadata exactly. The `all` rows, which D2 made the offset of the
# confirmatory analysis, come from that page's Total column, which no sum of
# the metadata reproduces: every metadata row carries a genre, so the sections
# are all there is to add up, and D1 records the Total column running
# 0.055-0.088% above General plus Blog. Those rows are checked against the
# section total with that tolerance, which is the strongest check the metadata
# supports. Before this they were joined against rows that cannot exist, so
# every one of them came back NA and the script could never pass.
#
# The metadata is the "download metadata" link on the GloWbE TEXTS page (the
# document icon beside the corpus title): a zip holding glowbe_sources.txt,
# one row per web page with its word count, country and genre (G or B). It is
# third-party data and is not committed here.
#
# Usage:
#   Rscript R/check-corpus-sizes.R path/to/glowbe_sources.txt

suppressPackageStartupMessages({
  library(dplyr)
  library(readr)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 1 || !file.exists(args[1])) {
  stop("give the path to glowbe_sources.txt from the GloWbE metadata download",
       call. = FALSE)
}

# Tab-separated, Latin-1, with a row of dashes under the header. Country and
# genre share one field, separated by a space ("AU B ").
# Word counts are read as doubles because an integer sum overflows past
# 2^31 - 1.
sources <- read_tsv(args[1], skip = 2,
                    col_names = c("text_id", "words", "country_genre"),
                    col_types = cols_only(text_id = col_integer(),
                                          words = col_double(),
                                          country_genre = col_character()),
                    locale = locale(encoding = "latin1"), quote = "",
                    progress = FALSE)

if (anyNA(sources$words)) {
  stop(sprintf("%d rows have no readable word count",
               sum(is.na(sources$words))), call. = FALSE)
}

sums <- sources %>%
  mutate(variety = sub("^(\\S+)\\s+(\\S+).*$", "\\1", country_genre),
         genre = sub("^(\\S+)\\s+(\\S+).*$", "\\2", country_genre),
         section = c(G = "general", B = "blog")[genre]) %>%
  count(variety, section, wt = words, name = "metadata_words")

# The Total column's excess over General plus Blog, from D1. A recorded `all`
# row has to sit inside it: at or above the section total, and no more than
# this far above.
TOTAL_TOLERANCE <- 0.002

expected <- sums %>%
  group_by(variety) %>%
  summarise(metadata_words = sum(metadata_words), .groups = "drop") %>%
  mutate(section = "all") %>%
  bind_rows(sums)

recorded <- read_csv("data/corpus-sizes.csv", show_col_types = FALSE) %>%
  select(variety, section, words)

check <- recorded %>%
  left_join(expected, by = c("variety", "section")) %>%
  mutate(
    excess = (words - metadata_words) / metadata_words,
    match = case_when(
      is.na(metadata_words) ~ FALSE,
      section == "all" ~ excess >= 0 & excess <= TOTAL_TOLERANCE,
      TRUE ~ words == metadata_words))

message(sprintf("%d pages read from %s", nrow(sources), args[1]))
print(check, n = Inf)

if (!all(check$match)) {
  stop("data/corpus-sizes.csv does not match the metadata", call. = FALSE)
}
message(sprintf(paste("section word counts match the metadata exactly, and",
                      "each `all` row sits\nbetween the section total and",
                      "%.1f%% above it (largest here %.3f%%)"),
                TOTAL_TOLERANCE * 100,
                max(check$excess[check$section == "all"]) * 100))
