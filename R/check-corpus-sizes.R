#!/usr/bin/env Rscript

# Recomputes the section word counts in data/corpus-sizes.csv from GloWbE's
# downloadable metadata, and fails if any of them differs.
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

recorded <- read_csv("data/corpus-sizes.csv", show_col_types = FALSE) %>%
  select(variety, section, words)

check <- recorded %>%
  left_join(sums, by = c("variety", "section")) %>%
  mutate(match = !is.na(metadata_words) & words == metadata_words)

message(sprintf("%d pages read from %s", nrow(sources), args[1]))
print(check, n = Inf)

if (!all(check$match)) {
  stop("data/corpus-sizes.csv does not match the metadata", call. = FALSE)
}
message("all section word counts match the metadata")
