#!/usr/bin/env Rscript
library(ggplot2)
args = commandArgs(trailingOnly=TRUE)

readScheds <- function(fn) {
        df <- data.frame("Day"=character(), "Temperature"=double(), "EndTime"=character(), stringsAsFactors=FALSE)
        inp <- readLines(fn)
        for (i in inp) {
                spl <- strsplit(i, "=")
                spl_j <- strsplit(spl[[1]][[2]], ";")
                for (j in spl_j[[1]]) {
                        spl_k <- strsplit(j[[1]], ">")
                        y <- 0
                        for (k in spl_k) {
                                df[nrow(df)+1,] = list(trimws(spl[[1]][[1]]),trimws(k[[1]]),trimws(k[[2]]))
                        }
                }
        }
        return(df)
}

shift <- function(x, n){
          c(x[-(seq(n))], rep("24:00", n))
}

datasets <- readScheds(args[1])
monday <- datasets[datasets$Day=="MONDAY",]
monday[nrow(monday)+1,] = list("MONDAY", "0.0", "00:00")
monday <- monday[with(monday, order(EndTime)), ]
monday$EndTime <- shift(monday$EndTime, 1)


print(monday)
i <- ggplot(monday, aes(EndTime, Temperature, group = 1))
i + geom_step(direction="vh")

