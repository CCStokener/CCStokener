from javalang import tree
from javalang.ast import Node
import numpy as np
import os

from util import RoleType
from util import NodeType
from util import *

# max_node_size = 10
# node_to_index = {
#     'method_declaration': 0
#     , 
# }

# max_role_size = 10
# role_to_index = {
#     'basic_type': 1
#     , 'refer_type': 2
#     , 'variable': 3
    
# }


class Token(object):
    path = None
    role = None
    name = None
    count = 0
    
    def __init__(self):
        self.path = None
        self.role = None
        self.name = None
    
    def __init__(self, name, path, role):
        self.path = path
        self.name = name
        self.role = role
    
    def incre_path(self, path):
        if self.path is None:
            self.path = np.zeros(int(NodeType.NODE_TYPE_END))
        self.count += 1

        self.path = self.path + path

    def set_path(self, path):
        self.count += 1
        self.path = path
    
    def output(self):
        if self.path is None:
            return []
        return self.path.astype(int).tolist()
    
class Variable(Token):
    def __init__(self, type, name, path=None, window_size=0):
        self.type = type # 变量类型，如int, float等
        self.role = RoleType.VARIABLE
        self.name = name
        self.related_var = []

        if path is None:
            path= np.zeros(int(NodeType.NODE_TYPE_END))
        self.path = path

        self.window_index = 0
        self.window_size = window_size
        self.related_var_window = [[] for i in range(0, window_size)]
    
    def add_related_var(self, related_var):
        self.related_var_window[self.window_index] = related_var
        self.window_index = (self.window_index+1) % self.window_size
    
    def get_related_var(self):
        related_var = []
        for value in self.related_var_window:
            related_var.extend(value)
        return list(set(related_var))

class Relation(Token):
    def __init__(self, name, path=None):
        self.name = name
        self.path = path
        self.role = RoleType.EXPRE_RELATION
        
class FieldAccess(Token):
    def __init__(self, name):
        self.name = name
        self.role = RoleType.FILED

class VariableType(Token):
    def __init__(self, name, role):
        self.name = name
        self.role = role

class Method(Token):
    def __init__(self, name, path=None):
        self.name = name
        self.role = RoleType.METHOD
        self.path = path

class Qualifier(Token):
    def __init__(self, name):
        self.name = name

class Keyword(Token):
    def __init__(self, name):
        self.name = name

class TokenParser(object):
    def __init__(self):
        self.clear()
        self.file_path = None
        self.opt_file_path = None
        self.window_size = 3
        self.debug = 1
        self.method_depth = 0

    def clear(self):
        self.token_map = {}
        self.cur_path = []              # 单一路径
        # self.recorded_token_map = {}
        self.global_var_map = {}                # 变量
        self.global_field_map = {}              # 域访问
        self.global_type_map = {}               # 类型
        self.global_method_map = {}             # 函数
        self.global_qualifier_map = {}          # 类似于多级变量索引, 如a.b.c.d

        self.global_keyword_map = {}          # 关键字

        self.method_start = -1          # 方法的起始行 
        self.method_end = -1            # 方法的终止行

        self.valid_token_num = 0        # 有效的token, 如变量，标识符等, 不包含关键字，常量字符串
        self.total_token_num = 0        # token总数，有效token+无效token，即全部的token

        self.union_variable_list = []       # 关联合并的变量
        self.union_method_list = []         # 关联合并的函数
        self.union_expre_relation_list = [] # 关系表
    
    def dump(self):
        if((self.method_end-self.method_start+1)<6):
            return ""

        dump_str = '<block filePath:{}, startline:{}, endline:{}, validTokenNum:{}, totalTokenNum: {}>\n'   \
            .format(self.file_path, self.method_start, self.method_end, self.valid_token_num, self.total_token_num)

        # 输出variable
        dump_str += '<variable>\n'
        for key, value in self.global_var_map.items():
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
        dump_str += '</variable>\n'
        
        
        dump_str += ('<field>\n')
        for key, value in self.global_field_map.items():
            # dump_str += ('{}: {}\n'.format(key, value.output()))
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
        dump_str += ('</field>\n')
        
        dump_str += ('<method>\n')
        for key, value in self.global_method_map.items():
            # dump_str += ('{}: {}\n'.format(key, value.output()))
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
        dump_str += ('</method>\n')

        dump_str += '<keyword>\n'
        for key, value in self.global_keyword_map.items():
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
        dump_str += '</keyword>\n'

        dump_str += ('<type>\n')
        for key, value in self.global_type_map.items():
            if value.role == RoleType.BASIC_TYPE:
                continue
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
            # dump_str += ('{}: {}\n'.format(key, value.output()))
        dump_str += ('</type>\n')

        dump_str += ('<basic type>\n')
        for key, value in self.global_type_map.items():
            if value.role != RoleType.BASIC_TYPE:
                continue
            dump_str += ('{},{}: {}\n'.format(key, value.count, value.output()))
            # dump_str += ('{}: {}\n'.format(key, value.output()))
        dump_str += ('</basic type>\n')

        dump_str += '<variable group>\n'
        for obj in self.union_variable_list:
            dump_str += '{},1: {}\n'.format(obj.name, obj.output())
        dump_str += '</variable group>\n'

        dump_str += '<method group>\n'
        for obj in self.union_method_list:
            dump_str += '{},1: {}\n'.format(obj.name, obj.output())
        dump_str += '</method group>\n'

        dump_str += '<relation>\n'
        for obj in self.union_expre_relation_list:
            dump_str += '{},1: {}\n'.format(obj.name, obj.output())
        dump_str += '</relation>\n'


        dump_str += '</block>\n'

        return dump_str

    def logger(self, log_type, log_msg, log_obj=1):
        if log_obj is None:
            return 

        print(log_msg)
        if log_type == 'debug':
            exit(0)
        elif log_type == 'info':
            pass
        else:
            exit(1)

    
    def add_global_variable(self, name, type=None):
        if name is None or name == '':
            return 
        self.valid_token_num += 1
        self.total_token_num += 1

        if name not in self.global_var_map.keys():
            self.global_var_map[name] = Variable(type=type, name=name, window_size=self.window_size)

        if type is not None:
            self.global_var_map[name].type = type
            
        # self.global_var_map[name].incre_path(self.rearrange_path(self.cur_path))
        self.global_var_map[name].set_path(self.rearrange_path(self.cur_path))

        self.record_token('variable: {}, type: {}'.format(name, self.global_var_map[name].type))

    def add_global_field(self, name):
        if name is None or name == '':
            return 
        self.valid_token_num += 1
        self.total_token_num += 1

        self.record_token('field: {}'.format(name))
        
        if name not in self.global_field_map.keys():
            self.global_field_map[name] = FieldAccess(name=name)
        
        self.global_field_map[name].incre_path(self.rearrange_path(self.cur_path)) 

    def add_global_identifier(self, name):
        if name is None or name == '':
            return 
        self.total_token_num += 1

        self.record_token('identifier: {}'.format(name))

    def add_global_type(self, name, role):
        if name is None or name == '':
            return 
        self.valid_token_num += 1
        self.total_token_num += 1

        self.record_token('type: {}'.format(name))

        if name not in self.global_type_map.keys():
            self.global_type_map[name] = VariableType(name=name, role=role)
        self.global_type_map[name].incre_path(self.rearrange_path(self.cur_path)) 
        

    def add_global_method(self, name):
        if name is None or name == '':
            return 
        self.valid_token_num += 1
        self.total_token_num += 1

        self.record_token('method: {}'.format(name))

        if name not in self.global_method_map.keys():
            self.global_method_map[name] = Method(name=name)
        self.global_method_map[name].incre_path(self.rearrange_path(self.cur_path)) 

    # 将修饰符作为变量直接操作
    def add_global_qualifier(self, name):
        if name is None or name == '':
            return 

        self.add_global_variable(name=name)
        self.add_union_variable(name)
        # print('qulifier: ', end=',')
        # self.record_token('qualifier: {}'.format(name))
        # print('end_qulifier: ', end=',')

        # if name not in self.global_qualifier_map.keys():
        #     self.global_qualifier_map[name] = Qualifier(name=name)
            
    def add_global_modifier(self, name):
        if name is None or name == '':
            return 

        if type(name)==list:
            for modi in name:
                self.add_single_modifier(modi)
        else:
            self.add_single_modifier(name)

    def add_single_modifier(self, modifier):
        self.total_token_num += 1

        self.record_token('modifier: {}'.format(modifier))

    def add_global_keyword(self, name):
        if name is None or name == '':
            return 
        self.total_token_num += 1
        self.valid_token_num += 1

        self.record_token('keyword: {}'.format(name))

        if name not in self.global_keyword_map.keys():
            self.global_keyword_map[name] = Keyword(name=name)
        self.global_keyword_map[name].incre_path(self.rearrange_path(self.cur_path))

    def rearrange_path(self, path):
        path_np = np.zeros(int(NodeType.NODE_TYPE_END))
        for index in path:
            path_np[int(index)] += 1

        # 空类型
        # if path is None or len(path)==0:
        #     path_np[0] += 1

        return path_np
    
    def add_token(self, name, role, path):
        path = self.rearrange_path(path)
        if name in self.token_map.keys():
            self.token_map[name].incre_path(path)
        else:
            self.token_map[name] = Token(name, path, role)

    def add_union_relationship(self, name_arr):
        cur_path_np = self.rearrange_path(self.cur_path)
        if name_arr is None or type(name_arr) != list:
            self.union_expre_relation_list.append(Relation(name='None', path=cur_path_np))
            self.record_token('relation: {}, path: {}'.format(name_arr, None))

            # print('relation: {}, relate: {}'.format(name_arr, cur_path_np))
            return

        related_var_dict = self.get_related_var(name_arr, self.window_size)

        # print('relation: {}, relate: {}'.format(name_arr, related_var_dict))
        
        # 获取收集的向量和
        for node, cnt in related_var_dict.items():
            if node not in self.global_var_map.keys():
                continue
            cur_path_np += self.global_var_map[node].path

        self.union_expre_relation_list.append(Relation(name='-'.join(name_arr), path=cur_path_np)) 
        self.record_token('relation: {}, path: {}'.format(name_arr, cur_path_np))

    def add_union_variable(self, name, related_group=None):
        if(name is None or type(name) != str):
            return 
        
        # 获取当前路径的信息
        cur_path_np = self.rearrange_path(self.cur_path)

        if related_group is None or 'member' not in related_group.keys():
            # 如果不存在关联变量，则只记录当前路径信息
            self.union_variable_list.append(Variable(type=None, name=name, path=cur_path_np))
            # print('var: {}, relate: {}'.format(name, None))
            return 
        
        related_var_dict = self.get_related_var(related_group['member'], self.window_size)        

        # print('var: {}, relate: {}'.format(name, related_var_dict))
        name_arr = [name]
        # print(related_var_dict)
        # print('union var: {}'.format(name))
        # 获取收集的向量和
        for node, cnt in related_var_dict.items():
            if node not in self.global_var_map.keys():
                continue
            cur_path_np += self.global_var_map[node].path
            name_arr.append(node)
        #     print(node, end=', ')
        # print('\n-------------------\n')
        
        # 记录收集的向量和
        self.union_variable_list.append(Variable(type=None, name="-".join(name_arr), path=cur_path_np))

        # 记录变量的邻接点
        if name not in self.global_var_map.keys():
            self.global_var_map[name] = Variable(type=None, name=name, window_size=self.window_size)
        # self.global_var_map[name].related_var = related_group['member']
        self.global_var_map[name].add_related_var(related_group['member'])

    def add_union_method(self, name, related_group):
        # 获取当前路径的信息
        cur_path_np = self.rearrange_path(self.cur_path)

        if related_group is None or 'member' not in related_group.keys():
            # 如果不存在关联变量，则只记录当前路径信息
            self.union_method_list.append(Method(name=name, path=cur_path_np))

            # print('method: {}, relate: {}'.format(name, None))
            return 
        related_var_dict = self.get_related_var(related_group['member'], self.window_size)        

        # print('method: {}, relate: {}'.format(name, related_var_dict))
        name_arr = [name]

        # 获取收集的向量和
        for node, cnt in related_var_dict.items():
            if node not in self.global_var_map.keys():
                continue
            cur_path_np += self.global_var_map[node].path
            name_arr.append(node)
        
        # 记录收集的向量和
        self.union_method_list.append(Method(name="-".join(name_arr), path=cur_path_np))
        
        
    def get_related_var(self, related_var_list, depth):
        if(depth == 0):
            return {}

        ret_var_map = {}
        for var in related_var_list:
            if var not in self.global_var_map.keys():
                continue

            if var not in ret_var_map:
                ret_var_map[var] = 1
            else:
                ret_var_map[var] += 1

            cur_var_list = self.global_var_map[var].get_related_var()
            # 获取候选列表的cnt
            next_var_map = self.get_related_var(cur_var_list, depth-1)
            for key, value in next_var_map.items():
                if key not in ret_var_map.keys():
                    ret_var_map[key] = value
                else:
                    ret_var_map[key] += value
                    
        return ret_var_map

    def record_token(self, name):
        # if self.debug is not None:
        #     if name != None and name != '':
        #         # print(name)
        #         print('({}, {})'.format((self.cur_path), name), end='\n')
        pass

    def log_node(self, name):
        # if self.debug is not None:
        #     if name is not None:
        #         print('\nnode: {}'.format(name))
        pass

    def push_node(self, node_name):
        # if node_name in node_to_index.keys():
        #     node_index = node_to_index[node_name]
        #     self.cur_path.append(node_index)
        node_name = self.transform_node(node_name)
        self.cur_path.append(node_name)

    def pop_node(self, node_name):
        # if node_name in node_to_index.keys():
        #     node_index = node_to_index[node_name]
        #     self.cur_path.pop()
        node_name = self.transform_node(node_name)
        if len(self.cur_path) == 0:
            return 
        self.cur_path.pop()
    
    def transform_node(self, origin_node):
        # return origin_node
        if origin_node == NodeType.DO_BODY:
            return NodeType.LOOP_BODY
        if origin_node == NodeType.FOR_BODY:
            return NodeType.LOOP_BODY
        if origin_node == NodeType.WHILE_BODY:
            return NodeType.LOOP_BODY
        if origin_node == NodeType.DO_CONDITION:
            return NodeType.LOOP_CONDITION
        if origin_node == NodeType.FOR_CONDITION:
            return NodeType.LOOP_CONDITION
        if origin_node == NodeType.WHILE_CONDITION:
            return NodeType.LOOP_CONDITION
        return origin_node

    
    def parse(self, obj, file_path, opt_file_path):
        if obj is None:
            return 

        self.file_path = file_path
        self.opt_file_path = opt_file_path

        if isinstance(obj, tree.CompilationUnit):
            return self.parse_tree_compilation_unit(obj) 
        elif isinstance(obj, tree.Declaration):
            return self.parse_tree_declaration(obj)
        elif isinstance(obj, tree.Statement):
            return self.parse_tree_statement(obj)
        elif isinstance(obj, tree.Expression):
            return self.parse_tree_expression(obj)

    # def parse_declaration(self, method):
    #     if isinstance(method, tree.MethodDeclaration):
    #         self.parse_method_declaration(method)
    #     elif isinstance(method, tree.Declaration):
    #         self.parse_block_statement(method)
    #     else:
    #         self.logger('debug', 'unknown declaration {}'.format(method))

    # def parse_member_declaration(self, body):
    #     return self.parse_tree_declaration(body)

    # def parse_method_declaration(self, method):
    #     if not isinstance(method, tree.MethodDeclaration):
    #         return None
    #     # self.cur_path.append(node_to_index['method_declaration'])
    #     self.push_node('method_declaration')

    #     if method.return_type is not None:
    #         self.parse_method_return_type(method.return_type)

    #     if method.body is not None:
    #         self.parse_block(method.body)

    #     self.pop_node('method_declaration')

    def parse_block(self, body):
        if body is None or type(body) != list:
            self.logger('error', 'error input for [parse block]: [{}]'.format(body), body)
            return 

        for body_item in body:
            self.parse_block_statement(body_item)

    def parse_block_statement(self, body):
        if isinstance(body, tree.LocalVariableDeclaration):
            self.parse_tree_local_variable_declaration(body)
        elif isinstance(body, tree.ClassDeclaration):
            self.parse_tree_class_declaration(body)
        elif isinstance(body, tree.EnumDeclaration):
            self.parse_tree_enum_declaration(body)
        elif isinstance(body, tree.InterfaceDeclaration):
            self.parse_tree_interface_declaration(body)
        elif isinstance(body, tree.AnnotationDeclaration):
            self.parse_tree_annotation_declaration(body)
        elif isinstance(body, tree.Statement):
            self.parse_tree_statement(body)
        else:
            self.logger('debug', 'unknown body type {}'.format(body))
            
    # def parse_statement(self, statement):
    #     if isinstance(statement, tree.TryStatement):
    #         self.parse_tree_try_statement(statement)
    #     elif isinstance(statement, tree.ReturnStatement):
    #         self.parse_tree_return_statement(statement)
    #     elif isinstance(statement, tree.BlockStatement):
    #         self.parse_tree_block_statement(statement)
    #     elif isinstance(statement, tree.IfStatement):
    #         self.parse_tree_if_statement(statement)
    #     elif isinstance(statement, tree.AssertStatement):
    #         self.parse_tree_assert_statement(statement)
    #     elif isinstance(statement, tree.Statement):
    #         pass    # 空语句
    #     elif isinstance(statement, tree.SwitchStatement):
    #         self.parse_tree_switch_statement(statement)
    #     elif isinstance(statement, tree.WhileStatement):
    #         self.parse_tree_while_statement(statement)
    #     elif isinstance(statement, tree.DoStatement):
    #         self.parse_tree_do_statement(statement)
    #     elif isinstance(statement, tree.ForStatement):
    #         self.parse_tree_for_statement(statement)
    #     elif isinstance(statement, tree.BreakStatement):
    #         self.parse_tree_break_statement(statement)
    #     elif isinstance(statement, tree.ContinueStatement):
    #         self.parse_tree_continue_statement(statement)
    #     elif isinstance(statement, tree.ReturnStatement):
    #         self.parse_tree_return_statement(statement)
    #     elif isinstance(statement, tree.ThrowStatement):
    #         self.parse_tree_throw_statement(statement)
    #     elif isinstance(statement, tree.SynchronizedStatement):
    #         self.parse_tree_synchronized_statement(statement)
    #     elif isinstance(statement, tree.StatementExpression):
    #         self.parse_tree_statement_expression(statement)
    #     else:
    #         self.logger('debug', 'unknown expression {}'.format(statement))

    # def parse_try_statement(self, try_statement):
    #     if hasattr(try_statement, 'block') and try_statement.block is not None:
    #         self.parse_block(try_statement.block)
    #     if hasattr(try_statement, 'resources') and try_statement.resources is not None:
    #         for resource in try_statement.resouces:
    #             self.parse_resource(resource)
    #     if hasattr(try_statement, 'catches') and try_statement.catches is not None:
    #         self.parse_catches(try_statement.catches)
    #     if hasattr(try_statement, 'finally_block') and try_statement.finally_block is not None:
    #         self.parse_block(try_statement.finally_block)
        # else:
        #     self.logger('debug', 'unknown try statement {}'.format(try_statement))

    # def parse_resource(self, resource):
    #     if not isinstance(resource, tree.TryResource):
    #         self.logger('debug', 'unknown resource {}'.format(resource))
    #     if hasattr(resource, 'type') and resource.type is not None:
    #         self.parse_type(resource.type)
    #     if hasattr(resource, 'name') and resource.name is not None:
    #         # self.parse_identifier(resource.name)
    #         return resource.name
    #     if hasattr(resource, 'value') and resource.value is not None:
    #         self.parse_expression(resource.value)

    # def parse_catches(self, catches_statement):
    #     for catch_clause in catches_statement:
    #         self.parse_catch_clause(catch_clause)

    # def parse_catch_clause(self, catch_clause):
    #     if hasattr(catch_clause, 'parameter') and catch_clause.parameter is not None:
    #         self.parse_catch_parameter(catch_clause.parameter)
    #     if hasattr(catch_clause, 'block') and catch_clause.block is not None:
    #         self.parse_block(catch_clause.block)

    # def parse_catch_parameter(self, catch_parameter):
    #     if hasattr(catch_parameter, 'types') and catch_parameter.types is not None:
    #         for type in catch_parameter.types:
    #             self.add_token(type, 'refer_type', self.cur_path)
    #     if hasattr(catch_parameter, 'name') and catch_parameter.name is not None:
    #         self.add_token(catch_parameter.name, 'variable', self.cur_path)
    
    def parse_expression(self, expression):
        if isinstance(expression, tree.Assignment):
            return self.parse_tree_assignment(expression)
        else:
            return self.parse_expressionl(expression)
        
    def parse_expressionl(self, expression):
        if isinstance(expression, tree.TernaryExpression):
            return self.parse_tree_ternary_expression(expression)
        elif isinstance(expression, tree.LambdaExpression):
            return self.parse_tree_lambda_expression(expression)
        elif isinstance(expression, tree.MethodReference):
            return self.parse_tree_method_reference(expression)
        else:
            return self.parse_expression_2(expression)

    def parse_expression_2(self, expression):
        if isinstance(expression, tree.BinaryOperation):
            return self.parse_tree_binary_operation(expression)
        else:
            return self.parse_expression_3(expression)            

    def parse_expression_3(self, expression):
        if isinstance(expression, tree.Cast):
            return self.pares_tree_cast(expression)
        elif isinstance(expression, tree.LambdaExpression):
            return self.parse_tree_lambda_expression(expression)
        else:
            return self.parse_primary(expression)

    def parse_primary(self, expression):
        if expression is None:
            return
        # self.parse_inner_primary(expression)

        if isinstance(expression, tree.Literal):
            self.add_global_identifier(expression.value)
            pass   # 常量值，或字符串类型
        elif isinstance(expression, tree.ExplicitConstructorInvocation):
            return self.parse_tree_explicit_constructor_invocation(expression)
        elif isinstance(expression, tree.This):
            self.add_global_identifier('this')
            self.parse_tree_this(expression)
            # pass    # 'this' word
        elif isinstance(expression, tree.SuperMethodInvocation):
            return self.parse_tree_super_method_invocation(expression)
        elif isinstance(expression, tree.SuperConstructorInvocation):
            return self.parse_tree_supter_constructor_invocation(expression)
        elif isinstance(expression, tree.SuperMemberReference):
            return self.parse_tree_super_member_reference(expression)
        elif isinstance(expression, tree.ArrayCreator):
            return self.parse_tree_array_creator(expression)
        elif isinstance(expression, tree.ClassCreator):
            return self.parse_tree_class_creator(expression)
        elif isinstance(expression, tree.MethodInvocation):
            return self.parse_tree_method_invocation(expression)
        elif isinstance(expression, tree.ClassReference):
            return self.parse_tree_class_reference(expression)
        elif isinstance(expression, tree.InnerClassCreator):
            return self.parse_tree_inner_class_creator(expression)
        elif isinstance(expression, tree.VoidClassReference):
            return self.parse_tree_void_class_reference(expression)
        elif isinstance(expression, tree.MemberReference):
            return self.parse_tree_member_reference(expression)
        elif isinstance(expression, tree.Statement):
            return self.parse_tree_statement(expression)

        elif isinstance(expression, tree.Expression):
            return self.parse_expression(expression)
        else:
            self.logger('debug', 'unknown primary {}'.format(expression))
            return None

    '''
    def parse_type(self, return_type):
        if isinstance(return_type, tree.BasicType):
            return self.parse_basic_type(return_type)
        elif isinstance(return_type, tree.ReferenceType):
            return self.parse_reference_type(return_type)
        else:
            self.logger('debug', 'can not parse method return type, ')
            return ''

    def parse_basic_type(self, basic_type):
        if hasattr(basic_type, 'name') and basic_type.name is not None:
            self.add_token(basic_type.name, 'basic_type', self.cur_path)
            return basic_type.name
        else:
            self.logger('info', 'can not parse basic type ')

    def parse_reference_type(self, refer_type):
        if hasattr(refer_type, 'name') and refer_type.name is not None:
            self.add_token(refer_type.name, 'refer_type', self.cur_path)
            return refer_type.name
        else:
            self.logger('info', 'can not parse reference type ')
            # return ''
    '''

    def parse_tree_compilation_unit(self, obj):
        if obj is None or not isinstance(obj, tree.CompilationUnit):
            self.logger('error', 'error input for [parse tree complilation unit]: {}'.format(obj), obj)
            return None
        self.log_node('[tree compilation unit]')

        self.parse_tree_package_declaration(obj.package)
        self.parse_tree_import(obj.package)
        if obj.types is not None:
            for decl in obj.types:
                self.parse_tree_declaration(decl)


    def parse_tree_import(self, obj):
        self.log_node('[tree import]')

    def parse_tree_documented(self, obj):
        self.log_node('[tree documented]')
        pass

    def parse_tree_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.Declaration):
            self.logger('error', 'error input for [tree declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree declaration]')

        self.add_global_modifier(self.unpack_modifier(self.parse_inner_modifiers(obj.modifiers)))
        
        if isinstance(obj, tree.TypeDeclaration):
            return self.parse_tree_type_declaration(obj)
        elif isinstance(obj, tree.PackageDeclaration):
            return self.parse_tree_package_declaration(obj)
        elif isinstance(obj, tree.MethodDeclaration):
            return self.parse_tree_method_declaration(obj)
        elif isinstance(obj, tree.FieldDeclaration):
            return self.parse_tree_field_declaration(obj)
        elif isinstance(obj, tree.ConstructorDeclaration):
            return self.parse_tree_constructor_declaration(obj)
        elif isinstance(obj, tree.ConstantDeclaration):
            return self.parse_tree_constant_declaration(obj)
        elif isinstance(obj, tree.VariableDeclaration):
            return self.parse_tree_variable_declaration(obj)
        elif isinstance(obj, tree.FormalParameter):
            return self.parse_tree_formal_parameter(obj)
        elif isinstance(obj, tree.TryResource):
            return self.parse_tree_try_resource(obj)
        elif isinstance(obj, tree.CatchClauseParameter):
            return self.parse_tree_catch_caluse_paramenter(obj)
        elif isinstance(obj, tree.EnumConstantDeclaration):
            return self.parse_tree_enum_constant_declaration(obj)
        elif isinstance(obj, tree.AnnotationMethod):
            return self.parse_tree_annotation_method(obj)
        else:
            self.logger('debug', 'unknown [parse tree declaration]: {}'.format(obj))
        # todo
        # if not isinstance(obj, tree.Declaration):
        #     return 
        # elif 
    def parse_tree_type_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.TypeDeclaration):
            self.logger('error', 'error input for [tree type declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree type declaration]')

        if isinstance(obj, tree.ClassDeclaration):
            return self.parse_tree_class_declaration(obj)
        elif isinstance(obj, tree.EnumDeclaration):
            return self.parse_tree_enum_declaration(obj)
        elif isinstance(obj, tree.InterfaceDeclaration):
            return self.parse_tree_interface_declaration(obj)
        elif isinstance(obj, tree.AnnotationDeclaration):
            return self.parse_tree_annotation_declaration(obj)
        else:
            self.logger('debug', 'unknown [parse tree type declaration]: {}'.format(obj))
            
    def parse_tree_package_declaration(self, obj):
        self.log_node('[tree package declaration]')
        pass

    def parse_tree_class_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.ClassDeclaration):
            self.logger('error', 'error input for [tree class declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree class declaration]')

        self.add_global_keyword('class')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        self.parse_inner_type_parameters(obj.type_parameters)

        self.add_global_type(self.unpack_type(self.parse_tree_type(obj.extends)), RoleType.REFERENCE_TYPE)
        if obj.implements is not None:
            for impl in obj.implements:
                self.add_global_type(self.unpack_type(self.parse_tree_type(impl)), RoleType.REFERENCE_TYPE)
        
        self.parse_inner_class_body(obj.body)
        
    def parse_tree_enum_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.EnumDeclaration):
            self.logger('error', 'error input for [tree enum declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree enum declaration]')

        self.add_global_keyword('enum')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        self.parse_inner_enum_body(obj.body)
        
    def parse_tree_interface_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.InterfaceDeclaration):
            self.logger('error', 'error input for [tree interface declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree interface declaration]')

        self.add_global_keyword('interface')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        self.parse_inner_type_parameters(obj.type_parameters)
        self.parse_inner_class_body(obj.body)
        
    def parse_tree_annotation_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.AnnotationDeclaration):
            self.logger('error', 'error input for [tree annotation declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree annotation declaration]')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        self.parse_inner_annotation_type_body(obj.body)

# ------------------------------------------------------------------------------
    def parse_tree_type(self, obj):
        if obj is None or not isinstance(obj, tree.Type):
            self.logger('error', 'error input for [tree type]: [{}]'.format(obj), obj)
            return 
        self.log_node('[tree type]')

        if isinstance(obj, tree.BasicType):
            return self.parse_tree_basic_type(obj)
        elif isinstance(obj, tree.ReferenceType):
            return self.parse_tree_reference_type(obj)
        else:
            self.logger('debug', 'unknown parse tree type: {}'.format(obj), obj)
            return None

    def parse_tree_basic_type(self, obj):
        if type(obj) != tree.BasicType:
            self.logger('error', 'error input for [tree basic type]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree basic type]')

        self.add_global_type(obj.name, RoleType.BASIC_TYPE)
        # self.record_token(obj.name)

        return {'type_name': obj.name, 'type': RoleType.BASIC_TYPE}
        
    def parse_tree_reference_type(self, obj):
        if type(obj) != tree.ReferenceType:
            self.logger('error', 'error input for [tree reference type]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree reference type]')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        # self.record_token(obj.name)

        self.parse_inner_nonwildcard_type_arguments(obj.arguments)

        return {'type_name': obj.name, 'type': RoleType.REFERENCE_TYPE}
    
    def parse_tree_type_argument(self, obj):
        if type(obj) != tree.TypeArgument:
            self.logger('error', 'error input for [tree type argument]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree type argument]')

        return self.parse_tree_type(obj.type)

# ------------------------------------------------------------------------------
    def parse_tree_type_parameter(self, obj):
        if obj is None or not isinstance(obj, tree.TypeParameter):
            self.logger('error', 'error input for [tree type parameter]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree type parameter]')

        if obj.name is None:
            return None

        extends_list = []
        if obj.extends is not None:
            for refer_type in obj.extends:
                extends_list.append(self.parse_tree_reference_type(refer_type))

        return {'type': [obj.name], 'extends': extends_list}

# ------------------------------------------------------------------------------
    def parse_tree_annnotation(self, obj):
        self.log_node('[tree annotation]')
        pass

    def parse_tree_element_value_pair(self, obj):
        self.log_node('[tree element value pair]')
        pass

    def parse_tree_element_array_value(self, obj):
        if obj is None or not isinstance(obj, tree.ElementArrayValue):
            self.logger('error', 'error input for [tree element array value]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree element array value]')

        if obj.values is not None:
            for value in obj.values:
                self.parse_element_value(value)
# ------------------------------------------------------------------------------
    def parse_tree_member(self, obj):
        self.log_node('[tree member]')
        pass

    def parse_tree_method_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.MethodDeclaration):
            self.logger('error', 'error input for [parse tree method declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree method declaration]')

        # 当method depth =0 时，记录method的起止行，并初始化, 因为method可能存在嵌套情况
        if self.method_depth == 0:
            self.clear()

            if obj.position is not None:
                self.method_start = obj.position[0]
            if obj.end_position is not None:
                self.method_end = obj.end_position[0]

            self.push_node(NodeType.METHOD_DECLARATION)

        self.method_depth += 1

        self.parse_inner_type_parameters(obj.type_parameters)
        self.add_global_method(obj.name)
        self.parse_tree_type(obj.return_type)

        params_dict = self.parse_inner_formal_parameters(obj.parameters)
        self.parse_block(obj.body)

        self.pop_node(NodeType.METHOD_DECLARATION)

        self.method_depth -= 1
        # print('opt file')
        # print(self.dump())

        if self.method_depth == 0:
            with open(self.opt_file_path, 'a+') as fileOut:
                fileOut.write(self.dump())
            self.clear()
        
    def parse_tree_field_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.FieldDeclaration):
            self.logger('error', 'error input for [tree field declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree field declaration]')

        if isinstance(obj, tree.ConstantDeclaration):
            return self.parse_tree_constant_declaration(obj)
        # else:
        #     self.logger('debug', 'unknown [parse tree field declaration]: {}'.format(obj))
        self.parse_tree_type(obj.type)

        if obj.declarators is not None:
            for decl in obj.declarators:
                self.parse_tree_variable_declarator(decl)

            
    def parse_tree_constructor_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.ConstructorDeclaration):
            self.logger('error', 'error input for [parse tree constructor declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree constructor declaration]')

        if self.method_depth == 0:
            self.clear()
            if obj.position is not None:
                self.method_start = obj.position[0]
            if obj.end_position is not None:
                self.method_end = obj.end_position[0]
        self.method_depth += 1
        
        self.push_node(NodeType.METHOD_DECLARATION)

        self.parse_inner_type_parameters(obj.type_parameters)
        self.add_global_method(obj.name)
        self.parse_inner_formal_parameters(obj.parameters)
        self.parse_block(obj.body)

        self.pop_node(NodeType.METHOD_DECLARATION)

        self.method_depth -= 1

        # print('opt file')
        # print(self.dump())
        if self.method_depth == 0:
            with open(self.opt_file_path, 'a+') as fileOut:
                fileOut.write(self.dump())
            self.clear()

# ------------------------------------------------------------------------------
    def parse_tree_constant_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.ConstantDeclaration):
            self.logger('error', 'error input for [tree constant declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree constant declaration]')

        type_dict = self.parse_tree_type(obj.type)
        self.add_global_type(self.unpack_type(type_dict), RoleType.REFERENCE_TYPE)

        if obj.declarators is not None:
            for decl in obj.declarators:
                self.parse_tree_variable_declarator(decl)
    
    def parse_tree_array_initializer(self, obj):
        if obj is None or not isinstance(obj, tree.ArrayInitializer):
            self.logger('error', 'error input for [tree array initializer]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree array initializer]')

        # 此处出现嵌套行为，需要注意一下
        init_list = list()
        if obj.initializers is not None:
            for initializer in obj.initializers:
                if initializer == None:
                    continue
                cur_init = self.parse_inner_variable_initializer(initializer)            
                init_list.append(cur_init)

        return merge_dict(init_list)

    # 涉及到变量命名-->数据依赖
    def parse_tree_variable_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.VariableDeclaration):
            self.logger('error', 'error input for [tree variable declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree variable declaration]')

        if isinstance(obj, tree.LocalVariableDeclaration):
            return self.parse_tree_local_variable_declaration(obj)
        # else:
            # self.logger('debug', 'unknown [parse tree varaible declaration]: {}'.format(obj))
        type_dict = self.parse_tree_type(obj.type)
        var_type = None
        if type_dict is not None:
            var_type = type_dict['type']

        declarators = obj.declarators
        if declarators is not None:
            for decl in declarators:
                # 涉及到数据依赖关系
                decla_dict = self.parse_tree_variable_declarator(decl)
                self.add_global_variable(decla_dict['var_name'], var_type)
        

    def parse_tree_local_variable_declaration(self, obj):
        if obj is None or type(obj) != tree.LocalVariableDeclaration:
            self.logger('error', 'error input for [tree local variable declaration]: [{}]'.format(obj), obj)
            return
        self.log_node('[tree local variable declaration]')

        # 忽略modifiers, annotations
        self.push_node(NodeType.LOCAL_VARIABLE_DECLARATION)
        var_type_dict = self.parse_tree_type(obj.type)
        if var_type_dict is not None:
            var_type = var_type_dict['type_name']

        for declarator in obj.declarators:
            declar_dict = self.parse_tree_variable_declarator(declarator)
            if declar_dict is None:
                continue

            # todo: 需要输出初始化列表中的变量名，及初始化列表

            # 将变量添加到全局表中
            self.add_global_variable(name=declar_dict['var_name'], type=var_type)
            # self.global_var_map[declar_dict['var_name']] = Variable(type=var_type, name=declar_dict['var_name'])

        self.pop_node(NodeType.LOCAL_VARIABLE_DECLARATION)

    def parse_tree_variable_declarator(self, obj):
        if obj is None or type(obj) != tree.VariableDeclarator:
            self.logger('error', 'error input for [tree variable declarator]: [{}]'.format(obj), obj)
            return 
        self.log_node('[tree variable declarator]')

        # assign action
        
        # self.add_global_variable(obj.name)
        var_name = obj.name
        initializer = obj.initializer
        init_dict = None
        if initializer != None:
            init_dict = self.parse_inner_variable_initializer(initializer)

        # 收集窗口内的值
        self.add_union_variable(var_name, init_dict)

        return {'var_name': var_name, 'init': init_dict, 'member': [var_name]}

    # assign 右操作数：
    # 1. 初始化操作：发生在{}中
    # 2. 赋值操作，表达式形式触发
    def parse_inner_variable_initializer(self, initializer):
        if isinstance(initializer, tree.ArrayInitializer):
            # 返回值为多维列表的嵌套
            return self.parse_tree_array_initializer(initializer)
        elif isinstance(initializer, tree.Expression):
            # 返回值为列表
            return self.parse_tree_expression(initializer)
        else:
            self.logger('debug', 'unknown [parse tree variable declarator]->[initializer]: {}'.format(initializer))
        
        
    def parse_tree_formal_parameter(self, obj):
        if obj is None or not isinstance(obj, tree.FormalParameter):
            self.logger('error', 'error input for [tree formal parameter]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree formal parameter]')

        var_type = self.parse_tree_type(obj.type)
        var_name = obj.name

        self.add_global_variable(var_name, self.unpack_type(var_type))
        self.add_union_variable(var_name)
        
        return merge_dict({'member': [var_name]}, var_type)

    def parse_tree_inferred_formal_parameter(self, obj):
        if obj is None or not isinstance(obj, tree.InferredFormalParameter):
            self.logger('error', 'error input for [inferred formal parameter]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree inferred formal parameter]')

        self.add_global_variable(obj.name)
        self.add_union_variable(obj.name)

        return {'member': [obj.name]}

# ------------------------------------------------------------------------------
    def parse_tree_statement(self, obj):
        if obj is None or not isinstance(obj, tree.Statement):
            self.logger('error', 'error input for [parse tree statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree statement]')

        if isinstance(obj, tree.IfStatement):
            return self.parse_tree_if_statement(obj)
        elif isinstance(obj, tree.WhileStatement):
            return self.parse_tree_while_statement(obj)
        elif isinstance(obj, tree.DoStatement):
            return self.parse_tree_do_statement(obj)
        elif isinstance(obj, tree.ForStatement):
            return self.parse_tree_for_statement(obj)
        elif isinstance(obj, tree.AssertStatement):
            return self.parse_tree_assert_statement(obj)
        elif isinstance(obj, tree.BreakStatement):
            return self.parse_tree_break_statement(obj)
        elif isinstance(obj, tree.ContinueStatement):
            return self.parse_tree_continue_statement(obj)
        elif isinstance(obj, tree.ReturnStatement):
            return self.parse_tree_return_statement(obj)
        elif isinstance(obj, tree.ThrowStatement):
            return self.parse_tree_throw_statement(obj)
        elif isinstance(obj, tree.SynchronizedStatement):
            return self.parse_tree_synchronized_statement(obj)
        elif isinstance(obj, tree.TryStatement):
            return self.parse_tree_try_statement(obj)
        elif isinstance(obj, tree.SwitchStatement):
            return self.parse_tree_switch_statement(obj)
        elif isinstance(obj, tree.BlockStatement):
            return self.parse_tree_block_statement(obj)
        elif isinstance(obj, tree.StatementExpression):
            return self.parse_tree_statement_expression(obj)
        elif isinstance(obj, tree.CatchClause):
            return self.parse_tree_catch_clause(obj)
        elif type(obj) == tree.Statement:
            pass    # 空表达式
        else:
            self.logger('debug', 'unknown [parse tree statement]: {}'.format(obj), obj)
        
    def parse_tree_if_statement(self, obj):
        if obj is None or not isinstance(obj, tree.IfStatement):
            self.logger('error', 'error input for [tree if statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree if statement]')

        self.add_global_keyword('if')

        self.push_node(NodeType.IF_CONDITION)
        self.parse_expression(obj.condition)
        self.pop_node(NodeType.IF_CONDITION)

        self.push_node(NodeType.ELSE_BODY)
        self.parse_expression(obj.then_statement)
        self.pop_node(NodeType.ELSE_BODY)

        self.parse_expression(obj.else_statement)

        
    def parse_tree_while_statement(self, obj):
        if obj is None or not isinstance(obj, tree.WhileStatement):
            self.logger('error', 'error input for [tree while statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree while statement]')
        
        self.add_global_keyword('loop')

        self.push_node(NodeType.WHILE_CONDITION)        
        self.parse_expression(obj.condition)
        self.pop_node(NodeType.WHILE_CONDITION)

        self.push_node(NodeType.WHILE_BODY)
        self.parse_tree_statement(obj.body)
        self.pop_node(NodeType.WHILE_BODY)


    def parse_tree_do_statement(self, obj):
        if obj is None or not isinstance(obj, tree.DoStatement):
            self.logger('error', 'error input for [tree do statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree do statement]')

        self.add_global_keyword('loop')

        self.push_node(NodeType.DO_BODY)
        self.parse_tree_statement(obj.body)
        self.pop_node(NodeType.DO_BODY)

        self.push_node(NodeType.DO_CONDITION)
        self.parse_expression(obj.condition)
        self.pop_node(NodeType.DO_CONDITION)
        
        
    def parse_tree_for_statement(self, obj):
        if obj is None or not isinstance(obj, tree.ForStatement):
            self.logger('error', 'error input for [tree for statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree for statement]')

        self.add_global_keyword('loop')

        for_control = obj.control
        if for_control is not None:
            if isinstance(for_control, tree.ForControl):
                self.parse_tree_for_control(for_control)
            elif isinstance(for_control, tree.EnhancedForControl):
                self.parse_tree_enhanced_for_control(for_control)
        
        self.push_node(NodeType.FOR_BODY)
        self.parse_tree_statement(obj.body)
        self.pop_node(NodeType.FOR_BODY)
        

    def parse_tree_assert_statement(self, obj):
        if obj is None or not isinstance(obj, tree.AssertStatement):
            self.logger('error', 'error input for [tree assert statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree assert statement]')

        self.add_global_keyword('assert')

        self.push_node(NodeType.ASSERT_CONDITION)        
        self.parse_expression(obj.condition)
        self.pop_node(NodeType.ASSERT_CONDITION)

        self.push_node(NodeType.ASSERT_BODY)
        self.parse_expression(obj.value)
        self.pop_node(NodeType.ASSERT_BODY)

                
    def parse_tree_break_statement(self, obj):
        self.log_node('[tree break statement]')

        self.add_global_keyword('break')

        pass
    
    def parse_tree_continue_statement(self, obj):
        self.log_node('[tree continue statement]')

        self.add_global_keyword('continue')

        pass

    def parse_tree_return_statement(self, obj):
        if obj is None or not isinstance(obj, tree.ReturnStatement):
            self.logger('error', 'error input for [tree return statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree return statement]')

        self.add_global_keyword('return')

        self.push_node(NodeType.RETURN)
        self.parse_expression(obj.expression)
        self.pop_node(NodeType.RETURN)
        
        
    def parse_tree_throw_statement(self, obj):
        if obj is None or not isinstance(obj, tree.ThrowStatement):
            self.logger('error', 'error input for [tree throw statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree throw statement]')

        self.add_global_keyword('throw')

        self.push_node(NodeType.THROW)
        self.parse_expression(obj.expression)
        self.pop_node(NodeType.THROW)

        
    def parse_tree_synchronized_statement(self, obj):
        if obj is None or not isinstance(obj, tree.SynchronizedStatement):
            self.logger('error', 'error input for [tree synchronized statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree synchronized statement]')

        self.add_global_keyword('synchronized')

        self.push_node(NodeType.SYNCHRONIZED_CONDITION)
        self.parse_expression(obj.lock)
        self.pop_node(NodeType.SYNCHRONIZED_CONDITION)

        self.push_node(NodeType.SYNCHRONIZED_BODY)
        self.parse_block(obj.block)
        self.pop_node(NodeType.SYNCHRONIZED_BODY)
        
        
    def parse_tree_try_statement(self, obj):
        if obj is None or not isinstance(obj, tree.TryStatement):
            self.logger('error', 'error input for [tree try statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree try statement]')

        self.add_global_keyword('try')

        resources = obj.resources
        if resources is not None:
            for resource in resources:
                self.parse_tree_try_resource(resource)
            
        self.push_node(NodeType.TRY_BODY)
        self.parse_block(obj.block)
        self.pop_node(NodeType.TRY_BODY)

        self.push_node(NodeType.CATCH_BODY)
        catches = obj.catches
        if catches is not None:
            for catch in catches:
                self.parse_tree_catch_clause(catch)
        self.pop_node(NodeType.CATCH_BODY)

        self.push_node(NodeType.FINALLY_BODY)
        self.parse_block(obj.finally_block)
        self.pop_node(NodeType.FINALLY_BODY)
        
    def parse_tree_switch_statement(self, obj):
        if obj is None or not isinstance(obj, tree.SwitchStatement):
            self.logger('error', 'error input for [tree switch statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree switch statement]')

        self.add_global_keyword('switch')

        self.push_node(NodeType.SWITCH_CONDITION)
        self.parse_expression(obj.expression)
        self.pop_node(NodeType.SWITCH_CONDITION)

        self.parse_inner_switch_block_groups(obj.cases)
        
    def parse_tree_block_statement(self, obj):
        if obj is None or not isinstance(obj, tree.BlockStatement):
            self.logger('error', 'error input for [tree block statement]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree block statement]')

        return self.parse_block(obj.statements)

    def parse_tree_statement_expression(self, obj):
        if obj is None or not isinstance(obj, tree.StatementExpression):
            self.logger('error', 'error input for [tree statement expression]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree statement expression]')

        self.parse_expression(obj.expression)
    
# ------------------------------------------------------------------------------
    def parse_tree_try_resource(self, obj):
        if obj is None or not isinstance(obj, tree.TryResource):
            self.logger('error', 'error input for [tree try resource]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree try resource]')

        type_dict = self.parse_tree_reference_type(obj.type)
        var_type = self.unpack_type(type_dict)

        # assign action
        # todo 存在赋值操作

        self.add_global_variable(obj.name, var_type)

        expre_dict = self.parse_expression(obj.value)

        # obj.name 与 expre_dict之间存在赋值操作
        self.add_union_variable(obj.name, expre_dict)

        
    def parse_tree_catch_clause(self, obj):
        if obj is None or not isinstance(obj, tree.CatchClause):
            self.logger('error', 'error input for [tree catch clause]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree catch clause]')

        self.add_global_keyword('catch')

        self.parse_tree_catch_caluse_paramenter(obj.parameter)

        # self.push_node(NodeType.CATCH_BODY)
        self.parse_block(obj.block)
        # self.pop_node(NodeType.CATCH_BODY)
        

    def parse_tree_catch_caluse_paramenter(self, obj):
        if obj is None or not isinstance(obj, tree.CatchClauseParameter):
            self.logger('error', 'error input for [tree catch clause parameter]: [{}]'.format(obj), obj)
            return None
        self.log_node('[catch clause parameter]')
        
        types = obj.types
        last_type = None
        if types is not None:
            for type in types:
                self.add_global_type(type, RoleType.REFERENCE_TYPE)
                last_type = type

        self.add_global_variable(obj.name, last_type)
        self.add_union_variable(obj.name)
       
# ------------------------------------------------------------------------------
    def parse_tree_switch_statement_case(self, obj):
        if obj is None or not isinstance(obj, tree.SwitchStatementCase):
            self.logger('error', 'error input for [tree switch statement case]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree switch statement case]')


        self.add_global_keyword('case')

        self.push_node(NodeType.CASE_LABEL)
        if obj.case is not None:
            if isinstance(obj.case, tree.Expression):
                self.parse_expression(obj.case)
            else:
                self.add_global_identifier(obj.case)

        self.pop_node(NodeType.CASE_LABEL)

        self.push_node(NodeType.CASE_BODY)
        if obj.statements is not None:
            for statement in obj.statements:
                self.parse_block_statement(statement)
        self.pop_node(NodeType.CASE_BODY)

        
    def parse_tree_for_control(self, obj):
        if obj is None or not isinstance(obj, tree.ForControl):
            self.logger('error', 'error input for [tree for control]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree for control]')

        # init
        init = obj.init
        if init is not None:
            if isinstance(init, tree.VariableDeclaration):
                self.parse_tree_variable_declaration(init)
            elif type(init)==list:
                for expre in init:
                    self.parse_expression(expre)
        
        # condition
        condition = obj.condition
        self.push_node(NodeType.FOR_CONDITION)
        self.parse_expression(condition)
        self.pop_node(NodeType.FOR_CONDITION)
        
        # update
        self.push_node(NodeType.FOR_BODY)
        update = obj.update
        if update is not None:
            for expre in update:
                self.parse_expression(expre)
        self.pop_node(NodeType.FOR_BODY)
        
        
    def parse_tree_enhanced_for_control(self, obj):
        if obj is None or not isinstance(obj, tree.EnhancedForControl):
            self.logger('error', 'error input for [tree enhanced for control]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree enhanced for control]')
        
        self.push_node(NodeType.FOR_CONDITION)
        self.parse_tree_variable_declaration(obj.var)
        self.pop_node(NodeType.FOR_CONDITION)

        self.push_node(NodeType.FOR_BODY)
        self.parse_expression(obj.iterable)
        self.pop_node(NodeType.FOR_BODY)

    
# ------------------------------------------------------------------------------
    def parse_tree_expression(self, obj):
        return self.parse_expression(obj)
        # if type(obj)==tree.Assignment:
        #     return self.parse_tree_assignment(obj)
        # elif type(obj)==tree.TernaryExpression:
        #     return self.parse_tree_ternary_expression(obj)
        # elif type(obj)==tree.BinaryOperation:
        #     return self.parse_tree_binary_operation(obj)
        # elif type(obj)==tree.Cast:
        #     return self.pares_tree_cast(obj)
        # elif type(obj)==tree.MethodReference:
        #     return self.parse_tree_method_reference(obj)
        # elif type(obj)==tree.LambdaExpression:
        #     return self.parse_tree_lambda_expression(obj)
        # elif type(obj)==tree.Primary:
        #     return self.parse_primary(obj)
        # elif type(obj)==tree.ArraySelector:
        #     return self.parse_tree_array_selector(obj)
        # else:
        #     self.logger('debug', 'unknown [parse tree expression]: {}'.format(obj))

    # 存在数据依赖情况
    # 赋值操作
    def parse_tree_assignment(self, obj):
        if obj is None or type(obj) != tree.Assignment:
            self.logger('error', 'error input for [tree assignment]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree assignment]')

        # assign action
        self.push_node(NodeType.EXPRE_ASSIGN)
        expressionl = self.parse_inner_expressionl(obj.expressionl)
        value = self.parse_tree_expression(obj.value)
        self.pop_node(NodeType.EXPRE_ASSIGN)

        # print('expre left: {}'.format(expressionl))
        # print('expre right: {}'.format(value))
        # exit(0)
        if expressionl is not None and type(expressionl)==dict \
            and 'member' in expressionl.keys() and value is not None and 'member' in value.keys():
            for member in expressionl['member']:
                self.add_union_variable(member, value)
        
        return {'left': expressionl, 'right': value, 
                'member': transfor_to_array(expressionl, value)}


    # 条件表达式
    # parse_exressionl:1776        
    def parse_tree_ternary_expression(self, obj):
        if obj is None or type(obj) != tree.TernaryExpression:
            self.logger('error', 'error input for [tree ternary expression]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree ternary expression]')

        self.push_node(NodeType.EXPRE_TERNARY)
        condition = self.parse_expression_2(obj.condition)
        if_true = self.parse_expression(obj.if_true)
        if_false = self.parse_expressionl(obj.if_false)
        self.pop_node(NodeType.EXPRE_TERNARY)

        return {'condition': condition, 'value': transfor_to_array(if_true, if_false), 
                'member': transfor_to_array(condition, if_true, if_false)}
    
        
    def parse_tree_binary_operation(self, obj):
        if obj is None or type(obj) != tree.BinaryOperation:
            self.logger('error', 'error input for [tree binary operation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree binary operation]')

        self.push_node(NodeType.EXPRE_BINARY)
        oper_left = self.parse_expression_2(obj.operandl)
        oper_right = None
        if isinstance(obj.operandr, tree.Type):
            self.parse_tree_type(obj.operandr)
        else:
            oper_right = self.parse_expression_2(obj.operandr)
        self.pop_node(NodeType.EXPRE_BINARY)

        member_arr = transfor_to_array(oper_left, oper_right)
        oper_type = parse_oper_node_type(obj.operator)
        self.push_node(oper_type)
        self.add_union_relationship(member_arr)
        self.pop_node(oper_type)

        # print('member: {}, oper: {}'.format(member_arr, oper_type))

        return {'member': transfor_to_array(oper_left, oper_right)}
        
    # ‘把’表达式：用于强制类型转换
    # 返回表达式的值 (包含变量等)
    def pares_tree_cast(self, obj):
        if obj is None or type(obj) != tree.Cast:
            self.logger('error', 'error input for [tree cast]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree cast]')

        cast_type = self.parse_tree_type(obj.type)
        return self.parse_expression_3(obj.expression) 

    # method reference 不返回值
    # 因为没有变量
    def parse_tree_method_reference(self, obj):
        if obj is None or type(obj) != tree.MethodReference:
            self.logger('error', 'error input for [tree method reference]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree method reference]')

        field = self.parse_expression_2(obj.expression)
        self.add_global_field(field)


        method = obj.method
        if method is not None:
            if isinstance(method, tree.MemberReference):
                # new 选项
                self.parse_tree_member_reference(obj.method)
            elif isinstance(method, tree.Expression):
                # 表达式, 可能存在赋值等操作
                return self.parse_expression(method)
            else:
                self.logger('debug', 'unknown [parse tree method reference]-->[obj.method]: [{}]'.format(method), method)

        self.parse_inner_nonwildcard_type_arguments(obj.type_arguments)

        
    
    # lambda 表达式不设置返回值
    # 无法从返回值中分析数据依赖行为，所以不设置返回值
    def parse_tree_lambda_expression(self, obj):
        if obj is None or type(obj) != tree.LambdaExpression:
            self.logger('error', 'error input for [lambda expression]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree lambda expression]')

        self.add_global_keyword('lambda')

        self.push_node(NodeType.EXPRE_LAMBDA)
        parameters = obj.parameters
        if parameters is not None:
            for param in parameters:
                if type(param) == tree.InferredFormalParameter:
                    self.parse_tree_inferred_formal_parameter(param)
                elif type(param) == tree.FormalParameter:
                    self.parse_tree_formal_parameter(param)
                else:
                    self.parse_expression_2(param)
        
        self.parse_inner_lambda_method_body(obj.body)

        self.pop_node(NodeType.EXPRE_LAMBDA)
    
    
# ------------------------------------------------------------------------------
    def parse_tree_primary(self, obj):
        pass
    def parse_tree_literal(self, obj):
        pass
    def parse_tree_this(self, obj):
        if obj is None or not isinstance(obj, tree.This):
            self.logger('error', 'error input for [tree this]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree this]')
        return self.parse_inner_primary(obj)
            
    def parse_tree_member_reference(self, obj):
        if obj is None or type(obj) != tree.MemberReference:
            self.logger('error', 'error input for [tree member reference]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree member reference]')

        member = obj.member

        selector = self.parse_inner_primary(obj)
        if selector is not None and 'selector' in selector.keys():
            self.push_node(NodeType.ARRAY_SELECTOR)
        
        # 如果存在qualifier，则可能是qualifier.member(及a.b)的形式，需要将member设置为qulifier，将旧的member当成method token对待，作为static token
        if selector is not None and 'qualifier' in selector.keys():
            self.add_global_method(obj.member)
            member = ''.join(selector['qualifier'])

        self.add_global_variable(member)

        if selector is not None and 'member' in selector:
            self.add_union_variable(member, selector)
        # self.record_token('var: {}'.format(obj.member))

        if selector is not None and 'selector' in selector.keys():
            self.pop_node(NodeType.ARRAY_SELECTOR)


        return {'member': [member] }

    def parse_tree_invocation(self, obj):
        if obj is None or not isinstance(obj, tree.Invocation):
            self.logger('error', 'error input for [tree invocation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree invocation]')

        if isinstance(obj, tree.ExplicitConstructorInvocation):
            return self.parse_tree_explicit_constructor_invocation(obj)
        elif isinstance(obj, tree.SuperConstructorInvocation):
            return self.parse_tree_supter_constructor_invocation(obj)
        elif isinstance(obj, tree.MethodInvocation):
            return self.parse_tree_method_invocation(obj)
        elif isinstance(obj, tree.SuperMethodInvocation):
            return self.parse_tree_super_method_invocation(obj)

    def parse_tree_explicit_constructor_invocation(self, obj):
        if obj is None or type(obj) != tree.ExplicitConstructorInvocation:
            self.logger('error', 'error input for [tree explicit constructor invocation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree explicit constructor invocation]')

        self.push_node(NodeType.INVOCATION_CONSTRUCTOR)

        self.parse_inner_primary(obj)

        # type_arguments应该是无返回值的
        type_arg_list = self.parse_inner_nonwildcard_type_arguments(obj.type_arguments)

        arg_list = self.parse_inner_arguments(obj.arguments)
        arg_dict = merge_dict(arg_list)

        self.pop_node(NodeType.INVOCATION_CONSTRUCTOR)

        self.add_union_method('this', arg_dict)

        return arg_dict
     
    def parse_tree_supter_constructor_invocation(self, obj):
        if obj is None or type(obj) != tree.SuperConstructorInvocation:
            self.logger('error', 'error input for [tree super constructor invocation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree super constructor invocation]')

        self.push_node(NodeType.INVOCATION_CONSTRUCTOR)

        self.parse_inner_primary(obj)
        self.parse_inner_nonwildcard_type_arguments(obj.type_arguments) 

        exp_list = self.parse_inner_arguments(obj.arguments)
        arg_dict = merge_dict(exp_list)

        self.pop_node(NodeType.INVOCATION_CONSTRUCTOR)

        self.add_union_method('super', arg_dict)

        return arg_dict
        
    def parse_tree_method_invocation(self, obj):
        if obj is None or type(obj) != tree.MethodInvocation:
            self.logger('error', 'error input for [tree method invocation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree method invocation]')

        self.push_node(NodeType.INVOCATION_METHOD)
        primary = self.parse_inner_primary(obj)
        
        self.parse_inner_nonwildcard_type_arguments(obj.type_arguments)

        self.add_global_method(obj.member)

        arg_list = self.parse_inner_arguments(obj.arguments)
        arg_dict_l = merge_dict(arg_list)

        # 函数调用时，如果主对象与参数存在调用行为，则添加绑定
        if(arg_dict_l != None and 'member' in arg_dict_l.keys()):
            self.add_union_variable(self.unpack_member(primary), arg_dict_l)

        arg_dict = merge_dict(arg_list, primary)

        self.pop_node(NodeType.INVOCATION_METHOD)

        # 记录method的窗口收集数据
        self.add_union_method(obj.member, arg_dict)

        
        return arg_dict
        
    def parse_tree_super_method_invocation(self, obj):
        if obj is None or type(obj) != tree.SuperMethodInvocation:
            self.logger('error', 'error input for [tree super method invocation]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree supter method invocation]')

        self.push_node(NodeType.INVOCATION_METHOD)
        self.parse_inner_primary(obj)

        self.parse_inner_nonwildcard_type_arguments(obj.type_arguments) 

        self.add_global_method(obj.member)

        self.parse_inner_nonwildcard_type_arguments(obj.type_arguments)

        arg_list = self.parse_inner_arguments(obj.arguments)
        arg_dict = merge_dict(arg_list)
        # if obj.arguments is not None:
        #     for expression in obj.arguments:
        #         cur_dict = self.parse_expression(expression)
        #         member_dict = merge_dict(member_dict, cur_dict)
        
        self.pop_node(NodeType.INVOCATION_METHOD)

        # 加入method属性
        arg_dict['method'] = [obj.member]

        # 记录method的窗口收集数据
        self.add_union_method(obj.member, arg_dict)

        return arg_dict
        
    def parse_tree_super_member_reference(self, obj):
        if obj is None or type(obj) != tree.SuperMemberReference:
            self.logger('error', 'error input for [tree super member reference]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree super member reference]')

        selector = self.parse_inner_primary(obj)
        if selector is not None and 'selector' in selector.keys():
            self.push_node(NodeType.ARRAY_SELECTOR)

        self.add_global_variable(name=obj.member)
        self.add_union_variable(obj.member, selector)

        if selector is not None and 'selector' in selector.keys():
            self.pop_node(NodeType.ARRAY_SELECTOR)


        # self.parse_inner_nonwildcard_type_arguments(obj.type_arguments) 

        return {'member': [ obj.member ]}
        
    def parse_tree_array_selector(self, obj):
        if obj is None or type(obj) != tree.ArraySelector:
            self.logger('error', 'error input for [tree array selector]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree array selector]')

        self.push_node(NodeType.ARRAY_SELECTOR)
        expre_dict = self.parse_expression(obj.index)
        self.pop_node(NodeType.ARRAY_SELECTOR)
        if expre_dict is not None:
            expre_dict['selector'] = 'array'
        else:
            expre_dict = {'selector': 'array'}

        return expre_dict

    def parse_tree_class_reference(self, obj):
        if obj is None or not isinstance(obj, tree.ClassReference):
            self.logger('error', 'error input for [tree class reference]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree class reference]')

        refer = self.parse_tree_type(obj.type)
        self.parse_inner_primary(obj)

        return refer

    def parse_tree_void_class_reference(self, obj):
        if obj is None or not isinstance(obj, tree.VoidClassReference):
            self.logger('error', 'error input for [tree void class reference]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree void class reference]')
            
        self.parse_inner_primary(obj)
    
# ------------------------------------------------------------------------------
    def parse_tree_creator(self, obj):
        if obj is None or not isinstance(obj, tree.Creator):
            self.logger('error', 'error input for [tree creator]: [{}]'.format(obj), obj)
            return None
        if isinstance(obj, tree.ArrayCreator):
            return self.parse_tree_array_creator(obj)
        elif isinstance(obj, tree.ClassCreator):
            return self.parse_tree_class_creator(obj)
        elif isinstance(obj, tree.InnerClassCreator):
            return self.parse_tree_inner_class_creator(obj)
        else:
            self.logger('debug', 'unknown [tree creator]: [{}]'.format(obj))

    def parse_tree_array_creator(self, obj):
        if obj is None or type(obj) != tree.ArrayCreator:
            self.logger('error', 'error input for [tree array creator]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree array creator]')

        self.push_node(NodeType.CREATOR_ARRAY)
        self.add_global_type(obj.type, role=RoleType.REFERENCE_TYPE)

        dim_list = []
        if obj.dimensions is not None:
            for dim in obj.dimensions:
                if dim is None:
                    continue
                dim_list.append(self.parse_expression(dim))                
        dim_dict = merge_dict(dim_list)
        initializer = self.parse_tree_array_initializer(obj.initializer)

        self.parse_inner_primary(obj)

        self.pop_node(NodeType.CREATOR_ARRAY)
        return merge_dict(dim_dict, initializer)

        
    def parse_tree_class_creator(self, obj):
        if obj is None or type(obj) != tree.ClassCreator:
            self.logger('error', 'error input for [tree class creator]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree class creator]')

        self.add_global_keyword('new')

        self.push_node(NodeType.CREATOR_CLASS)
        self.parse_inner_nonwildcard_type_arguments(obj.constructor_type_arguments)
        type_dict=self.parse_tree_reference_type(obj.type)
        # self.add_global_type(self.unpack_type(type_dict), role=RoleType.REFERENCE_TYPE)

        arg_list = self.parse_inner_arguments(obj.arguments)
        self.parse_inner_class_body(obj.body)
        self.pop_node(NodeType.CREATOR_CLASS)
        
        return merge_dict(arg_list)
        
        
    def parse_tree_inner_class_creator(self, obj):
        if obj is None or type(obj) != tree.InnerClassCreator:
            self.logger('error', 'error input for [tree inner class creator]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree inner class creator]')
        
        self.push_node(NodeType.CREATOR_CLASS) 
        self.parse_tree_reference_type(obj.type)
        arg_list = self.parse_inner_arguments(obj.arguments)
        self.parse_inner_class_body(obj.body)
        self.pop_node(NodeType.CREATOR_CLASS)

        return merge_dict(arg_list)


    def parse_tree_enum_body(self, obj):
        if obj is None or not isinstance(obj, tree.EnumBody):
            self.logger('error', 'error input for [tree enum body]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree enum body]')

        enum_constants = obj.constants
        if enum_constants is not None:
            for constant in enum_constants:
                self.parse_tree_enum_constant_declaration(constant)
        
        self.parse_inner_class_body(obj.declarations)


    def parse_tree_enum_constant_declaration(self, obj):
        if obj is None or not isinstance(obj, tree.EnumConstantDeclaration):
            self.logger('error', 'error input for [tree enum constant declaration]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree enum constant declaration]')

        self.add_global_type(obj.name, RoleType.REFERENCE_TYPE)
        self.parse_inner_arguments(obj.arguments)
        self.parse_inner_class_body(obj.body)
        
    def parse_tree_annotation_method(self, obj):
        if obj is None or not isinstance(obj, tree.AnnotationMethod):
            self.logger('error', 'error input for [tree annotation method]: [{}]'.format(obj), obj)
            return None
        self.log_node('[tree annotation method')

        self.add_global_type(obj.return_type, RoleType.REFERENCE_TYPE)
        self.add_global_method(obj.name)

        self.parse_element_value(obj.default)


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

    def parse_inner_expressionl(self, obj):
        return self.parse_expressionl(obj)

    def parse_inner_lambda_method_body(self, obj):
        if obj is None:
            return 

        if isinstance(obj, tree.Expression):
            return self.parse_tree_expression(obj)
        else:
            return self.parse_block(obj)

    # type arguments 是一些自定义类型，无返回的必要
    def parse_inner_nonwildcard_type_arguments(self, obj):
        if obj is None or type(obj) != list:
            return list()
        
        arg_list = list()
        for argument in obj:
            arg_list.append(self.parse_tree_type_argument(argument))
        # return arg_list

    def parse_inner_arguments(self, obj):
        if obj is None or type(obj) != list:
            return []

        exp_list = list()
        for expression in obj:
            exp_list.append(self.parse_expression(expression))
        return exp_list
    
    def parse_inner_class_body(self, obj):
        if obj is None or type(obj) != list:
            return 
        for declar in obj:
            if isinstance(declar, tree.Declaration):
                self.parse_tree_declaration(declar)
            else:
                self.parse_block(declar)
    
    # 解析primary中的qualifier, 及selector
    def parse_inner_primary(self, obj):
        if obj is None or not isinstance(obj, tree.Primary):
            return 

        self.add_global_qualifier(obj.qualifier)

        # return merge_dict(self.parse_inner_selectors(obj.selectors), {"member": [obj.qualifier]})
        return merge_dict(self.parse_inner_selectors(obj.selectors), {"qualifier": [obj.qualifier]})

    def parse_inner_selectors(self, obj):
        if obj is None:
            return 
        
        selector_list = []
        for selector in obj:
            if selector is None:
                continue
            elif isinstance(selector, tree.ArraySelector):
                selector_list.append(self.parse_tree_array_selector(selector))
            elif isinstance(selector, tree.Invocation):
                selector_list.append(self.parse_tree_invocation(selector))
            elif isinstance(selector, tree.InnerClassCreator):
                selector_list.append( self.parse_tree_inner_class_creator(selector))
            elif isinstance(selector, tree.SuperMemberReference):
                selector_list.append( self.parse_tree_super_member_reference(selector))

        return merge_dict(selector_list)
    
    def parse_inner_formal_parameters(self, obj):
        param_list = []
        if obj is None or type(obj)!=list:
            return None
        for params in obj:
            param_list.append(self.parse_tree_formal_parameter(params))

        return merge_dict(param_list)
        
    def parse_inner_type_parameters(self, obj):
        if obj is None or type(obj) != list:
            return None
        param_list = []
        for type_param in obj:
            param = self.parse_tree_type_parameter(type_param)
            param_list.append(param)
        
        return merge_dict(param_list)
    
    def parse_inner_enum_body(self, obj):
        return self.parse_tree_enum_body(obj)

    def parse_inner_annotation_type_body(self, obj):
        if obj is None or type(obj) != list:
            return None
        for element in obj:
            if isinstance(element, tree.Declaration):
                self.parse_tree_declaration(element)
            else:
                self.logger('debug', 'unknown [parse inner annotation type body]->[for element in body]: {}'.format(element))

    def parse_inner_switch_block_groups(self, obj):
        if obj is None or type(obj) != list:
            return None
        for switch_case in obj:
            self.parse_tree_switch_statement_case(switch_case)
                
    def parse_inner_modifiers(self, obj):
        if obj is None or (type(obj)!=set and type(obj)!=list):
            return None
        modifier_list = []
        for modifier in obj:
            modifier_list.append(modifier)

        return {'modifier': modifier_list}
            
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

    def parse_element_value(self, obj):
        if obj is None:
            return None
        if isinstance(obj, tree.Annotation):
            return self.parse_tree_annnotation(obj)
        elif isinstance(obj, tree.ElementArrayValue):
            return self.parse_tree_element_array_value(obj)
        elif type(obj) == list:
            return None
        else:
            return self.parse_expressionl(obj)

    def unpack_type(self, obj):
        if obj is None:
            return None
        return obj['type_name']
    def unpack_modifier(self, obj):
        if obj is None:
            return None
        return obj['modifier']
    def unpack_member(self, obj):
        if(obj is None or 'member' not in obj.keys()): 
            return None
        return "-".join(obj['member'])
