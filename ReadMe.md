<h2>0. Introduction</h2>

* ccstokener: clone detection tool
* 8projects: four java open source projects and four c open source projects.
* java-label-pairs: the files in **pairs.zip** are the sampled true pairs and false pairs from four java open source projects. **astnn.zip** and **tbccd.zip** are the clone pairs organized into the format used by ASTNN and TBCCD.

<h2>1. Install Dependency</h2>

CCStokener runs under Python3 environment, and you should first install **pandarallel** package to run CCStokener. After performing clone detection, the results of clone pairs will be stored in **results** directory.
    
    pip3 install pandarallel

<h2>2. How to run CCStokener to perform clone detection</h2>

Our tool, CCStokener, is in directory **ccstokener**, now it supports detection for c and java language. **runner.py** is the runner file.

    python runner.py -i /path/to/dataset -m common/bcb -l java/c [-t 0.6]

* -i: path to dataset
* -m: detection mode. If you detect on BigCloneBench, the mode will be **bcb**, otherwise, the mode will be **common**.
* -l: language of datasets, now we support detection for **java** and **c** languages.
* -t: similarity threshold of clone pairs, it is optional. If it is not setting, we will use the default threshold.

***_Example:_*** You can run CCStokener as follows to perform clone detection for BigCloneBench.

    python runner.py -i /home/datasets/BigCloneEval-master/ijadataset/bcb_reduced -m bcb -l java



<h2>3. How to use CCStokener to verify whether clone pairs are true or not? </h2>

We support verify whether clone pairs are true or not. The clone pairs should edit in a file firstly, then call **verify.py** as follows to verify. 

    python verify.py -i /path/to/dataset -l java/c

* -i: path to the clone pair files directory.
* -l: language of clone pair, support java or c language.