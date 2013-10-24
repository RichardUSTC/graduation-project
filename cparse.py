# -----------------------------------------------------------------------------
# cparse.py
#
# Simple parser for ANSI C.  Based on the grammar in K&R, 2nd Ed.
# -----------------------------------------------------------------------------

import sys
import exceptions
import clex
import ply.yacc as yacc
import syntax_node
import predef
import pdb

class UnhandledSyntaxError(Exception):
    def __init__(self, lineno, production):
        self.lineno = lineno
        self.production = production
    def __str__(self):
        return "Error @"+self.lineno+':' + production
    def __repr__(self):
        return self.__str__()

# Get the token map
tokens = clex.tokens

# Set start point
start = 'compound_statement'

# translation-unit:

def p_translation_unit_1(t):
    'translation_unit : external_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_translation_unit_2(t):
    'translation_unit : translation_unit external_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# external-declaration:

def p_external_declaration_1(t):
    'external_declaration : function_definition'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_external_declaration_2(t):
    'external_declaration : declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# function-definition:

def p_function_definition_1(t):
    'function_definition : declaration_specifiers declarator declaration_list compound_statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_function_definition_2(t):
    'function_definition : declarator declaration_list compound_statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_function_definition_3(t):
    'function_definition : declarator compound_statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_function_definition_4(t):
    'function_definition : declaration_specifiers declarator compound_statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# declaration:

def p_declaration_1(t):
    'declaration : declaration_specifiers init_declarator_list SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_2(t):
    'declaration : declaration_specifiers SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# declaration-list:

def p_declaration_list_1(t):
    'declaration_list : declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_list_2(t):
    'declaration_list : declaration_list declaration '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# declaration-specifiers
def p_declaration_specifiers_1(t):
    'declaration_specifiers : storage_class_specifier declaration_specifiers'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_specifiers_2(t):
    'declaration_specifiers : type_specifier declaration_specifiers'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_specifiers_3(t):
    'declaration_specifiers : type_qualifier declaration_specifiers'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_specifiers_4(t):
    'declaration_specifiers : storage_class_specifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_specifiers_5(t):
    'declaration_specifiers : type_specifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declaration_specifiers_6(t):
    'declaration_specifiers : type_qualifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# storage-class-specifier
def p_storage_class_specifier(t):
    '''storage_class_specifier : AUTO
                               | REGISTER
                               | STATIC
                               | EXTERN
                               | TYPEDEF
                               '''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# type-specifier:
def p_type_specifier(t):
    '''type_specifier : VOID
                      | CHAR
                      | SHORT
                      | INT
                      | LONG
                      | FLOAT
                      | DOUBLE
                      | SIGNED
                      | UNSIGNED
                      | struct_or_union_specifier
                      | enum_specifier
                      | TYPEID
                      '''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# type-qualifier:
def p_type_qualifier(t):
    '''type_qualifier : CONST
                      | VOLATILE'''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-or-union-specifier

def p_struct_or_union_specifier_1(t):
    'struct_or_union_specifier : struct_or_union ID LBRACE struct_declaration_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_or_union_specifier_2(t):
    'struct_or_union_specifier : struct_or_union LBRACE struct_declaration_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_or_union_specifier_3(t):
    'struct_or_union_specifier : struct_or_union ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-or-union:
def p_struct_or_union(t):
    '''struct_or_union : STRUCT
                       | UNION
                       '''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-declaration-list:

def p_struct_declaration_list_1(t):
    'struct_declaration_list : struct_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_declaration_list_2(t):
    'struct_declaration_list : struct_declaration_list struct_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# init-declarator-list:

def p_init_declarator_list_1(t):
    'init_declarator_list : init_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_init_declarator_list_2(t):
    'init_declarator_list : init_declarator_list COMMA init_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# init-declarator

def p_init_declarator_1(t):
    'init_declarator : declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_init_declarator_2(t):
    'init_declarator : declarator EQUALS initializer'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-declaration:

def p_struct_declaration(t):
    'struct_declaration : specifier_qualifier_list struct_declarator_list SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# specifier-qualifier-list:

def p_specifier_qualifier_list_1(t):
    'specifier_qualifier_list : type_specifier specifier_qualifier_list'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_specifier_qualifier_list_2(t):
    'specifier_qualifier_list : type_specifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_specifier_qualifier_list_3(t):
    'specifier_qualifier_list : type_qualifier specifier_qualifier_list'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_specifier_qualifier_list_4(t):
    'specifier_qualifier_list : type_qualifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-declarator-list:

def p_struct_declarator_list_1(t):
    'struct_declarator_list : struct_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_declarator_list_2(t):
    'struct_declarator_list : struct_declarator_list COMMA struct_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# struct-declarator:

def p_struct_declarator_1(t):
    'struct_declarator : declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_declarator_2(t):
    'struct_declarator : declarator COLON constant_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_struct_declarator_3(t):
    'struct_declarator : COLON constant_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# enum-specifier:

def p_enum_specifier_1(t):
    'enum_specifier : ENUM ID LBRACE enumerator_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_enum_specifier_2(t):
    'enum_specifier : ENUM LBRACE enumerator_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_enum_specifier_3(t):
    'enum_specifier : ENUM ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# enumerator_list:
def p_enumerator_list_1(t):
    'enumerator_list : enumerator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_enumerator_list_2(t):
    'enumerator_list : enumerator_list COMMA enumerator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# enumerator:
def p_enumerator_1(t):
    'enumerator : ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_enumerator_2(t):
    'enumerator : ID EQUALS constant_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# declarator:

def p_declarator_1(t):
    'declarator : pointer direct_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_declarator_2(t):
    'declarator : direct_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# direct-declarator:

def p_direct_declarator_1(t):
    'direct_declarator : ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_declarator_2(t):
    'direct_declarator : LPAREN declarator RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_declarator_3(t):
    'direct_declarator : direct_declarator LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_declarator_4(t):
    'direct_declarator : direct_declarator LPAREN parameter_type_list RPAREN '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_declarator_5(t):
    'direct_declarator : direct_declarator LPAREN identifier_list RPAREN '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_declarator_6(t):
    'direct_declarator : direct_declarator LPAREN RPAREN '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# pointer:
def p_pointer_1(t):
    'pointer : TIMES type_qualifier_list'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_pointer_2(t):
    'pointer : TIMES'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_pointer_3(t):
    'pointer : TIMES type_qualifier_list pointer'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_pointer_4(t):
    'pointer : TIMES pointer'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# type-qualifier-list:

def p_type_qualifier_list_1(t):
    'type_qualifier_list : type_qualifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_type_qualifier_list_2(t):
    'type_qualifier_list : type_qualifier_list type_qualifier'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# parameter-type-list:

def p_parameter_type_list_1(t):
    'parameter_type_list : parameter_list'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_parameter_type_list_2(t):
    'parameter_type_list : parameter_list COMMA ELLIPSIS'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# parameter-list:

def p_parameter_list_1(t):
    'parameter_list : parameter_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_parameter_list_2(t):
    'parameter_list : parameter_list COMMA parameter_declaration'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# parameter-declaration:
def p_parameter_declaration_1(t):
    'parameter_declaration : declaration_specifiers declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_parameter_declaration_2(t):
    'parameter_declaration : declaration_specifiers abstract_declarator_opt'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# identifier-list:
def p_identifier_list_1(t):
    'identifier_list : ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_identifier_list_2(t):
    'identifier_list : identifier_list COMMA ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# initializer:

def p_initializer_1(t):
    'initializer : assignment_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_initializer_2(t):
    '''initializer : LBRACE initializer_list RBRACE
                   | LBRACE initializer_list COMMA RBRACE'''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# initializer-list:

def p_initializer_list_1(t):
    'initializer_list : initializer'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_initializer_list_2(t):
    'initializer_list : initializer_list COMMA initializer'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# type-name:

def p_type_name(t):
    'type_name : specifier_qualifier_list abstract_declarator_opt'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_abstract_declarator_opt_1(t):
    'abstract_declarator_opt : empty'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_abstract_declarator_opt_2(t):
    'abstract_declarator_opt : abstract_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# abstract-declarator:

def p_abstract_declarator_1(t):
    'abstract_declarator : pointer '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_abstract_declarator_2(t):
    'abstract_declarator : pointer direct_abstract_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_abstract_declarator_3(t):
    'abstract_declarator : direct_abstract_declarator'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# direct-abstract-declarator:

def p_direct_abstract_declarator_1(t):
    'direct_abstract_declarator : LPAREN abstract_declarator RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_abstract_declarator_2(t):
    'direct_abstract_declarator : direct_abstract_declarator LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_abstract_declarator_3(t):
    'direct_abstract_declarator : LBRACKET constant_expression_opt RBRACKET'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_abstract_declarator_4(t):
    'direct_abstract_declarator : direct_abstract_declarator LPAREN parameter_type_list_opt RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_direct_abstract_declarator_5(t):
    'direct_abstract_declarator : LPAREN parameter_type_list_opt RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# Optional fields in abstract declarators

def p_constant_expression_opt_1(t):
    'constant_expression_opt : empty'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_constant_expression_opt_2(t):
    'constant_expression_opt : constant_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_parameter_type_list_opt_1(t):
    'parameter_type_list_opt : empty'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_parameter_type_list_opt_2(t):
    'parameter_type_list_opt : parameter_type_list'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

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
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_labeled_statement_2(t):
    'labeled_statement : CASE constant_expression COLON statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_labeled_statement_3(t):
    'labeled_statement : DEFAULT COLON statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# expression-statement:
def p_expression_statement(t):
    'expression_statement : expression_opt SEMI'
    t[0] = t[1]

# compound-statement:

def p_compound_statement_1(t):
    'compound_statement : LBRACE declaration_list statement_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_compound_statement_2(t):
    'compound_statement : LBRACE statement_list RBRACE'
    t[0] = t[2]

def p_compound_statement_3(t):
    'compound_statement : LBRACE declaration_list RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_compound_statement_4(t):
    'compound_statement : LBRACE RBRACE'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# statement-list:

def p_statement_list_1(t):
    'statement_list : statement'
    t[0] = [ t[1] ]

def p_statement_list_2(t):
    'statement_list : statement_list statement'
    t[0] = t[1].append(t[2])

# selection-statement

def p_selection_statement_1(t):
    'selection_statement : IF LPAREN expression RPAREN statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_selection_statement_2(t):
    'selection_statement : IF LPAREN expression RPAREN statement ELSE statement '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_selection_statement_3(t):
    'selection_statement : SWITCH LPAREN expression RPAREN statement '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# iteration_statement:

def p_iteration_statement_1(t):
    'iteration_statement : WHILE LPAREN expression RPAREN statement'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_iteration_statement_2(t):
    'iteration_statement : FOR LPAREN expression_opt SEMI expression_opt SEMI expression_opt RPAREN statement '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_iteration_statement_3(t):
    'iteration_statement : DO statement WHILE LPAREN expression RPAREN SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# jump_statement:

def p_jump_statement_1(t):
    'jump_statement : GOTO ID SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_jump_statement_2(t):
    'jump_statement : CONTINUE SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_jump_statement_3(t):
    'jump_statement : BREAK SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_jump_statement_4(t):
    'jump_statement : RETURN expression_opt SEMI'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_expression_opt_1(t):
    'expression_opt : empty'
    t[0] = None

def p_expression_opt_2(t):
    'expression_opt : expression'
    t[0] = t[1]

# expression:
def p_expression_1(t):
    'expression : assignment_expression'
    t[0] = t[1]

def p_expression_2(t):
    'expression : expression COMMA assignment_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# assigment_expression:
def p_assignment_expression_1(t):
    'assignment_expression : conditional_expression'
    t[0] = t[1]

def p_assignment_expression_2(t):
    'assignment_expression : unary_expression assignment_operator assignment_expression'
    t[0] = syntax_node.BinaryOperandExpression(t[1], t[2], t[3])

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
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# constant-expression

def p_constant_expression(t):
    'constant_expression : conditional_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# logical-or-expression

def p_logical_or_expression_1(t):
    'logical_or_expression : logical_and_expression'
    t[0] = t[1]

def p_logical_or_expression_2(t):
    'logical_or_expression : logical_or_expression LOR logical_and_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# logical-and-expression

def p_logical_and_expression_1(t):
    'logical_and_expression : inclusive_or_expression'
    t[0] = t[1]

def p_logical_and_expression_2(t):
    'logical_and_expression : logical_and_expression LAND inclusive_or_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# inclusive-or-expression:

def p_inclusive_or_expression_1(t):
    'inclusive_or_expression : exclusive_or_expression'
    t[0] = t[1]

def p_inclusive_or_expression_2(t):
    'inclusive_or_expression : inclusive_or_expression OR exclusive_or_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# exclusive-or-expression:

def p_exclusive_or_expression_1(t):
    'exclusive_or_expression :  and_expression'
    t[0] = t[1]

def p_exclusive_or_expression_2(t):
    'exclusive_or_expression :  exclusive_or_expression XOR and_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# AND-expression

def p_and_expression_1(t):
    'and_expression : equality_expression'
    t[0] = t[1]

def p_and_expression_2(t):
    'and_expression : and_expression AND equality_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)


# equality-expression:
def p_equality_expression_1(t):
    'equality_expression : relational_expression'
    t[0] = t[1]

def p_equality_expression_2(t):
    'equality_expression : equality_expression EQ relational_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_equality_expression_3(t):
    'equality_expression : equality_expression NE relational_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)


# relational-expression:
def p_relational_expression_1(t):
    'relational_expression : shift_expression'
    t[0] = t[1]

def p_relational_expression_2(t):
    'relational_expression : relational_expression LT shift_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_relational_expression_3(t):
    'relational_expression : relational_expression GT shift_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_relational_expression_4(t):
    'relational_expression : relational_expression LE shift_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_relational_expression_5(t):
    'relational_expression : relational_expression GE shift_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# shift-expression

def p_shift_expression_1(t):
    'shift_expression : additive_expression'
    t[0] = t[1]

def p_shift_expression_2(t):
    'shift_expression : shift_expression LSHIFT additive_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_shift_expression_3(t):
    'shift_expression : shift_expression RSHIFT additive_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# additive-expression

def p_additive_expression_1(t):
    'additive_expression : multiplicative_expression'
    t[0] = t[1]

def p_additive_expression_2(t):
    'additive_expression : additive_expression PLUS multiplicative_expression'
    t[0] = syntax_node.BinaryOperandExpression(t[1], t[2], t[3])

def p_additive_expression_3(t):
    'additive_expression : additive_expression MINUS multiplicative_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# multiplicative-expression

def p_multiplicative_expression_1(t):
    'multiplicative_expression : cast_expression'
    t[0] = t[1]

def p_multiplicative_expression_2(t):
    'multiplicative_expression : multiplicative_expression TIMES cast_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_multiplicative_expression_3(t):
    'multiplicative_expression : multiplicative_expression DIVIDE cast_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_multiplicative_expression_4(t):
    'multiplicative_expression : multiplicative_expression MOD cast_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# cast-expression:

def p_cast_expression_1(t):
    'cast_expression : unary_expression'
    t[0] = t[1]

def p_cast_expression_2(t):
    'cast_expression : LPAREN type_name RPAREN cast_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# unary-expression:
def p_unary_expression_1(t):
    'unary_expression : postfix_expression'
    t[0] = t[1]

def p_unary_expression_2(t):
    'unary_expression : PLUSPLUS unary_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_unary_expression_3(t):
    'unary_expression : MINUSMINUS unary_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_unary_expression_4(t):
    'unary_expression : unary_operator cast_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_unary_expression_5(t):
    'unary_expression : SIZEOF unary_expression'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_unary_expression_6(t):
    'unary_expression : SIZEOF LPAREN type_name RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)
    
#unary-operator
def p_unary_operator(t):
    '''unary_operator : AND
                    | TIMES
                    | PLUS 
                    | MINUS
                    | NOT
                    | LNOT '''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# postfix-expression:
def p_postfix_expression_1(t):
    'postfix_expression : primary_expression'
    t[0] = t[1]

def p_postfix_expression_2(t):
    'postfix_expression : postfix_expression LBRACKET expression RBRACKET'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_3(t):
    'postfix_expression : postfix_expression LPAREN argument_expression_list RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_4(t):
    'postfix_expression : postfix_expression LPAREN RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_5(t):
    'postfix_expression : postfix_expression PERIOD ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_6(t):
    'postfix_expression : postfix_expression ARROW ID'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_7(t):
    'postfix_expression : postfix_expression PLUSPLUS'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_postfix_expression_8(t):
    'postfix_expression : postfix_expression MINUSMINUS'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# primary-expression:
def p_primary_expression_1(t):
    'primary_expression :  ID'
    try:
        t[0] = predef.predefinedValues[t[1]]
    except KeyError:
        raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_primary_expression_2(t):
    'primary_expression :  constant'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_primary_expression_3(t):
    'primary_expression : SCONST'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_primary_expression_3(t):
    'primary_expression : LPAREN expression RPAREN'
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# argument-expression-list:
def p_argument_expression_list(t):
    '''argument_expression_list :  assignment_expression
                              |  argument_expression_list COMMA assignment_expression'''
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

# constant:
def p_constant(t): 
   '''constant : ICONST
              | FCONST
              | CCONST'''
   raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)


def p_empty(t):
    'empty : '
    raise UnhandledSyntaxError(t.lexer.lineno, sys._getframe().f_code.co_name.__doc__)

def p_error(t):
    print("Whoa. We're hosed")

import profile
# Build the grammar

parser = yacc.yacc(method='LALR')
# parser = yacc.yacc()

#profile.run("yacc.yacc(method='LALR')")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <input_file_name>" % sys.argv[0])
        sys.exit(-1)
    with open(sys.argv[1], "r") as fIn:
        data = fIn.read()
        result = parser.parse(data, debug=0)
        print result