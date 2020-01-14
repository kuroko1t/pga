#MIT License
#
#Copyright (c) 2020 kurosawa
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import re, os
from collections import OrderedDict
import argparse
from colorama import Fore, Back, Style

KEYWORDS = [
    "class ",
    "def ",
    "import ",
    '\"\"\"'
]

class Analy:
    def __init__(self, path):
        self.path = path

    def get_file(self):
        pyfiles = []
        for root, dirs, files in os.walk(self.path):
            fpy = [f for f in  files if '.py' in f]
            for f in fpy:
               pyfiles.append(root + '/' + f)
        return pyfiles

    def __key_pattern(self):
        key_pts = []
        for word in KEYWORDS:
            key_pts.append(re.compile(f'{word}'))
        return key_pts

    def index(self, path):
        """
        return : indexes [index num, sentence]
        """
        indexes = []
        with open(path) as f:
            lines = f.readlines()
        index_pt = re.compile('(\s*)(.*)')
        for line in lines:
            ind = index_pt.match(line)
            if ind:
                if len(ind.group(2)) != 0:
                    indexes.append([len(ind.group(1)), ind.group(2)])
        return indexes

    def group(self, indexes):
        """
        class_index : {line num(almost): index}
        """
        class_index, def_index, import_index, child_index, comment_index = OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict(), OrderedDict()

        key_pts = self.__key_pattern()
        FLAG = True
        comment_i = 0
        comment_sentence = ""
        comment_count = 0
        for i, index in enumerate(indexes):
            for key_num, key_pt in enumerate(key_pts):
                if key_pt.match(index[1]):
                    if key_num == 0: # class
                        index[1] = index[1].replace('class ', '')
                        class_index[i] = index
                    elif key_num == 1: # def
                        index[1] = index[1].replace('def ', '')
                        def_index[i] = index
                    elif key_num == 2: # import
                        import_index[i] = index
                    elif key_num == 3: # comment
                        if re.search('\"\"\".+\"\"\"$', index[1]):
                            comment_index[i] = index[1]
                            COMMENT_FLAG = False
                        else:
                            comment_i = i
                            comment_count +=1
                            comment_sentence += index[1]
                            COMMENT_FLAG = True
                    else:
                        assert True, "NO KEYWORDS!!"
                    FLAG = False
                    break
                if comment_count == 1: # comment
                    if re.search('\"\"\"', index[1]):
                        comment_sentence += index[1]
                        comment_index[comment_i] = comment_sentence
                        comment_count = 0
                        comment_sentence = ''
                    else:
                        comment_sentence += index[1]
                    break
            if FLAG:
                child_index[i] = index
        #print(comment_index)
        return class_index, def_index, import_index, comment_index

    def rank(self, class_index, def_index, import_index):
        def_rank = {}
        for din in def_index.keys():
            parent_class = None
            for cin in class_index.keys():
                if cin < din:
                    parent_class = cin
            def_rank[din] = parent_class
        return def_rank

    def comment_rank(self, index, comment_index):
        """comment_rank: index is def or class index not comment index"""
        comment_rank = {}
        for coin in comment_index.keys():
            if coin-1 in index:
                comment_rank[coin-1] = index[coin-1]
        return comment_rank

    def run(self):
        files = self.get_file()
        files_class_index, files_def_index, files_import_index, files_comment_index, files_def_rank = {}, {} , {}, {}, {}
        files_comment_def_rank, files_comment_class_rank = {}, {}
        for f in files:
            indexes = self.index(f)
            class_index, def_index, import_index, comment_index = self.group(indexes)
            def_rank = self.rank(class_index, def_index, import_index)
            files_class_index[f] = class_index
            files_def_index[f] = def_index
            files_import_index[f] = import_index
            files_comment_index[f] = comment_index
            files_def_rank[f] = def_rank
            files_comment_def_rank[f] = self.comment_rank(def_index, comment_index)
            files_comment_class_rank[f] = self.comment_rank(class_index, comment_index)
        return files_class_index, files_def_index, files_import_index, files_comment_index, files_def_rank, files_comment_def_rank, files_comment_class_rank
    
    def print_class(self, files_class_index, files_comment_index, files_comment_class_rank):
        for f, class_index in files_class_index.items():
            if len(class_index) != 0:
                print(Fore.CYAN + f'-- {f} --' + Style.RESET_ALL)
                for cline, cin in class_index.items():
                    print(cin[1])
                    if cline in files_comment_class_rank[f]:
                        print(Fore.BLUE + files_comment_index[f][cline+1] + Style.RESET_ALL)
                        print()

    def print_def(self, files_def_index, files_def_rank, files_class_index, files_comment_def_rank):
        for f, def_rank in files_def_rank.items():
            print(Fore.CYAN + f'-- {f} --' + Style.RESET_ALL)
            for din, cin in def_rank.items():
                def_index = files_def_index[f][din]
                if cin != None:
                    class_index = files_class_index[f][cin]
                    #print(Fore.BLUE + class_index[1] +  '->'+ def_index[1] + Style.RESET_ALL)
                    print(class_index[1] + ' -> '+ def_index[1])
                else:
                    #print(Fore.BLUE + def_index[1] + Style.RESET_ALL)
                    print(def_index[1])
                if din in files_comment_def_rank[f]:
                    print(Fore.BLUE + files_comment_index[f][din+1] + Style.RESET_ALL)
                print()
                    
if __name__ == "__main__":
    ### Parser ###
    parser = argparse.ArgumentParser(description='Recursive Analysis python Program')
    parser.add_argument('-c', '--class_print', action='store_true', help='show class list')
    parser.add_argument('-d', '--def_print', action='store_true', help='show function list')
    parser.add_argument('-p', '--path', type=str, help='root path for analysis')
    args = parser.parse_args()
    ##############

    if args.path == None:
        assert False, "Set path using -p option"
    analy = Analy(args.path)
    files_class_index, files_def_index, files_import_index, files_comment_index, files_def_rank, files_comment_def_rank, files_comment_class_rank = analy.run()
    if args.class_print:
        print('## class List ##')
        analy.print_class(files_class_index, files_comment_index, files_comment_class_rank)
    if args.def_print:
        print('## def List ##')
        analy.print_def(files_def_index, files_def_rank, files_class_index, files_comment_def_rank)
