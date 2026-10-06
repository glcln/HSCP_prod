import os
import sys

def run_and_filter_command(base_command, filter_string, typeSig):
    try:
        command = "{} | grep '{}'".format(base_command, filter_string)
        lines = os.popen(command).read().splitlines()


        for line in lines:
            print("line : ", line) 
            direcName = line.split("_")[1] 

            if typeSig == "signal":
                #THIS BELOW IS FOR ALL SIGNALS EXCEPT ZPRIME
                direcName = "SIGNAL/V" + filter_string + "/" + line.split("_")[2] + "_V" + filter_string
                  
                #THIS IS FOR ZPRIME SPECIFICALLY
                #direcName = line.split("_")[2] + "_" + line.split("_")[3] + "_"+line.split("_")[4] + "_" + line.split("_")[5]  +"_V" + filter_string
         
            if not os.path.exists(direcName):
                os.makedirs(direcName)
            direcSplit = line.split("_")[1] +"_"+ line.split("_")[2] 

            if typeSig == "signal":
                #THIS BELOW IS FOR ALL SIGNALS EXCEPT ZPRIME
                direcSplit = line.split("_")[2] + "_" + line.split("_")[3]

                #THIS IS FOR ZPRIME SPECIFICALLY
                #direcSplit = line.split("_")[2] + "_" + line.split("_")[3] + "_" + line.split("_")[4]+ "_" + line.split("_")[5]

            newDir = os.path.join(direcName,direcSplit)
            print (newDir)

            if not os.path.exists(newDir):
                os.makedirs(newDir)

            new_command = "{}/{}".format(base_command, line)
            new_output = os.popen(new_command).read()

            updated_command = "{}/{}".format(new_command, new_output)            
            updated_output = os.popen(updated_command).read().splitlines()
            for p in range(len(updated_output)):
                trf_command = updated_command.rstrip('\n')
                #print(trf_command + "/" + str(updated_output[p])+"/")
                last_command = 'gfal-copy -r' + trf_command[7:] + "/" + str(updated_output[p])+"/" + " " + newDir + "/"
                print(last_command)
                os.system(last_command)


    except Exception as e:
        print("Error running the command: {}".format(e))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <Version> <data type>")
        sys.exit(1)

    filter_string = sys.argv[1]
    data_type = sys.argv[2]
    
    if(data_type == "SingleMu"):
        base_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/SingleMuon"
        run_and_filter_command(base_command, filter_string, data_type)

    elif(data_type == "MET"):
        base_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/MET"
        run_and_filter_command(base_command, filter_string, data_type)

    elif(data_type == "WJetsToLNu_0J"):
        base_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/WJetsToLNu_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8"
        run_and_filter_command(base_command, filter_string, data_type)

    elif(data_type == "WJetsToLNu_1J"):
        base_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/WJetsToLNu_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8"
        run_and_filter_command(base_command, filter_string, data_type)

    elif(data_type == "WJetsToLNu_2J"):
        base_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/WJetsToLNu_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8"
        run_and_filter_command(base_command, filter_string, data_type)
    
    elif(data_type == "signal"):
        raw_command = "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/"
        all_MC = os.popen(raw_command).read().splitlines()
        #signal_paths = [s for s in all_MC if "ZPrime" in s]
        signal_paths = [s for s in all_MC if "HSCP" in s]
        for p in signal_paths:
            run_and_filter_command(raw_command+p, filter_string, data_type)

