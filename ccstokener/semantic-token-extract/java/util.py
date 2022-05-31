
from enum import IntEnum

from numpy import empty


class NodeType(IntEnum):
    LOCAL_VARIABLE_DECLARATION= 1
    METHOD_DECLARATION = 2

    IF_CONDITION= 3
    ELSE_BODY= 4

    ASSERT_CONDITION= 5
    ASSERT_BODY= 6

    SWITCH_CONDITION= 7
    SWITCH_BODY= 8
    CASE_LABEL= 9
    CASE_BODY= 10

    WHILE_CONDITION= 11
    WHILE_BODY= 12

    DO_BODY= 13
    DO_CONDITION= 14

    FOR_CONDITION= 15
    FOR_BODY= 16

    RETURN= 17
    THROW= 18
    SYNCHRONIZED_CONDITION= 19
    SYNCHRONIZED_BODY= 20

    TRY_BODY= 21
    CATCH_BODY= 22
    FINALLY_BODY= 23
    
    EXPRE_ASSIGN = 24
    EXPRE_TERNARY = 25
    EXPRE_BINARY = 26
    EXPRE_LAMBDA = 27
    INVOCATION_METHOD = 28                  # 普通方法调用
    INVOCATION_CONSTRUCTOR = 29             # 构造方法调用
    CREATOR_CLASS = 30                  # 类构造
    CREATOR_ARRAY = 31                  # 数组构造

    LOOP_BODY = 32
    LOOP_CONDITION = 33

    ARRAY_SELECTOR = 34             # 通过数组获取数值

    EXPRE_BINARY_LOGIC = 35         # 逻辑、关系表达式：如>, <, ==, !=
    EXPRE_BINARY_MATHMATIC = 36     # 算术、移位、位逻辑表达式：如*, /, >>, &
    EXPRE_BINARY_CONDITION = 37     # 状态表达式：如&&、||

    NODE_TYPE_END = 38
    

class RoleType(IntEnum):
    BASIC_TYPE = 1
    REFERENCE_TYPE= 2
    VARIABLE= 3
    FILED= 4
    METHOD= 5
    QUALIFIER= 6
    EXPRE_RELATION = 7
    ROLE_TYPE_END = 8

def transfor_to_array(*args):
    ret = []
    for value in args:
        if type(value)==list:
            ret.extend(value)
        elif value==None:
            continue
        elif type(value)==dict:
            if ('member') in value.keys() and value['member'] is not None:
                ret.extend(value['member'])
        else:
            ret.append(value)

    return ret

def merge_dict(*args):
    ret = dict()
    for cur in args:
        if cur is None:
            continue
        elif type(cur)==list:
            for val in cur:
                ret = merge_dict(ret, val)

        if type(cur)!=dict:
            continue
        
        for k, v in cur.items():
            if type(v) != list:
                v = [v]
            tmp = []
            for t in v:
                if t is None or (type(t)==str and len(t)==0):
                    continue
                tmp.append(t)

            if len(tmp) == 0:
                continue
            
            if k in ret.keys() and type(ret[k])==list:
                ret[k].extend(v)
            else:
                ret[k] = v
    return ret

def parse_oper_node_type(oper_name):
    if oper_name in ['>', '<', '>=', '<=', 'instanceof', '==', '!=']:
        return NodeType.EXPRE_BINARY_LOGIC
    if oper_name in ['/', '*', '%', '+', '-', '&', '^', '|', '>>', '<<', '>>>']:
        return NodeType.EXPRE_BINARY_MATHMATIC
    if oper_name in ['&&', '||']:
        return NodeType.EXPRE_BINARY_CONDITION
    return None
