
library(ecospat)
library(raster)

boycei<-function(interval,obs,fit){
  
  fit.bin<-fit
  obs.bin<-obs
  fit.bin[fit[]>=interval[1]&fit[]<=interval[2]]<-"i";fit.bin[fit.bin!="i"]<-0
  obs.bin[obs[]>=interval[1]&obs[]<=interval[2]]<-"i";obs.bin[obs.bin!="i"]<-0
  
  pi<-length(which(obs.bin=="i"))/length(obs)
  ei<-length(which(fit.bin=="i"))/length(fit.bin)
  fi<-pi/ei
  
  return(fi)
}


ecospat.boyce <- function (fit, obs, nclass = 0, window.w = "default", res = 100,
                           PEplot = T)
{
  if(class(fit)=="RasterLayer"){
    if(class(obs)=="data.frame"){
      obs<-extract(fit, obs)}
    fit<-getValues(fit)
    fit <- fit[!is.na(fit)]
  }
  
  if (window.w == "default") {
    window.w <- (max(fit) - min(fit))/10
  }
  
  interval <- c(min(fit), max(fit))
  mini <- interval[1]
  maxi <- interval[2]
  
  if (nclass == 0) {
    vec.mov <- seq(from = mini, to = maxi - window.w, by = (maxi - mini - window.w)/res)
    vec.mov[res + 1] <- vec.mov[res + 1] + 1
    interval <- cbind(vec.mov, vec.mov + window.w)
  }
  else if (length(nclass) > 1) {
    vec.mov <- c(mini, nclass)
    interval <- cbind(vec.mov, c(vec.mov[-1], maxi))
  }
  else if (nclass > 0 & length(nclass) < 2) {
    vec.mov <- seq(from = mini, to = maxi, by = (maxi - mini)/nclass)
  }


  f <- apply(interval, 1, boycei, obs, fit)
  
  if (length(f[which(f != "NaN")]) <= 2) {
    b <- NA
  }
  else {
    b <- cor(f[which(f != "NaN")], vec.mov[which(f != "NaN")],
             method = "spearman")
  }
  ID <- seq(1:(length(vec.mov)))
  HS <- apply(interval, 1, sum)/2
  if (PEplot == T)
    plot((apply(interval[which(f != "NaN"), ], 1, sum)/2),
         f[which(f != "NaN")], xlab = "Habitat suitability",
         ylab = "Predicted/Expected ratio")
  results <- list(F.ratio = f, Spearman.cor = round(b, 3), HS = HS,
                  ID = ID)
  return(results)
}

###############################################################


obs <- read.csv("my_species_presence_points.csv")# two columns data representing the X and Y as species coordinate
fit <- raster("my_model_output.tif")

boyce.index <- ecospat.boyce(fit,obs[,2:3], nclass=0, window.w="default", res=100, PEplot=T)# here my X and Y are in column 2 and column 3 in obs data so I used the args "obs[,2:3]" and you have to define your X and Y in your species data in same way