from gettext import find
from token_parser import TokenParser
import javalang
from javalang import tree
import os
import pandas as pd
import codecs


from pandarallel import pandarallel
pandarallel.initialize()

import sys
sys.setrecursionlimit(50000)

error_file_list = []

def parse_func(content, file_path):
    tokens = javalang.tokenizer.tokenize(content)
    parser = javalang.parser.Parser(tokens)
    tree = parser.parse_member_declaration()
    for statement in tree.body:
        print(statement)
    file_path = os.path.abspath(file_path)
    
    tree_parser = TokenParser()
    tree_parser.parse(tree, file_path)        
    print(tree_parser.dump())

    return tree

def extract_funcs(tree):
    print(tree.text)
    exit(0)

def parse_file(file_path, opt_file_path):
    file_path = os.path.abspath(file_path)

    if os.path.exists(opt_file_path):
        os.remove(opt_file_path)

    tree = None
    try:
        file_content = None
        with codecs.open(file_path, 'r', encoding='utf-8', errors='ignore') as fileIn:
            file_content = fileIn.read()

        tokens = javalang.tokenizer.tokenize(file_content)
        parser = javalang.parser.Parser(tokens)
        tree = parser.parse()
    except Exception as e:
        # print('exception when parse file: {}, msg: {}'.format(file_path, e))
        tree = None

    if tree is None:
        try:
            file_content = None
            with codecs.open(file_path, 'r', encoding='utf-8', errors='ignore') as fileIn:
                file_content = fileIn.readlines()
            # pos = file_content.find('\n')
            # file_content = file_content[pos+1:]
            # 忽略文件中import或class之前的内容
            firstIdx = 0
            for i in range(0, len(file_content)):
                if(file_content[i].strip().startswith('import') 
                # or file_content[i].find('class') != -1
                or file_content[i].strip().startswith('class')
                or file_content[i].strip().startswith('public')
                or file_content[i].strip().startswith('static')
                ):
                    firstIdx = i
                    break;
            
            file_content = ''.join(file_content[firstIdx:])

            tokens = javalang.tokenizer.tokenize(file_content)
            parser = javalang.parser.Parser(tokens)
            tree = parser.parse()
        except Exception as e:
            print('exception again when parse file: {}, msg: {}'.format(file_path, e))
            tree = None
        

    try:
        # print(tree)
        token_parser = TokenParser()
        token_parser.parse(tree, file_path=file_path, opt_file_path=opt_file_path)

        # print_tree(tree)
    except Exception as e:
        print('exception when parse tokens: {}, msg: {}'.format(file_path, e))
        
def print_tree(root):
    que = []
    que.append([root])

    depth = 0
    while len(que)>0:
        print('\ndepth: {}'.format(depth))
        depth += 1
        size = len(que)
        for i in range(0, size):
            node_arr = que.pop(0)
            print('[ ', end="")
            for node in node_arr:
                if(node == None or (type(node)==list and len(node)==0)):
                    continue

                print("{}, ".format(node), end="")

                if(not isinstance(node, tree.Node)):
                    que.append([])
                    continue
                next = []
                for child in node.children:
                    if(type(child) == list):
                        next.extend(child)
                    elif(isinstance(child, tree.Node)):
                        next.append(child)
                    # if(isinstance(child, tree.Node)):
                    #     que.extend(node.children)
                que.append(next)
            print(' ]', end="")


def list_all_files(dir_path, suffix=''):
    file_list = []
    paths = os.walk(dir_path)
    for dir_path, dir_names, file_names in paths:
        for file_name in file_names:
            if file_name.endswith(suffix):
                file_list.append(os.path.abspath(os.path.join(dir_path, file_name)))

    return file_list

def list_sub_dir(dir_path):
    return [os.path.join(dir_path, o) for o in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, o))]

def get_pure_name(file_path):
    file_name = os.path.basename(file_path)
    dot_pos = file_name.rfind('.')
    if dot_pos==-1:
        return file_name
    else:
        return file_name[0:dot_pos]
    
def parse_dir(src_dir_path, opt_dir_path):
    if not os.path.exists(opt_dir_path):
        os.makedirs(opt_dir_path)


    # 生成输出列表
    file_list = list_all_files(dir_path=src_dir_path, suffix='.java')

    print('parse dir: {}'.format(src_dir_path))
    print('parse files num: {}'.format(len(file_list)))

    opt_file_list = []
    opt_file_occur = {}
    for src_file in file_list:
        pure_name = get_pure_name(src_file)
        if pure_name not in opt_file_occur:
            opt_file_occur[pure_name] = 1
            opt_file_list.append(os.path.join(opt_dir_path, pure_name+'.out'))
        else:
            opt_file_occur[pure_name] += 1
            opt_file_list.append(os.path.join(opt_dir_path, pure_name+'__'+str(opt_file_occur[pure_name])+'.out'))
    # print(opt_file_occur['0'])
    # 
    file_pd = pd.DataFrame({'src_file': file_list, 'opt_file': opt_file_list})
    file_pd.parallel_apply(lambda x: parse_file(x['src_file'], x['opt_file']), axis=1)
    # file_pd.apply(lambda x: parse_file(x['src_file'], x['opt_file']), axis=1)

def parse_dir_for_sampled(src_dir_path, opt_dir_path):
    if not os.path.exists(opt_dir_path):
        os.makedirs(opt_dir_path)


    # 生成输出列表
    file_list = list_all_files(dir_path=src_dir_path, suffix='.java')

    print('parse dir: {}'.format(src_dir_path))
    print('parse files num: {}'.format(len(file_list)))

    src_file_list = []
    opt_file_list = []
    opt_file_occur = {}
    for src_file in file_list:
        # 忽略对假克隆对的解析
        if src_file.find('false-sampled-pairs') != -1:
            continue
        src_file_list.append(src_file)

        pure_name = get_pure_name(src_file)
        if pure_name not in opt_file_occur:
            opt_file_occur[pure_name] = 1
            opt_file_list.append(os.path.join(opt_dir_path, pure_name+'.out'))
        else:
            opt_file_occur[pure_name] += 1
            opt_file_list.append(os.path.join(opt_dir_path, pure_name+'__'+str(opt_file_occur[pure_name])+'.out'))
    # print(opt_file_occur['0'])
    # 
    print('real file num: ', len(src_file_list))
    file_pd = pd.DataFrame({'src_file': src_file_list, 'opt_file': opt_file_list})
    file_pd.parallel_apply(lambda x: parse_file(x['src_file'], x['opt_file']), axis=1)
    # file_pd.apply(lambda x: parse_file(x['src_file'], x['opt_file']), axis=1)

def parse_bcb_subs(in_dir, opt_dir):
    sub_dir_list = list_sub_dir(in_dir)
    for sub_dir in sub_dir_list:
        cur_opt_dir = os.path.join(opt_dir, get_pure_name(sub_dir))
        parse_dir(sub_dir, cur_opt_dir)

if __name__ == '__main__':
    if(len(sys.argv) != 7):
        print('python parse.py -i /path/to/dataset -o /path/to/output -m bcb/common')
        exit(0)

    mode = 'bcb'
    inputDir = ''
    outputDir = ''
    for i in [1, 3, 5]:
        if sys.argv[i] == '-m':
            mode = sys.argv[i+1]
        elif sys.argv[i] == '-i':
            inputDir = sys.argv[i+1]
        elif sys.argv[i] == '-o':
            outputDir = sys.argv[i+1]

    if inputDir=='' or not os.path.exists(inputDir):
        print('input dir not exist: {}'.format(inputDir))
        exit(0)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)
    
    if mode == 'bcb':
        parse_bcb_subs(inputDir, outputDir)
    elif mode == 'common':
        parse_dir(inputDir, outputDir)
    else:
        print('error mode: {}'.format(mode))