import os
import sys

if __name__ == '__main__':
    if(len(sys.argv) != 9 and len(sys.argv)!=7):
        print('python runner.py -i /path/to/dataset -m common/bcb -t 0.6 -l c/java')
        exit(0)
    
    inputDir = ''
    outputDir = './tokens'
    threshold = 0.6
    mode = 'common'
    language = 'java'

    for i in [1,3,5,7]:
        if i >= len(sys.argv):
            break
        if sys.argv[i] == '-i':
            inputDir = sys.argv[i+1]
        elif sys.argv[i] == '-m':
            mode = sys.argv[i+1]
        elif sys.argv[i] == '-t':
            threshold = sys.argv[i+1]
        elif sys.argv[i] == '-l':
            language = sys.argv[i+1]

    print('language: %s' % language)

    if mode != 'bcb' and mode != 'common':
        print('the parameter of \'-m\' should be bcb or common')
        exit(0)
    
    if len(inputDir)==0 or not os.path.exists(inputDir):
        print('input dir not exist: {}'.format(inputDir))
        exit(0)

    inputDir = os.path.realpath(inputDir)

    # extract semantic tokens
    print('extract semantic tokens...')
    if language == 'java':
        os.system('cd semantic-token-extract/java; python parse.py -i %s -o ../../tokens -m %s' % (inputDir, mode))
    elif language == 'c':
        os.system('cd semantic-token-extract/c; java -jar c-parser.jar -i %s -o ../../tokens' % (inputDir))
    else:
        print('unknown language: {}'.format(language))
        exit(0)

    # clone detection
    print('performing clone detection...')
    os.system('./clone-detect/clonedetector -i ./tokens -o ./report -t {} -m {} -l {}'.format(threshold, mode, language))

    # collect results
    print('collect detection results...')
    os.system('rm -rf results; mkdir results')
    os.system('find ./report -type f -name "*.pair" | xargs cat >> ./results/clonepairs.txt')

    os.system('find ./report -type f -name "*.log" | xargs cat >> ./results/report.log')

    os.system('rm -rf tokens report')

    print('clone pairs are stored in ./results/clonepairs.txt')