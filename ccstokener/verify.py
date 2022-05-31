# coding=utf-8

import os
import sys

if __name__ == '__main__':
    if(len(sys.argv) != 5):
        print('python verify.py -i /path/to/dataset -l c/java')
        exit(0)
    
    inputDir = ''
    outputDir = './tokens-verify'
    language = 'java'

    for i in [1,3]:
        if i >= len(sys.argv):
            break
        if sys.argv[i] == '-i':
            inputDir = sys.argv[i+1]
        elif sys.argv[i] == '-l':
            language = sys.argv[i+1]

    print('language: %s' % language)
    
    if len(inputDir)==0 or not os.path.exists(inputDir):
        print('input dir not exist: {}'.format(inputDir))
        exit(0)

    inputDir = os.path.realpath(inputDir)

    # extract semantic tokens
    print('extract semantic tokens...')
    if language == 'java':
        os.system('cd semantic-token-extract/java; python parse.py -i %s -o ../../tokens-verify -m %s' % (inputDir, 'common'))
    elif language == 'c':
        os.system('cd semantic-token-extract/c; java -jar c-parser.jar -i %s -o ../../tokens-verify' % (inputDir))
    else:
        print('unknown language: {}'.format(language))
        exit(0)

    # clone verification 
    print('performing clone verification...')
    os.system('./clone-detect/cloneverify -i ./tokens-verify -o ./results-verify -l {}'.format(language))

    os.system('rm -rf tokens-verify')

    print('results are stored in ./results-verify/')