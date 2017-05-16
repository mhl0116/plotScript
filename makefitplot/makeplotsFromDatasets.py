import ROOT
from subprocess import call
import os.path
import sys
import makefitplot as fplt

tag = "fullRange"
#process = "H4L"
#process = "Z4L"
process = "ZZ4L"
#process = "Z2L"

pdfName1 = "doubleCB_1"
pdfName2 = "gauss_1"
plotdir = "20170516_residual_1overpT"

plotpath = "/home/mhl/public_html/2017/"+plotdir+"/"+process+"_"+tag+"/"
if (not os.path.exists(plotpath)):
   call('mkdir -p ' + plotpath, shell=True)
   call('cp /home/mhl/public_html/index.php ' + plotpath, shell=True)
else:
   continueFit =  raw_input('plot dir exsit, overwrite ? : ')
   if (not (continueFit == "y" or continueFit == "yes") ):
      print "plots exsit, move them away or create new dir first !"
      sys.exit()
   else:
      call('rm  ' + plotpath + '*.png',shell=True)
      call('rm  ' + plotpath + '*.pdf',shell=True)
      call('rm  ' + plotpath + '*.txt',shell=True)

datafilepath = "/raid/raid9/mhl/HZZ4L_Run2_post2017Moriond/roodatasets/"

xLow = -0.2
xHigh = 0.2
xBins = 100

# save fitted parameters 
summaryTxtPath = "/raid/raid9/mhl/HZZ4L_Run2_post2017Moriond/txtfiles/"
summaryTxtName = process + "_muPtResidual_eta_"+tag+".txt"
summaryTxt = summaryTxtPath+summaryTxtName
if (os.path.exists(summaryTxt)): 
   call('rm ' + summaryTxt, shell=True)

#pTs = [5,20,30,40,50,60,100]
pTs = [5,10,15,20,25,30,35,40,50,60,100]
pTs[:] = [1.0/x for x in pTs]
pTs = pTs[::-1]
etas = [0.0,0.5]#,1.4,2.4]

for i in range(len(pTs)-1):
    for j in range(len(etas)-1):

        pTLow = pTs[i]
        pTHigh = pTs[i+1]
        etaLow = etas[j]
        etaHigh = etas[j+1]
        config = {\
        "x_low":xLow,\
        "x_high":xHigh,\
        "x_bins":xBins,\
        "doLogy":False,\
        "xTitle":"(pT_{reco}-pT_{gen})/pT_{gen}",\
        "yTitle":"Events/" + str((xHigh-xLow)/xBins),\
        "savepath":plotpath
        }

        config["savename"] = "muPtResidual_pt_" + str(pTLow).replace(".","p") + "_" + str(pTHigh).replace(".","p") \
                                       + "_eta_" + str(etaLow).replace(".","p") + "_" + str(etaHigh).replace(".","p") + "_dcb"
        logDataset = ''
        logCut = ''

        datasets = []

        # gather information from 4 leptons
        for k in [1,2,3,4]:

            datasetfile = "muPtResidual_pt_" + process + "_L"+str(k)+".root"
            datafile = ROOT.TFile(datafilepath + datasetfile)
            logDataset += datafilepath + datasetfile + '\n'
            tmpworkspace = datafile.Get("w_out")
            dataset = tmpworkspace.obj("dataset")

#            cut = "passedFullSelection > 0.5 && mass4l > " + str(m4lLow) + " && mass4l < " + str(m4lHigh) + " && finalState == 1 && \
#                   pTGENL" + str(k) + " > " + str(pTLow) + " && pTGENL" + str(k) + " < " + str(pTHigh) + " && \
#                   abs(etaL" + str(k) + ") > " + str(etaLow) + " && abs(etaL" + str(k) + ") < " + str(etaHigh) 
            cut =  "1/pTGENL" + str(k) + " > " + str(pTLow) + " && 1/pTGENL" + str(k) + " < " + str(pTHigh) + " && \
                   abs(etaL" + str(k) + ") > " + str(etaLow) + " && abs(etaL" + str(k) + ") < " + str(etaHigh)
            logCut += cut + '\n'

#            rv_passedFullSelection = ROOT.RooRealVar("passedFullSelection","",0,2)
#            rv_mass4l = ROOT.RooRealVar("mass4l","",m4lLow,m4lHigh)
#            rv_finalState = ROOT.RooRealVar("finalState","",0,5)
            rv_genPt = ROOT.RooRealVar("pTGENL"+str(k),"",5,100)
            rv_pT = ROOT.RooRealVar("pTL"+str(k),"",5,100)
            rv_eta = ROOT.RooRealVar("etaL"+str(k),"",-2.4,2.4)

            rv_x = ROOT.RooRealVar("x","",xLow,xHigh)

            dataset_select = ROOT.RooDataSet("dataset_select_"+str(k),"",dataset, ROOT.RooArgSet(rv_genPt,rv_pT,rv_eta,rv_x),cut)
#                                  ROOT.RooArgSet(rv_passedFullSelection,rv_mass4l,rv_finalState,rv_genPt,rv_pT,rv_eta,rv_x),cut)
  
            # plot only interesting variable x, and avoid problem when append if different dataset have different columns  
            dataset_reduce = dataset_select.reduce(ROOT.RooArgSet(rv_x))
            datasets.append(dataset_reduce)

        # append x from 4 leptons into one dataset, ready for fit and plot
        dataset_append = ROOT.RooDataSet(datasets[0], "dataset_append")
        dataset_append.append(datasets[1])
        dataset_append.append(datasets[2])
        dataset_append.append(datasets[3])

        # make a new class for fit plot
        fplot = fplt.MakeFitPlot(config) # config needed in MakePlot
        fplot.MakePdfFactory()
        pdf1 = fplot.w.pdf(pdfName1)
        fplot.fitResult = pdf1.fitTo(dataset_append, ROOT.RooFit.Save(True))

        fplot.config["dataset"] = dataset_append
        fplot.config["pdf"] = pdf1
 
        fplot.MakePlot()
        fplt.WriteLog(config["savepath"]+config["savename"],"dataset:\n " + logDataset)
        fplt.WriteLog(config["savepath"]+config["savename"],"cut:\n " + logCut,False)

        # save sigma and alpha1,2 from fitted dcb, proceed with gaussian fit
        sigma = fplot.w.var("sigmaDCB").getVal() 
        alpha1 = fplot.w.var("alphaDCB").getVal()
        alpha2 = fplot.w.var("alpha2").getVal()
        newFitRange = min(alpha1,alpha2)*sigma*0.8

        # make new dataset, only allow data with smaller x range [-sigma*min(a1,a2), sigma*min(a1,a2)] * somefactor
        dataset_reduce = dataset_append.reduce("abs(x) < " + str(newFitRange))
        # set up config for second make fit plot class
        config["x_low"] = -1*newFitRange
        config["x_high"] = newFitRange
        config["x_bins"] = 30
        config["yTitle"] = "Events/" + str(round((config["x_high"]-config["x_low"])/config["x_bins"],5) )
        config["savename"] = config["savename"].replace("dcb","gauss")

        # second class for fit plot
        fplot2 = fplt.MakeFitPlot(config)
        fplot2.MakePdfFactory()
        pdf2 = fplot2.w.pdf(pdfName2)
        fplot2.fitResult = pdf2.fitTo(dataset_reduce, ROOT.RooFit.Save(True))
        fplot2.config["dataset"] = dataset_reduce
        fplot2.config["pdf"] = pdf2

        fplot2.MakePlot()
        fplt.WriteLog(config["savepath"]+config["savename"],"dataset:\n " + logDataset)
        fplt.WriteLog(config["savepath"]+config["savename"],"cut:\n " + logCut,False)
        fplt.WriteLog(config["savepath"]+config["savename"], "x > " + str(-1*newFitRange) + " && x < " + str(newFitRange) )

        with open(summaryTxt, "a+") as myfile:
             myfile.write(' '.join([str(pTLow),str(pTHigh),str(etaLow),str(etaHigh), \
             str(fplot2.w.var("meanGauss").getVal() ), \
             str(fplot2.w.var("meanGauss").getError() ) ] ) + '\n' )
        myfile.close()
