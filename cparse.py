# -----------------------------------------------------------------------------
# cparse.py
#
# Simple parser for ANSI C.  Based on the grammar in K&R, 2nd Ed.
# -----------------------------------------------------------------------------

import sys
import exceptions
import clex
import ply.yacc as yacc
import translator
import struct
import pdb

class UnhandledSyntaxError(Exception): pass
class ParseError(Exception): pass

# Get the token map
tokens = clex.tokens

# Set start point
start = 'compound_statement'

# translation-unit:

def p_translation_unit_1(t):
    'translation_unit : external_declaration'
    raise UnhandledSyntaxError

def p_translation_unit_2(t):
    'translation_unit : translation_unit external_declaration'
    raise UnhandledSyntaxError

# external-declaration:

def p_external_declaration_1(t):
    'external_declaration : function_definition'
    raise UnhandledSyntaxError

def p_external_declaration_2(t):
    'external_declaration : declaration'
    raise UnhandledSyntaxError

# function-definition:

def p_function_definition_1(t):
    'function_definition : declaration_specifiers declarator declaration_list compound_statement'
    raise UnhandledSyntaxError

def p_function_definition_2(t):
    'function_definition : declarator declaration_list compound_statement'
    raise UnhandledSyntaxError

def p_function_definition_3(t):
    'function_definition : declarator compound_statement'
    raise UnhandledSyntaxError

def p_function_definition_4(t):
    'function_definition : declaration_specifiers declarator compound_statement'
    raise UnhandledSyntaxError

# declaration:

def p_declaration_1(t):
    'declaration : declaration_specifiers init_declarator_list SEMI'
    if isinstance(t[1], translator.Type):
        for d in t[2]:
            if isinstance(d, translator.VariableDeclarator):
                item = d.variable
                if item.type == None:
                    item.type = t[1]
                elif isinstance(item.type, translator.PointerType):
                    if item.type.baseType == None:
                        item.type.baseType = t[1]
                    else:
                        raise UnhandledSyntaxError
                else:
                    raise UnhandledSyntaxError
            else:
                raise UnhandledSyntaxError
        t[0] = translator.Declaration(t[2])
    else:
        raise UnhandledSyntaxError

def p_declaration_2(t):
    'declaration : declaration_specifiers SEMI'
    if isinstance(t[1], translator.Type):
        declarator = translator.TypeDeclarator(t[1])
        t[0] = translator.Declaration([declarator])
    else:
        raise UnhandledSyntaxError

# declaration-list:

def p_declaration_list_1(t):
    'declaration_list : declaration'
    t[0] = [ t[1] ]

def p_declaration_list_2(t):
    'declaration_list : declaration_list declaration '
    t[0] = t[1] + t[2]

# declaration-specifiers
def p_declaration_specifiers_1(t):
    'declaration_specifiers : storage_class_specifier declaration_specifiers'
    raise UnhandledSyntaxError

def p_declaration_specifiers_2(t):
    'declaration_specifiers : type_specifier declaration_specifiers'
    raise UnhandledSyntaxError

def p_declaration_specifiers_3(t):
    'declaration_specifiers : type_qualifier declaration_specifiers'
    raise UnhandledSyntaxError

def p_declaration_specifiers_4(t):
    'declaration_specifiers : storage_class_specifier'
    raise UnhandledSyntaxError

def p_declaration_specifiers_5(t):
    'declaration_specifiers : type_specifier'
    t[0] = t[1]

def p_declaration_specifiers_6(t):
    'declaration_specifiers : type_qualifier'
    raise UnhandledSyntaxError

# storage-class-specifier
def p_storage_class_specifier(t):
    '''storage_class_specifier : AUTO
                               | REGISTER
                               | STATIC
                               | EXTERN
                               | TYPEDEF
                               '''
    raise UnhandledSyntaxError

# type-specifier:
def p_type_specifier_1(t):
    'type_specifier : VOID'
    t[0] = translator.VoidType()

def p_type_specifier_2(t):
    '''type_specifier : CHAR
                      | SIGNED CHAR'''
    t[0] = translator.IntType(isSigned=True, size=struct.calcsize("c")*8)

def p_type_specifier_3(t):
    '''type_specifier : SHORT
                      | SIGNED SHORT'''
    t[0] = translator.IntType(isSigned=True, size=struct.calcsize("h")*8)

def p_type_specifier_4(t):
    '''type_specifier : INT
                      | SIGNED INT
                      '''
    t[0] = translator.IntType()

def p_type_specifier_5(t):
    '''type_specifier : LONG
                      | SIGNED LONG
                      '''
    t[0] = translator.IntType(isSigned=True, size=struct.calcsize("l")*8)

def p_type_specifier_6(t):
    '''type_specifier : UNSIGNED CHAR'''
    t[0] = translator.IntType(isSigned=False, size=struct.calcsize("b")*8)

def p_type_specifier_7(t):
    '''type_specifier : UNSIGNED SHORT'''
    t[0] = translator.IntType(isSigned=False, size=struct.calcsize("H")*8)

def p_type_specifier_8(t):
    '''type_specifier : UNSIGNED INT'''
    t[0] = translator.IntType(isSigned=False)

def p_type_specifier_9(t):
    '''type_specifier : UNSIGNED LONG'''
    t[0] = translator.IntType(isSigned=False, size=struct.calcsize("L")*8)

def p_type_specifier_10(t):
    'type_specifier : SIGNED'
    t[0] = translator.IntType(isSigned=True)

def p_type_specifier_11(t):
    'type_specifier : UNSIGNED'
    t[0] = translator.IntType(isSigned=False)

def p_type_specifier_12(t):
    'type_specifier : FLOAT'
    t[0] = translator.FloatType()

def p_type_specifier_13(t):
    'type_specifier : DOUBLE'
    t[0] = translator.DoubleType()

def p_type_specifier_14(t):
    '''type_specifier : struct_or_union_specifier
                      | enum_specifier
                      '''
    t[0] = t[1]

def p_type_specifier_15(t):
    'type_specifier : TYPEID'
    t[0] = translator.TypeIDType(t[1])

# type-qualifier:
def p_type_qualifier(t):
    '''type_qualifier : CONST
                      | VOLATILE'''
    raise UnhandledSyntaxError

# struct-or-union-specifier

def p_struct_or_union_specifier_1(t):
    '''struct_or_union_specifier : struct_or_union ID LBRACE struct_declaration_list RBRACE
                                 | struct_or_union TYPEID LBRACE struct_declaration_list RBRACE'''
    t[0] = t[1]
    t[0].name = t[2]
    t[0].definition = t[4]
    translator.tempTypeIDTable.add(t[2], t[0])

def p_struct_or_union_specifier_2(t):
    'struct_or_union_specifier : struct_or_union LBRACE struct_declaration_list RBRACE'
    t[0] = t[1]
    t[0].definition = t[3]

def p_struct_or_union_specifier_3(t):
    '''struct_or_union_specifier : struct_or_union ID
                                 | struct_or_union TYPEID'''
    t[0] = t[1]
    t[0].name = t[2]

# struct-or-union:
def p_struct_or_union_1(t):
    'struct_or_union : STRUCT'
    t[0] = translator.StructType()

def p_struct_or_union_2(t):
    'struct_or_union : UNION'
    t[0] = translator.UnionType()
# struct-declaration-list:

def p_struct_declaration_list_1(t):
    'struct_declaration_list : struct_declaration'
    t[0] = [ t[1] ]

def p_struct_declaration_list_2(t):
    'struct_declaration_list : struct_declaration_list struct_declaration'
    t[0] = t[1] + [ t[2] ]

# init-declarator-list:

def p_init_declarator_list_1(t):
    'init_declarator_list : init_declarator'
    t[0] = [ t[1] ]

def p_init_declarator_list_2(t):
    'init_declarator_list : init_declarator_list COMMA init_declarator'
    t[0] = t[1] + [ t[3] ]

# init-declarator

def p_init_declarator_1(t):
    'init_declarator : declarator'
    t[0] = t[1]

def p_init_declarator_2(t):
    'init_declarator : declarator EQUALS initializer'
    if isinstance(t[1], translator.VariableDeclarator):
        t[0] = t[1]
        t[0].initializer = t[3]
    else:
        raise UnhandledSyntaxError

# struct-declaration:

def p_struct_declaration(t):
    'struct_declaration : specifier_qualifier_list struct_declarator_list SEMI'
    if isinstance(t[1], translator.Type):
        t[0] = t[2]
        for item in t[0]:
            if item.variable.type == None:
                item.variable.type = t[1]
            elif isinstance(item.variable.type, translator.PointerType):
                if item.variable.type.baseType == None:
                    item.variable.type.baseType = t[1]
                else:
                    raise UnhandledSyntaxError
            else:
                raise UnhandledSyntaxError
    else:
        raise UnhandledSyntaxError

# specifier-qualifier-list:

def p_specifier_qualifier_list_1(t):
    'specifier_qualifier_list : type_specifier specifier_qualifier_list'
    raise UnhandledSyntaxError

def p_specifier_qualifier_list_2(t):
    'specifier_qualifier_list : type_specifier'
    t[0] = t[1]

def p_specifier_qualifier_list_3(t):
    'specifier_qualifier_list : type_qualifier specifier_qualifier_list'
    raise UnhandledSyntaxError

def p_specifier_qualifier_list_4(t):
    'specifier_qualifier_list : type_qualifier'
    raise UnhandledSyntaxError

# struct-declarator-list:

def p_struct_declarator_list_1(t):
    'struct_declarator_list : struct_declarator'
    t[0] = [ t[1] ]

def p_struct_declarator_list_2(t):
    'struct_declarator_list : struct_declarator_list COMMA struct_declarator'
    t[0] = t[1] + [ t[3] ]

# struct-declarator:

def p_struct_declarator_1(t):
    'struct_declarator : declarator'
    t[0] = t[1]

def p_struct_declarator_2(t):
    'struct_declarator : declarator COLON constant_expression'
    raise UnhandledSyntaxError

def p_struct_declarator_3(t):
    'struct_declarator : COLON constant_expression'
    raise UnhandledSyntaxError

# enum-specifier:

def p_enum_specifier_1(t):
    'enum_specifier : ENUM ID LBRACE enumerator_list RBRACE'
    raise UnhandledSyntaxError

def p_enum_specifier_2(t):
    'enum_specifier : ENUM LBRACE enumerator_list RBRACE'
    raise UnhandledSyntaxError

def p_enum_specifier_3(t):
    'enum_specifier : ENUM ID'
    raise UnhandledSyntaxError

# enumerator_list:
def p_enumerator_list_1(t):
    'enumerator_list : enumerator'
    raise UnhandledSyntaxError

def p_enumerator_list_2(t):
    'enumerator_list : enumerator_list COMMA enumerator'
    raise UnhandledSyntaxError

# enumerator:
def p_enumerator_1(t):
    'enumerator : ID'
    raise UnhandledSyntaxError

def p_enumerator_2(t):
    'enumerator : ID EQUALS constant_expression'
    raise UnhandledSyntaxError

# declarator:

def p_declarator_1(t):
    'declarator : pointer direct_declarator'
    assert isinstance(t[1], translator.PointerType)
    if isinstance(t[2], translator.VariableDeclarator):
        t[0] = t[2]
        t[0].variable.type = t[1]
    else:
        raise UnhandledSyntaxError

def p_declarator_2(t):
    'declarator : direct_declarator'
    t[0] = t[1]

# direct-declarator:

def p_direct_declarator_1(t):
    'direct_declarator : ID'
    t[0] = translator.VariableDeclarator()
    t[0].variable = translator.Variable(t[1])

def p_direct_declarator_2(t):
    'direct_declarator : LPAREN declarator RPAREN'
    t[0] = t[1]

def p_direct_declarator_3(t):
    'direct_declarator : direct_declarator LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError

def p_direct_declarator_4(t):
    'direct_declarator : direct_declarator LPAREN parameter_type_list RPAREN '
    raise UnhandledSyntaxError

def p_direct_declarator_5(t):
    'direct_declarator : direct_declarator LPAREN identifier_list RPAREN '
    raise UnhandledSyntaxError

def p_direct_declarator_6(t):
    'direct_declarator : direct_declarator LPAREN RPAREN '
    raise UnhandledSyntaxError

# pointer:
def p_pointer_1(t):
    'pointer : TIMES type_qualifier_list'
    t[0] = translator.PointerType(level=1)

def p_pointer_2(t):
    'pointer : TIMES'
    t[0] = translator.PointerType(level=1)

def p_pointer_3(t):
    'pointer : TIMES type_qualifier_list pointer'
    t[0] = t[3]
    t[0].level += 1

def p_pointer_4(t):
    'pointer : TIMES pointer'
    t[0] = t[2]
    t[0].level += 1

# type-qualifier-list:

def p_type_qualifier_list_1(t):
    'type_qualifier_list : type_qualifier'
    raise UnhandledSyntaxError

def p_type_qualifier_list_2(t):
    'type_qualifier_list : type_qualifier_list type_qualifier'
    raise UnhandledSyntaxError

# parameter-type-list:

def p_parameter_type_list_1(t):
    'parameter_type_list : parameter_list'
    raise UnhandledSyntaxError

def p_parameter_type_list_2(t):
    'parameter_type_list : parameter_list COMMA ELLIPSIS'
    raise UnhandledSyntaxError

# parameter-list:

def p_parameter_list_1(t):
    'parameter_list : parameter_declaration'
    raise UnhandledSyntaxError

def p_parameter_list_2(t):
    'parameter_list : parameter_list COMMA parameter_declaration'
    raise UnhandledSyntaxError

# parameter-declaration:
def p_parameter_declaration_1(t):
    'parameter_declaration : declaration_specifiers declarator'
    raise UnhandledSyntaxError

def p_parameter_declaration_2(t):
    'parameter_declaration : declaration_specifiers abstract_declarator_opt'
    raise UnhandledSyntaxError

# identifier-list:
def p_identifier_list_1(t):
    'identifier_list : ID'
    raise UnhandledSyntaxError

def p_identifier_list_2(t):
    'identifier_list : identifier_list COMMA ID'
    raise UnhandledSyntaxError

# initializer:

def p_initializer_1(t):
    'initializer : assignment_expression'
    t[0] = t[1]

def p_initializer_2(t):
    '''initializer : LBRACE initializer_list RBRACE
                   | LBRACE initializer_list COMMA RBRACE'''
    t[0] = t[2]

# initializer-list:

def p_initializer_list_1(t):
    'initializer_list : initializer'
    t[0] = [ t[1] ]

def p_initializer_list_2(t):
    'initializer_list : initializer_list COMMA initializer'
    t[0] = t[1] + [ t[3] ]

# type-name:

def p_type_name(t):
    'type_name : specifier_qualifier_list abstract_declarator_opt'
    if isinstance(t[1], translator.Type):
        if t[2] == None:
            t[0] = t[1]
        elif isinstance(t[2], translator.PointerType):
            assert t[2].baseType == None
            t[0] = t[2]
            t[0].baseType = t[1]
        else:
            raise UnhandledSyntaxError
    else:
        raise UnhandledSyntaxError

def p_abstract_declarator_opt_1(t):
    'abstract_declarator_opt : empty'
    t[0] = t[1]

def p_abstract_declarator_opt_2(t):
    'abstract_declarator_opt : abstract_declarator'
    t[0] = t[1]

# abstract-declarator:

def p_abstract_declarator_1(t):
    'abstract_declarator : pointer '
    t[0] = t[1]

def p_abstract_declarator_2(t):
    'abstract_declarator : pointer direct_abstract_declarator'
    raise UnhandledSyntaxError

def p_abstract_declarator_3(t):
    'abstract_declarator : direct_abstract_declarator'
    raise UnhandledSyntaxError

# direct-abstract-declarator:

def p_direct_abstract_declarator_1(t):
    'direct_abstract_declarator : LPAREN abstract_declarator RPAREN'
    raise UnhandledSyntaxError

def p_direct_abstract_declarator_2(t):
    'direct_abstract_declarator : direct_abstract_declarator LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError

def p_direct_abstract_declarator_3(t):
    'direct_abstract_declarator : LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError

def p_direct_abstract_declarator_4(t):
    'direct_abstract_declarator : direct_abstract_declarator LPAREN parameter_type_list_opt RPAREN'
    raise UnhandledSyntaxError

def p_direct_abstract_declarator_5(t):
    'direct_abstract_declarator : LPAREN parameter_type_list_opt RPAREN'
    raise UnhandledSyntaxError

# Optional fields in abstract declarators

def p_constant_expression_opt_1(t):
    'constant_expression_opt : empty'
    t[0] = t[1]

def p_constant_expression_opt_2(t):
    'constant_expression_opt : constant_expression'
    raise UnhandledSyntaxError

def p_parameter_type_list_opt_1(t):
    'parameter_type_list_opt : empty'
    t[0] = t[1]

def p_parameter_type_list_opt_2(t):
    'parameter_type_list_opt : parameter_type_list'
    raise UnhandledSyntaxError

# statement:

def p_statement(t):
    '''
    statement : labeled_statement
              | expression_statement
              | compound_statement
              | selection_statement
              | iteration_statement
              | jump_statement
              '''
    t[0] = t[1]

# labeled-statement:

def p_labeled_statement_1(t):
    'labeled_statement : ID COLON statement'
    raise UnhandledSyntaxError

def p_labeled_statement_2(t):
    'labeled_statement : CASE constant_expression COLON statement'
    t[0] = translator.CaseStatement(case=t[2], caseBody=t[4])

def p_labeled_statement_3(t):
    'labeled_statement : DEFAULT COLON statement'
    t[0] = translator.DefaultStatement(body=t[3])

# expression-statement:
def p_expression_statement(t):
    'expression_statement : expression_opt SEMI'
    t[0] = translator.ExpressionStatement(t[1])

# compound-statement:

def p_compound_statement_1(t):
    'compound_statement : LBRACE block_item_list RBRACE'
    t[0] = translator.CompoundStatement(t[2])

def p_compound_statement_2(t):
    'compound_statement : LBRACE RBRACE'
    t[0] = translator.CompoundStatement()

def p_block_item_list_1(t):
    'block_item_list : block_item'
    t[0] = [ t[1] ]

def p_block_item_list_2(t):
    'block_item_list : block_item_list block_item'
    t[0] = t[1] + [ t[2] ]

def p_block_item(t):
    '''block_item : statement
                  | declaration'''
    t[0] = t[1]

# statement-list:

def p_statement_list_1(t):
    'statement_list : statement'
    t[0] = [ t[1] ]

def p_statement_list_2(t):
    'statement_list : statement_list statement'
    t[0] = t[1] + [ t[2] ]

# selection-statement

def p_selection_statement_1(t):
    'selection_statement : IF LPAREN expression RPAREN statement'
    t[0] = translator.IfStatement(condition=t[3], truePart=t[5])

def p_selection_statement_2(t):
    'selection_statement : IF LPAREN expression RPAREN statement ELSE statement '
    t[0] = translator.IfStatement(condition=t[3], truePart=t[5], falsePart=t[7])

def p_selection_statement_3(t):
    'selection_statement : SWITCH LPAREN expression RPAREN statement '
    t[0] = translator.SwitchStatement(t[3], t[5])

# iteration_statement:

def p_iteration_statement_1(t):
    'iteration_statement : WHILE LPAREN expression RPAREN statement'
    t[0] = translator.WhileStatement(t[3], t[5])

def p_iteration_statement_2(t):
    'iteration_statement : FOR LPAREN expression_opt SEMI expression_opt SEMI expression_opt RPAREN statement '
    t[0] = translator.ForStatement(preLoopPart=t[3], condition=t[5], postLoopBodyPart=t[7], loopBodyPart=t[9])

def p_iteration_statement_3(t):
    'iteration_statement : FOR LPAREN declaration expression_opt SEMI expression_opt RPAREN statement '
    t[0] = translator.ForStatement(preLoopPart=t[3], condition=t[4], postLoopBodyPart=t[6], loopBodyPart=t[8])

def p_iteration_statement_4(t):
    'iteration_statement : DO statement WHILE LPAREN expression RPAREN SEMI'
    t[0] = translator.DoWhileStatement(t[5], t[2])

# jump_statement:

def p_jump_statement_1(t):
    'jump_statement : GOTO ID SEMI'
    raise UnhandledSyntaxError

def p_jump_statement_2(t):
    'jump_statement : CONTINUE SEMI'
    t[0] = translator.ContinueStatement()

def p_jump_statement_3(t):
    'jump_statement : BREAK SEMI'
    t[0] = translator.BreakStatement()

def p_jump_statement_4(t):
    'jump_statement : RETURN expression_opt SEMI'
    raise UnhandledSyntaxError

def p_expression_opt_1(t):
    'expression_opt : empty'
    t[0] = t[1]

def p_expression_opt_2(t):
    'expression_opt : expression'
    t[0] = t[1]

# expression:
def p_expression_1(t):
    'expression : assignment_expression'
    t[0] = t[1]

def p_expression_2(t):
    'expression : expression COMMA assignment_expression'
    if isinstance(t[1], translator.CommaExpression):
        t[0] = t[1].append(t[3])
    else:
        t[0] = translator.CommaExpression([t[1], t[3]])

# assigment_expression:
def p_assignment_expression_1(t):
    'assignment_expression : conditional_expression'
    t[0] = t[1]

def p_assignment_expression_2(t):
    'assignment_expression : unary_expression assignment_operator assignment_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# assignment_operator:
def p_assignment_operator(t):
    '''
    assignment_operator : EQUALS
                        | TIMESEQUAL
                        | DIVEQUAL
                        | MODEQUAL
                        | PLUSEQUAL
                        | MINUSEQUAL
                        | LSHIFTEQUAL
                        | RSHIFTEQUAL
                        | ANDEQUAL
                        | OREQUAL
                        | XOREQUAL
                        '''
    t[0] = t[1]

# conditional-expression
def p_conditional_expression_1(t):
    'conditional_expression : logical_or_expression'
    t[0] = t[1]

def p_conditional_expression_2(t):
    'conditional_expression : logical_or_expression CONDOP expression COLON conditional_expression '
    t[0] = translator.ConditionalExpression(t[1], t[3], t[5])

# constant-expression

def p_constant_expression(t):
    'constant_expression : conditional_expression'
    t[0] = t[1]

# logical-or-expression

def p_logical_or_expression_1(t):
    'logical_or_expression : logical_and_expression'
    t[0] = t[1]

def p_logical_or_expression_2(t):
    'logical_or_expression : logical_or_expression LOR logical_and_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# logical-and-expression

def p_logical_and_expression_1(t):
    'logical_and_expression : inclusive_or_expression'
    t[0] = t[1]

def p_logical_and_expression_2(t):
    'logical_and_expression : logical_and_expression LAND inclusive_or_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# inclusive-or-expression:

def p_inclusive_or_expression_1(t):
    'inclusive_or_expression : exclusive_or_expression'
    t[0] = t[1]

def p_inclusive_or_expression_2(t):
    'inclusive_or_expression : inclusive_or_expression OR exclusive_or_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# exclusive-or-expression:

def p_exclusive_or_expression_1(t):
    'exclusive_or_expression :  and_expression'
    t[0] = t[1]

def p_exclusive_or_expression_2(t):
    'exclusive_or_expression :  exclusive_or_expression XOR and_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# AND-expression

def p_and_expression_1(t):
    'and_expression : equality_expression'
    t[0] = t[1]

def p_and_expression_2(t):
    'and_expression : and_expression AND equality_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])


# equality-expression:
def p_equality_expression_1(t):
    'equality_expression : relational_expression'
    t[0] = t[1]

def p_equality_expression_2(t):
    'equality_expression : equality_expression EQ relational_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_equality_expression_3(t):
    'equality_expression : equality_expression NE relational_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])


# relational-expression:
def p_relational_expression_1(t):
    'relational_expression : shift_expression'
    t[0] = t[1]

def p_relational_expression_2(t):
    'relational_expression : relational_expression LT shift_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_relational_expression_3(t):
    'relational_expression : relational_expression GT shift_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_relational_expression_4(t):
    'relational_expression : relational_expression LE shift_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_relational_expression_5(t):
    'relational_expression : relational_expression GE shift_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# shift-expression

def p_shift_expression_1(t):
    'shift_expression : additive_expression'
    t[0] = t[1]

def p_shift_expression_2(t):
    'shift_expression : shift_expression LSHIFT additive_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_shift_expression_3(t):
    'shift_expression : shift_expression RSHIFT additive_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# additive-expression

def p_additive_expression_1(t):
    'additive_expression : multiplicative_expression'
    t[0] = t[1]

def p_additive_expression_2(t):
    'additive_expression : additive_expression PLUS multiplicative_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_additive_expression_3(t):
    'additive_expression : additive_expression MINUS multiplicative_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# multiplicative-expression

def p_multiplicative_expression_1(t):
    'multiplicative_expression : cast_expression'
    t[0] = t[1]

def p_multiplicative_expression_2(t):
    'multiplicative_expression : multiplicative_expression TIMES cast_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_multiplicative_expression_3(t):
    'multiplicative_expression : multiplicative_expression DIVIDE cast_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

def p_multiplicative_expression_4(t):
    'multiplicative_expression : multiplicative_expression MOD cast_expression'
    t[0] = translator.BinaryOperandExpression(t[1], t[2], t[3])

# cast-expression:

def p_cast_expression_1(t):
    'cast_expression : unary_expression'
    t[0] = t[1]

def p_cast_expression_2(t):
    'cast_expression : LPAREN type_name RPAREN cast_expression'
    if isinstance(t[2], translator.Type):
        t[0] = translator.CastExpression(t[2], t[4])
    else:
        raise UnhandledSyntaxError

def p_cast_expression_3(t):
    'cast_expression :  type_specifier LPAREN cast_expression RPAREN'
    if isinstance(t[1], translator.Type):
        t[0] = translator.CastExpression(t[1], t[3])
    else:
        raise UnhandledSyntaxError

# unary-expression:
def p_unary_expression_1(t):
    'unary_expression : postfix_expression'
    t[0] = t[1]

def p_unary_expression_2(t):
    'unary_expression : PLUSPLUS unary_expression'
    t[0] = translator.UnaryOperandExpression(operand=t[2], operator=t[1], isPrefix=True)

def p_unary_expression_3(t):
    'unary_expression : MINUSMINUS unary_expression'
    t[0] = translator.UnaryOperandExpression(operand=t[2], operator=t[1], isPrefix=True)

def p_unary_expression_4(t):
    'unary_expression : unary_operator cast_expression'
    t[0] = translator.UnaryOperandExpression(operand=t[2], operator=t[1], isPrefix=True)

def p_unary_expression_5(t):
    'unary_expression : SIZEOF unary_expression'
    raise UnhandledSyntaxError

def p_unary_expression_6(t):
    'unary_expression : SIZEOF LPAREN type_name RPAREN'
    raise UnhandledSyntaxError
    
#unary-operator
def p_unary_operator(t):
    '''unary_operator : AND
                    | TIMES
                    | PLUS 
                    | MINUS
                    | NOT
                    | LNOT '''
    t[0] = t[1]

# postfix-expression:
def p_postfix_expression_1(t):
    'postfix_expression : primary_expression'
    t[0] = t[1]

def p_postfix_expression_2(t):
    'postfix_expression : postfix_expression LBRACKET expression RBRACKET'
    t[0] = translator.ArrayAccessExpression(t[1], t[3])

def p_postfix_expression_3(t):
    'postfix_expression : postfix_expression LPAREN argument_expression_list RPAREN'
    t[0] = translator.FunctionCallExpression(t[1], t[3])

def p_postfix_expression_4(t):
    'postfix_expression : postfix_expression LPAREN RPAREN'
    t[0] = translator.FunctionCallExpression(t[1], None)

def p_postfix_expression_5(t):
    'postfix_expression : postfix_expression PERIOD ID'
    member = translator.Variable(t[3])
    t[0] = translator.InstanceMemberAccessExpression(t[1], member)

def p_postfix_expression_6(t):
    'postfix_expression : postfix_expression ARROW ID'
    member = translator.Variable(t[3])
    t[0] = translator.PointerMemberAccessExpression(t[1], member)

def p_postfix_expression_7(t):
    'postfix_expression : postfix_expression PLUSPLUS'
    t[0] = translator.UnaryOperandExpression(t[1], t[2], isPrefix=False)

def p_postfix_expression_8(t):
    'postfix_expression : postfix_expression MINUSMINUS'
    t[0] = translator.UnaryOperandExpression(t[1], t[2], isPrefix=False)

# primary-expression:
def p_primary_expression_1(t):
    'primary_expression :  ID'
    t[0] = translator.Variable(t[1])

def p_primary_expression_2(t):
    'primary_expression :  constant'
    t[0] = t[1]


def p_primary_expression_3(t):
    'primary_expression : LPAREN expression RPAREN'
    t[0] = t[2]

# argument-expression-list:
def p_argument_expression_list_1(t):
    'argument_expression_list :  assignment_expression'
    t[0] = [ t[1] ]

def p_argument_expression_list_2(t):
    'argument_expression_list :  argument_expression_list COMMA assignment_expression'
    t[0] = t[1] + [ t[3] ]

# constant:
def p_constant_1(t): 
    'constant : ICONST'
    t[0] = translator.IntConstant(t[1])

def p_constant_2(t): 
    'constant : FCONST'
    t[0] = translator.FloatConstant(t[1])

def p_constant_3(t): 
    '''constant : CCONST'''
    t[0] = translator.CharConstant(t[1])

def p_constant_4(t): 
    '''constant : SCONST'''
    t[0] = translator.StringConstant(t[1])

def p_empty(t):
    'empty : '
    t[0] = None

def p_error(t):
    print("Whoa. We're hosed")
    raise ParseError

import profile
# Build the grammar

parser = yacc.yacc(method='LALR')
# parser = yacc.yacc()

#profile.run("yacc.yacc(method='LALR')")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <input_file_name> <output_file_name>" % sys.argv[0])
        sys.exit(-1)
    with open(sys.argv[1], "r") as fIn:
        data = fIn.read()
        translator.CodeEmitter.init(sys.argv[2])
        translator.CodeEmitter.append(data)
        translator.CodeEmitter.appendLine("")
        translator.CodeEmitter.appendLine("**********************************")
        data = translator.preprocess(data)
        result = parser.parse(data, debug=0)
        result.translate()
