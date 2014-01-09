import exceptions
import re
import struct
import cparse
import clex
import pdb

#####################################################################
#
#                      Bitfield Operator Support
#
#####################################################################

bitOp1ArgRE = re.compile(r'<\s*(\w+)\s*:\s*>')

bitOpWordRE = re.compile(r'(?<![\w\.])([\w\.]+)<\s*(\w+)\s*:\s*(\w+)\s*>')
bitOpExprRE = re.compile(r'\)<\s*(\w+)\s*:\s*(\w+)\s*>')

def substBitOps(code):
    # first convert single-bit selectors to two-index form
    # i.e., <n> --> <n:n>
    code = bitOp1ArgRE.sub(r'<\1:\1>', code)
    # simple case: selector applied to ID (name)
    # i.e., foo<a:b> --> bits(foo, a, b)
    code = bitOpWordRE.sub(r'bits(\1, \2, \3)', code)
    # if selector is applied to expression (ending in ')'),
    # we need to search backward for matching '('
    match = bitOpExprRE.search(code)
    while match:
        exprEnd = match.start()
        here = exprEnd - 1
        nestLevel = 1
        while nestLevel > 0:
            if code[here] == '(':
                nestLevel -= 1
            elif code[here] == ')':
                nestLevel += 1
            here -= 1
            if here < 0:
                sys.exit("Didn't find '('!")
        exprStart = here+1
        newExpr = r'bits(%s, %s, %s)' % (code[exprStart:exprEnd+1],
                                         match.group(1), match.group(2))
        code = code[:exprStart] + newExpr + code[match.end():]
        match = bitOpExprRE.search(code)
    return code

sextRE = re.compile(r'(?<!\w)sext\<(\d+)\>')
def substSext(code):
    code = sextRE.sub(r'sext_\1', code)
    return code

def preprocess(code):
    return substBitOps(substSext(code))

class UnhandledTranslationError(Exception): pass

class CodeEmitter(object):
    @classmethod
    def init(cls):
        cls.code = ""
        cls.regexBuilder = re.compile("(?<!\w)builder(?!\w)")
        cls.regexContext = re.compile("(?<!\w)context(?!\w)")
        cls.regexModule = re.compile("(?<!\w)module(?!\w)")
        cls.hasBuilder = False
        cls.hasContext = False
        cls.hasModule = False
        Temp.reset()
    @classmethod
    def appendHelper(cls, code):
        'if the code uses "builder", "context" or "module", add code to read them'
        if cls.hasBuilder==False and cls.regexBuilder.search(code) != None:
            cls.hasBuilder = True
            cls.code = "IRBuilder<> *builder = Translator::getBuilder();\n" + cls.code
        if cls.hasContext==False and cls.regexContext.search(code) != None:
            cls.hasContext = True
            cls.code = "LLVMContext& context = Translator::getContext();\n" + cls.code
        if cls.hasModule==False and cls.regexModule.search(code) != None:
            cls.hasModule = True
            cls.code = "Module* module = Translator::getModule();\n" + cls.code
    @classmethod
    def append(cls, code):
        cls.appendHelper(code)
        cls.code += code
    @classmethod
    def appendLine(cls, code):
        cls.appendHelper(code)
        cls.code += code + '\n'
    @classmethod
    def getCode(cls):
        return cls.code

class BranchGenerator(object):
    def __init__(self, condName=None, mayAppend=False):
        self.state = "init"
        self.mayAppend = mayAppend
        self.condName = condName
        self.trueBlockName = "trueBlock_%d" % Temp.getTempId()
        self.falseBlockName = "falseBlock_%d" % Temp.getTempId()
        self.exitBlockName = "exitBlock_%d" % Temp.getTempId()
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.trueBlockName, self.trueBlockName))
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.falseBlockName, self.falseBlockName))
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.exitBlockName, self.exitBlockName))
    def setCondName(self, condName):
        self.condName = condName
    def setMayAppend(self, mayAppend):
        self.mayAppend = mayAppend
    def startCondition(self):
        assert self.state == "init"
        self.state = "start condition"
    def endCondition(self):
        assert self.state == "start condition"
        self.state = "end condition"
        assert self.condName != None
        CodeEmitter.appendLine("builder->CreateCondBr(%s, %s, %s);" % (self.condName, self.trueBlockName, self.falseBlockName))
    def startTruePart(self):
        assert self.state == "end condition"
        self.state = "start true part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.trueBlockName)
    def endTruePart(self):
        assert self.state == "start true part"
        self.state = "end true part"
        if self.mayAppend:
            self.truePartIP = "insert_point_of_true_%d" % Temp.getTempId()
            CodeEmitter.appendLine("IRBuilder<>::InsertPoint %s = builder->saveIP();" % self.truePartIP)
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
    def startFalsePart(self):
        assert self.state == "end true part"
        self.state = "start false part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.falseBlockName)
    def endFalsePart(self):
        assert self.state == "start false part"
        self.state = "end false part"
        if self.mayAppend:
            self.falsePartIP = "insert_point_of_false_%d" % Temp.getTempId()
            CodeEmitter.appendLine("IRBuilder<>::InsertPoint %s = builder->saveIP();" % self.falsePartIP)
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
    def startAppendToTruePart(self):
        assert self.state == "end false part"
        self.state = "start append to true part"
        self.IP = "insert_point_%d" % Temp.getTempId()
        CodeEmitter.appendLine("IRBuilder<>::InsertPoint %s = builder->saveIP();" % self.IP)
        CodeEmitter.appendLine("builder->RestoreIP(%s);" % self.truePartIP)
    def endAppendToTruePart(self):
        assert self.state == "start append to true part"
        self.state = "end false part"
        CodeEmitter.appendLine("builder->RestoreIP(%s);" % self.IP)
    def startAppendToFalsePart(self):
        assert self.state == "end false part"
        self.state = "start append to false part"
        self.IP = "insert_point_%d" % Temp.getTempId()
        CodeEmitter.appendLine("IRBuilder<>::InsertPoint %s = builder->saveIP();" % self.IP)
        CodeEmitter.appendLine("builder->RestoreIP(%s);" % self.falsePartIP)
    def endAppendToFalsePart(self):
        assert self.state == "start append to false part"
        self.state = "end false part"
        CodeEmitter.appendLine("builder->RestoreIP(%s);" % self.IP)
    def startExitPart(self):
        assert self.state == "end false part"
        self.state = "start exit part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.exitBlockName)
    def endExitPart(self):
        assert self.state == "start exit part"
        self.state = "end exit part"
    def addPhi(self, name, irType, condTrueValue, condFalseValue):
        assert self.state == "start exit part"
        CodeEmitter.appendLine("PHINode *%s = builder->CreatePHI(%s, 2);" % (name, irType))
        CodeEmitter.appendLine("%s->addIncoming(%s, %s);" % (name, condTrueValue, self.trueBlockName))
        CodeEmitter.appendLine("%s->addIncoming(%s, %s);" % (name, condFalseValue, self.falseBlockName))

class LoopType(object):
    WHILE = 0
    DO_WHILE = 1
    FOR = 2

class LoopGenerator(object):
    def __init__(self, loopType, condName=None):
        self.loopType = loopType
        self.state = "init"
        self.condName = condName
        self.condBlockName = "cond_block_%d" % Temp.getTempId()
        self.bodyBlockName = "body_block_%d" % Temp.getTempId()
        self.exitBlockName = "exit_block_%d" % Temp.getTempId()
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.condBlockName, self.condBlockName))
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.bodyBlockName, self.bodyBlockName))
        CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
            (self.exitBlockName, self.exitBlockName))
        if loopType == LoopType.FOR:
            self.postLoopBodyBlockName = "post_body_block_%d" % Temp.getTempId()
            CodeEmitter.appendLine("BasicBlock *%s = BasicBlock::Create(context, \"%s\", Translator::getCurFunc());" %
                (self.postLoopBodyBlockName, self.postLoopBodyBlockName))
    def setCondName(self, condName):
        self.condName = condName
    def startCondition(self):
        if self.loopType == LoopType.DO_WHILE:
            assert self.state == "end loop body"
        else:
            assert self.state == "init"
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.condBlockName)
        self.state = "start condition"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.condBlockName)
    def endCondition(self):
        assert self.state == "start condition"
        self.state = "end condition"
        assert self.condName != None
        CodeEmitter.appendLine("builder->CreateCondBr(%s, %s, %s);" % (self.condName, self.bodyBlockName, self.exitBlockName))
    def startLoopBody(self):
        if self.loopType == LoopType.DO_WHILE:
            assert self.state == "init"
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.bodyBlockName)
        else:
            assert self.state == "end condition"
        self.state = "start loop body"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.bodyBlockName)
    def endLoopBody(self):
        assert self.state == "start loop body"
        self.state = "end loop body"
        if self.loopType == LoopType.FOR:
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.postLoopBodyBlockName)
        else:
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.condBlockName)
    def startPostLoopBodyPart(self):
        assert self.loopType == LoopType.FOR
        assert self.state == "end loop body"
        self.state = "start post loop body part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.postLoopBodyBlockName)
    def endPostLoopBodyPart(self):
        assert self.state == "start post loop body part"
        self.state = "end post loop body part"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.condBlockName)
    def startExitPart(self):
        if self.loopType == LoopType.DO_WHILE:
            assert self.state == "end condition"
        elif self.loopType == LoopType.FOR:
            assert self.state == "end post loop body part"
        else:
            assert self.state == "end loop body"
        self.state = "start exit part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.exitBlockName)
    def endExitPart(self):
        assert self.state == "start exit part"
        self.state = "end exit part"
    def startBreak(self):
        assert self.state == "start loop body"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
    def endBreak(self):
        pass
    def startContinue(self):
        assert self.state == "start loop body"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.postLoopBodyBlockName)
    def endContinue(self):
        pass

class SwitchGenerator(object):
    def __init__(self, control):
        assert isinstance(control, TranslationResult)
        self.control = control
        self.exitBlockName = "exit_block_%d" % Temp.getTempId()
        self.nextCaseBlockName = "case_block_%d" % Temp.getTempId()
        self.nextCaseBodyBlockName = self.nextCaseBlockName + "_body"
        self.defaultBodyBlockName = None
        self.state = "init"
        self.isDefaultAtLast = False
    def startSwtich(self):
        assert self.state == "init"
        self.state = "in switch"
        if not isinstance(self.control.type, IntType):
            self.control = TypeCaster.castTo(IntType(True, 64), self.control)
        CodeEmitter.appendLine("BasicBlock *%s = builder->CreateBlock();" % self.nextCaseBlockName)
        CodeEmitter.appendLine("BasicBlock *%s = builder->CreateBlock();" % self.exitBlockName)
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.nextCaseBlockName)
    def startBreak(self):
        assert self.state == "in switch"
        self.state = "in break"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
        pass
    def endBreak(self):
        assert self.state == "in break"
        self.state = "in switch"
        pass
    def addCase(self, case):
        assert self.state == "in switch"
        assert isinstance(case, Constant)

        caseBlockName = self.nextCaseBlockName
        caseBodyBlockName = self.nextCaseBodyBlockName
        self.nextCaseBlockName = "case_block_%d" % Temp.getTempId()
        self.nextCaseBodyBlockName = self.nextCaseBlockName + "_body"

        #Jump to the body of this case. If the previous case body has 'break', this 'br' instruction will be eliminated by LLVM
        CodeEmitter.appendLine("BasicBlock *%s = builder->CreateBlock();" % caseBodyBlockName)
        CodeEmitter.appendLine("builder->CreateBr(%s);" % caseBodyBlockName)

        CodeEmitter.appendLine("BasicBlock *%s = builder->CreateBlock();" % self.nextCaseBlockName)

        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % caseBlockName)
        caseResult = case.translate()
        newCaseResult = TypeCaster.castTo(self.control.type, caseResult)
        isEqual = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = builder->CreateICmpEQ(%s, %s);" % (isEqual, self.control.value, newCaseResult.value))
        CodeEmitter.appendLine("builder->CreateCondBr(%s, %s, %s);" % (isEqual, caseBodyBlockName, self.nextCaseBlockName))
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % caseBodyBlockName)

    def addDefault(self):
        assert self.state == "in switch"
        self.defaultBodyBlockName = "default_body_%d" % Temp.getTempId()
        CodeEmitter.appendLine("BasicBlock *%s = builder->CreateBlock();" % self.defaultBodyBlockName)
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.defaultBodyBlockName)
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.defaultBodyBlockName)

    def endSwitch(self):
        assert self.state == "in switch"
        self.state = "out of switch"

        # let the last case body jump to exit
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.nextCaseBlockName)
        if self.defaultBodyBlockName != None:
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.defaultBodyBlockName)
        else:
            CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.exitBlockName)

class Temp(object):
    i = 0
    @classmethod
    def getTempName(cls):
        cls.i += 1
        return 't' + str(cls.i)
    @classmethod
    def getTempId(cls):
        cls.i += 1
        return cls.i
    @classmethod
    def reset(cls):
        cls.i = 0

class TranslationResult(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value
    def __str__(self):
        return "%s:%s" % (str(self.value), str(self.type))
    def __repr__(self):
        return self.__str__()

class TypeCompareError(Exception): pass
class TypeCastError(Exception): pass
class TypeCompareResult(object):
    EQ = 0
    LT = -1
    GT = 1
    INCOMPARABLE = 2

class TypeCaster(object):
    @classmethod
    def integralPromotion(cls, input):
        if isinstance(input, IntType):
            if input.type.compare(IntType()) == TypeCompareResult.LT:
                return cls.castTo(IntType(), input)
        return input
    @classmethod
    def castForArithmetic(cls, result1, result2):
        assert isinstance(result1, TranslationResult)
        assert isinstance(result2, TranslationResult)
        try:
            result1 = cls.integralPromotion(result1)
            result2 = cls.integralPromotion(result2)
            type1 = result1.type
            type2 = result2.type
            if type1.compare(type2) == TypeCompareResult.EQ:
                return (result1, result2)
            elif type1.compare(type2) == TypeCompareResult.GT:
                newResult2 = cls.castTo(type1, result2)
                return (result1, newResult2)
            elif type1.compare(type2) == TypeCompareResult.LT:
                newResult1 = cls.castTo(type2, result1)
                return (newResult1, result2)
            else:
                raise TypeCastError
        except TypeCompareError:
            raise TypeCastError
    @classmethod
    def castTo(cls, targetType, input):
        assert isinstance(input, TranslationResult)
        if targetType.compare(input.type) == TypeCompareResult.EQ:
            return input
        newValue = Temp.getTempName()
        typeName = targetType.getIRType()
        if isinstance(targetType, DoubleType):
            CodeEmitter.appendLine("Value *%s = builder->CreateFPCast(%s, %s);" % (newValue, input.value, typeName))
        elif isinstance(targetType, FloatType):
            CodeEmitter.appendLine("Value *%s = builder->CreateFPCast(%s, %s);" %(newValue, input.value, typeName))
        elif isinstance(targetType, IntType):
            if targetType.isSigned:
                isSigned = "true"
            else:
                isSigned = "false"
            CodeEmitter.appendLine("Value *%s = builder->CreateIntCast(%s, %s, %s);" % (newValue, input.value, typeName, isSigned))
        elif isinstance(targetType, PointerType):
            CodeEmitter.appendLine("Value *%s = builder->CreatePointerCast(%s, %s)" % (newValue, input.value, typeName))
        else:
            raise TypeCastError
        return TranslationResult(targetType, newValue)

class Type(object):
    def __repr__(self):
        return self.__str__()
    def compare(self, other):
        raise TypeCompareError
    def getIRType(self):
        raise UnhandledTranslationError
    def getBytes(self):
        raise UnhandledTranslationError

class VoidType(Type):
    def __str__(self):
        return 'void'
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = Type::getVoidTy(context);" % typeName)
        return typeName
    def compare(self, other):
        if isinstance(other, VoidType):
            return TypeCompareResult.EQ
        else:
            return TypeCompareResult.INCOMPARABLE
    def getBytes(self):
        return 0

class IntType(Type):
    def __init__(self, isSigned=True, size=struct.calcsize("i")*8):
        self.isSigned = isSigned
        self.size = size
    def __str__(self):
        s = ""
        if not self.isSigned:
            s += 'u'
        s += "int%d_t" % self.size
        return s
    def compare(self, other):
        if isinstance(other, FloatType) or isinstance(other, DoubleType):
            return -1
        elif isinstance(other, IntType):
            if self.size == other.size:
                if self.isSigned:
                    if other.isSigned:
                        return TypeCompareResult.EQ
                    else:
                        return TypeCompareResult.LT
                else:
                    if other.isSigned:
                        return TypeCompareResult.GT
                    else:
                        return TypeCompareResult.EQ
            else:
                if self.size - other.size > 0:
                    return TypeCompareResult.GT
                else:
                    return TypeCompareResult.LT
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = Type::getIntNTy(context, %d);" % (typeName, self.size))
        return typeName
    def getBytes(self):
        return (self.size+7)/8

class Twin64Type(Type):
    def __str__(self):
        return "Twin64_t"
    def getIRType(self):
        typeName = "twin64_t_%d" % (Temp.getTempId())
        CodeEmitter.appendLine("StructType *%s = module->getTypeByName(\"Twin64_t\");" % (typeName))
        CodeEmitter.appendLine("if(!%s){" % typeName);
        typeVectorName = "typeVector_%d" % Temp.getTempId()
        CodeEmitter.appendLine("std::vector<Type *> %s;" % typeVectorName)
        intType = IntType(size=64, isSigned=True)
        CodeEmitter.appendLine("%s.push_back(%s);" % (typeVectorName, intType.getIRType()))
        CodeEmitter.appendLine("%s.push_back(%s);" % (typeVectorName, intType.getIRType()))
        CodeEmitter.appendLine("%s = StructType::create(%s, \"Twin64_t\");" % (typeName, typeVectorName))
        CodeEmitter.appendLine("}");
        return structTypeName
    def getBytes(self):
        return 16

class FloatType(Type):
    def __str__(self):
        return 'float'
    def compare(self, other):
        if isinstance(other, DoubleType):
            return TypeCompareResult.LT
        elif isinstance(other, FloatType):
            return TypeCompareResult.EQ
        elif isinstance(other, IntType):
            return TypeCompareResult.GT
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = Type::getFloatTy(context);" % (typeName))
        return typeName
    def getBytes(self):
        return struct.calcsize("f")

class DoubleType(Type):
    def __str__(self):
        return 'double'
    def compare(self, other):
        if isinstance(other, DoubleType):
            return TypeCompareResult.EQ
        elif isinstance(other, FloatType) or isinstance(other, IntType):
            return TypeCompareResult.GT
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = Type::getDoubleTy(context);" % (typeName))
        return typeName
    def getBytes(self):
        return struct.calcsize("d")

class EnumType(IntType):
    pass

class TypeIDType(Type):
    def __init__(self, typeID):
        self.typeID = typeID
    def __str__(self):
        return self.typeID
    def getActualType(self):
        t = typeIDTable.get(self.typeID)
        assert t != None
        return t
    def getBytes(self):
        return self.getActualType().getBytes()

class PointerType(Type):
    def __init__(self, baseType=None, level=1):
        self.baseType = baseType
        self.level = 1
    def __str__(self):
        if self.baseType != None:
            s = str(self.baseType)
        else:
            s = "Unknown"
        for i in range(self.level):
            s += "*"
        return s
    def getIRType(self):
        baseTypeName = self.baseType.getIRType()
        for i in range(self.level):
            typeName = Temp.getTempName()
            CodeEmitter.appendLine("PointerType *%s = %s->getPointerTo();" % (typeName, baseTypeName))
            baseTypeName = typeName
        return typeName
    def compare(self, other):
        if isinstance(other, PointerType):
            compareResult = self.baseType.compare(other.baseType)
            if compareResult == TypeCompareResult.EQ:
                return TypeCompareResult.EQ
            else:
                return TypeCompareResult.INCOMPARABLE
        else:
            return TypeCompareResult.INCOMPARABLE
    def getBytes(self):
        return struct.calcsize("P")

class StructUnionBaseType(Type):
    structUnion = "struct/union"
    def __init__(self, name=None, definition=None):
        self.name = name
        self.definition = definition
        self.irTypeName = None
        self.fullType = None
        self.fullName = None
    def __str__(self):
        s = self.structUnion + " "
        if self.name != None:
            s += self.name
        if self.definition != None:
            s += "{\n"
            for field in self.definition:
                s += str(field)
                s += ";\n"
            s += "\n}"
        return s
    def getFullName(self):
        if self.fullName == None:
            if self.name != None:
                self.fullName = self.structUnion + "_" + self.name
            else:
                self.fullName = self.structUnion
        return self.fullName
    def getFullType(self):
        if self.fullType == None:
            if self.definition != None:
                self.fullType = self
            else:
                t = typeIDTable.get(self.getFullName())
                assert t != None
                self.fullType = t
        return self.fullType
    def compare(self, other):
        if not isinstance(other, StructUnionBaseType):
            return TypeCompareResult.INCOMPARABLE
        if self.getFullType() == other.getFullType():
            return TypeCompareResult.EQ
        else:
            return TypeCompareResult.INCOMPARABLE

class StructType(StructUnionBaseType):
    structUnion = "struct"
    def getIRType(self):
        fullType = self.getFullType()
        structTypeName = "%s_%d" % (self.getFullName(), Temp.getTempId())
        if fullType.irTypeName == None:
            fullType.irTypeName = structTypeName
        CodeEmitter.appendLine("StructType *%s = module->getTypeByName(\"%s\");" % (structTypeName, fullType.irTypeName))
        CodeEmitter.appendLine("if(!%s){" % structTypeName);
        fieldTypeVectorName = "fieldTypeVector_%d" % Temp.getTempId()
        CodeEmitter.appendLine("std::vector<Type *> %s;" % fieldTypeVectorName)
        for field in fullType.definition:
            assert isinstance(field, VariableDeclarator)
            fieldTypeName = field.variable.type.getIRType()
            CodeEmitter.appendLine("%s.push_back(%s);" % (fieldTypeVectorName, fieldTypeName))
        CodeEmitter.appendLine("%s = StructType::create(%s, \"%s\");" % (structTypeName, fieldTypeVectorName, fullType.irTypeName))
        CodeEmitter.appendLine("}");
        return structTypeName
    def getBytes(self):
        # Here I assume that all fields align to its bytes boundary. This might not be right, be cautious.
        bytes = 0
        fullType = self.getFullType()
        for field in fullType.definition:
            assert isinstance(field, VariableDeclarator)
            fieldBytes = field.variable.type.getBytes()
            if bytes % fieldBytes != 0:
                bytes += fieldBytes - bytes % fieldBytes
            bytes += fieldBytes
        return bytes
    def getFieldPointerByName(self, name, structPointer):
        fullType = self.getFullType()
        index = 0
        fieldType = None
        for field in fullType.definition:
            assert isinstance(field, VariableDeclarator)
            if field.variable.name == name:
                fieldType = field.variable.type
                break
            index += 1
        else:
            raise UnhandledTranslationError
        indexVectorName = "index_vector_%d" % Temp.getTempId()
        CodeEmitter.appendLine("std::vector<Value *> %s;" % indexVectorName)
        zero = "zero_%d" % Temp.getTempId()
        CodeEmitter.appendLine("Value *%s = getImm(0);" % zero)
        indexName = "index_%d" % Temp.getTempId()
        CodeEmitter.appendLine("Value *%s = getImm(%d)" % (indexName, index))
        CodeEmitter.appendLine("%s.push_back(%s);" % (indexVectorName, zero))
        CodeEmitter.appendLine("%s.push_back(%s);" % (indexVectorName, indexName))
        fieldPointerName = "%s_%s_%d" % (self.getFullName(), name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateGEP(%s, %s);" % (fieldPointerName, structPointer, indexVectorName))
        return TranslationResult(PointerType(fieldType), fieldPointerName)

class UnionType(StructUnionBaseType):
    structUnion = "union"
    def getIRType(self):
        fullType = self.getFullType()
        unionTypeName = "%s_%d" % (self.getFullName(), Temp.getTempId())
        if fullType.irTypeName == None:
            fullType.irTypeName = unionTypeName
        CodeEmitter.appendLine("StructType *%s = module->getTypeByName(\"%s\");" % (unionTypeName, fullType.irTypeName))
        CodeEmitter.appendLine("if(!%s){" % unionTypeName);
        fieldTypeVectorName = "fieldTypeVector_%d" % Temp.getTempId()
        CodeEmitter.appendLine("std::vector<Type *> %s;" % fieldTypeVectorName)
        greatestFieldSize = 0
        greatestFieldType = None
        for field in fullType.definition:
            assert isinstance(field, VariableDeclarator)
            fieldType = field.variable.type
            if fieldType.getBytes() > greatestFieldSize:
                greatestFieldSize = fieldType.getBytes
                greatestFieldType = fieldType
        assert greatestFieldType != None
        greatestFieldTypeName = greatestFieldType.getIRType()
        CodeEmitter.appendLine("%s.push_back(%s);" % (fieldTypeVectorName, greatestFieldTypeName))
        CodeEmitter.appendLine("%s = StructType::create(%s, \"%s\");" % (unionTypeName, fieldTypeVectorName, fullType.irTypeName))
        CodeEmitter.appendLine("}");
        return greatestFieldTypeName
    def getFieldPointerByName(self, name, unionPointer):
        fullType = self.getFullType()
        fieldType = None
        for field in fullType.definition:
            assert isinstance(field, VariableDeclarator)
            if field.variable.name == name:
                fieldType = field.variable.type
                break
        else:
            raise UnhandledTranslationError
        fieldTypeName = fieldType.getIRType()
        fieldPointerTypeName = Temp.getTempName()
        CodeEmitter.appendLine("PointerType *%s = %s->getPointerTo();" % (fieldPointerTypeName, fieldTypeName))
        fieldPointerName = "%s_%s_%d" % (self.getFullName(), name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateBitCast(%s, %s);" % (fieldPointerName, unionPointer, fieldPointerTypeName))
        return TranslationResult(PointerType(fieldType), fieldPointerName)

class Expression(object):
    def __repr__(self):
        return self.__str__()
    def setValue(self, result):
        raise UnhandledTranslationError
    def translate(self):
        raise UnhandledTranslationError
    def reference(self):
        raise UnhandledTranslationError
    def dereference(self):
        raise UnhandledTranslationError

class Variable(Expression):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type
    def __str__(self):
        return self.name
    def setValue(self, result):
        v = variableTable.get(self.name)
        if v != None:
            v.setValue(result)
        else:
            raise UnhandledTranslationError
    def getPointer(self):
        v = variableTable.get(self.name)
        if v != None:
            return v.getPointer()
        else:
            raise UnhandledTranslationError
    def translate(self):
        v = variableTable.get(self.name)
        # if cannot find the variable from variableTable, treat it as immediate
        if v != None:
            return v.translate()
        else:
            CodeEmitter.appendLine("/* Cannot find %s, treat it as immediate. */" % self.name)
            v = IntConstantVariable(self.name, IntType(True, 64))
            return v.translate()

class Operand(Variable):
    def setValue(self, result):
        newResult = TypeCaster.castTo(self.type, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, self.name))
    def getPointer(self):
        raise UnhandledTranslationError
    def translate(self):
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (value, self.name, value))
        return TranslationResult(self.type, value)

class IntConstantVariable(Variable):
    def translate(self):
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = getImm(%s);" % (value, self.name))
        return TranslationResult(self.type, value)
    def getPointer(self):
        raise UnhandledTranslationError
    def setValue(self):
        raise UnhandledTranslationError

class NormalVariable(Variable):
    def __init__(self, name, type, allocaValue):
        self.name = name
        self.type = type
        self.allocaValue = allocaValue
    def setValue(self, result):
        assert self.allocaValue != None
        newResult = TypeCaster.castTo(self.type, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, self.allocaValue))
    def getPointer(self):
        return TranslationResult(PointerType(self.type), self.allocaValue)
    def translate(self):
        assert self.allocaValue != None
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (value, self.allocaValue, value))
        return TranslationResult(self.type, value)

class BinaryOperandExpression(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        self.operator = operator
    def __str__(self):
        return "(%s %s %s)" % (str(self.left), self.operator, str(self.right))

    # for '+' '-' '*' '/' '%'
    def _translateHelper1(self, opType, intSignSensitive=False):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        if isinstance(operandType, IntType):
            if intSignSensitive:
                if operandType.isSigned:
                    function = "CreateS%s" % opType
                else:
                    function = "CreateU%s" % opType
            else:
                function = "Create%s" % opType
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            function = "CreateF%s" % opType
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(operandType, resultName)
    # for '|' '&' '^' '<<' '>>'
    def _translateHelper2(self, opType):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        assert isinstance(leftResult.type, IntType)
        assert isinstance(rightResult.type, IntType)
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        function = "Create%s" % opType
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(operandType, resultName)
    # for '<' '>' '<=' '>=' '==' '!='
    def _translateHelper3(self, opType, intSignSensitive=True, floatOrder=True):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        if isinstance(operandType, IntType):
            if intSignSensitive:
                if operandType.isSigned:
                    function = "CreateICmpS%s" % opType
                else:
                    function = "CreateICmpU%s" % opType
            else:
                function = "CreateICmp%s" % opType
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            if floatOrder:
                function = "CreateFCmpO%s" % opType
            else:
                function = "CreateFCmpU%s" % opType
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(IntType(isSigned=False, size=1), resultName)
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        if self.operator == "=":
            rightResult = self.right.translate()
            self.left.setValue(rightResult)
            return rightResult
        elif self.operator == "+":
            return self._translateHelper1("Add")
        elif self.operator == "-":
            return self._translateHelper1("Sub")
        elif self.operator == "*":
            return self._translateHelper1("Mul")
        elif self.operator == "/":
            return self._translateHelper1("Div", intSignSensitive=True)
        elif self.operator == "%":
            return self._translateHelper1("Rem", intSignSensitive=True)
        elif self.operator == "|":
            return self._translateHelper2("Or")
        elif self.operator == "&":
            return self._translateHelper2("And")
        elif self.operator == "^":
            return self._translateHelper2("Xor")
        elif self.operator == "<<":
            return self._translateHelper2("Shl")
        elif self.operator == ">>":
            return self._translateHelper2("LShr")
        elif self.operator == "||":
            resultName = Temp.getTempName()
            leftResult = self.left.translate()
            if not isinstance(leftResult.type, IntType):
                leftResult = TypeCaster.castTo(IntType(), leftResult)
            zero = "zero_%d" % Temp.getTempId()
            CodeEmitter.appendLine("Value *%s = getImm%d(0);" % (zero, leftResult.type.size))
            leftBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (leftBoolValue, leftResult.value, zero))

            branch = BranchGenerator(leftBoolValue)
            branch.startCondition()
            branch.endCondition()

            branch.startTruePart()
            branch.endTruePart()

            branch.startFalsePart()
            rightResult = self.right.translate()
            if not isinstance(rightResult.type, IntType):
                rightResult = TypeCaster.castTo(IntType(), rightResult)
            rightBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (rightBoolValue, rightResult.value, zero))
            branch.endFalsePart()

            branch.startExitPart()
            resultType = IntType(isSigned=False, size=1)
            branch.addPhi(resultName, resultType.getIRType(), leftBoolValue, rightBoolValue)
            branch.endExitPart()
            return TranslationResult(resultType, resultName)
        elif self.operator == "&&":
            resultName = Temp.getTempName()
            leftResult = self.left.translate()
            if not isinstance(leftResult.type, IntType):
                leftResult = TypeCaster.castTo(IntType(), leftResult)
            zero = "zero_%d" % Temp.getTempId()
            CodeEmitter.appendLine("Value *%s = getImm%d(0);" % (zero, leftResult.type.size))
            leftBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (leftBoolValue, leftResult.value, zero))

            branch = BranchGenerator(leftBoolValue)
            branch.startCondition()
            branch.endCondition()

            branch.startTruePart()
            rightResult = self.right.translate()
            if not isinstance(rightResult.type, IntType):
                rightResult = TypeCaster.castTo(IntType(), rightResult)
            rightBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (rightBoolValue, rightResult.value, zero))
            branch.endTruePart()

            branch.startFalsePart()
            branch.endFalsePart()

            branch.startExitPart()
            resultType = IntType(isSigned=False, size=1)
            branch.addPhi(resultName, resultType.getIRType(), rightBoolValue, leftBoolValue)
            branch.endExitPart()
            return TranslationResult(resultType, resultName)
        elif self.operator == "<":
            return self._translateHelper3("LT")
        elif self.operator == ">":
            return self._translateHelper3("GT")
        elif self.operator == "<=":
            return self._translateHelper3("LE")
        elif self.operator == ">=":
            return self._translateHelper3("GE")
        elif self.operator == "==":
            return self._translateHelper3("EQ", intSignSensitive=False)
        elif self.operator == "!=":
            return self._translateHelper3("NE", intSignSensitive=False)
        elif self.operator == "+=":
            result = self._translateHelper1("Add")
            self.left.setValue(result)
        elif self.operator == "-=":
            result = self._translateHelper1("Sub")
            self.left.setValue(result)
        elif self.operator == "*=":
            result = self._translateHelper1("Mul")
            self.left.setValue(result)
        elif self.operator == "/=":
            result = self._translateHelper1("Div", intSignSensitive=True)
            self.left.setValue(result)
        elif self.operator == "%=":
            result = self._translateHelper1("Rem", intSignSensitive=True)
            self.left.setValue(result)
        elif self.operator == "<<=":
            result = self._translateHelper2("Shl")
            self.left.setValue(result)
        elif self.operator == ">>=":
            result = self._translateHelper2("LShr")
            self.left.setValue(result)
        elif self.operator == "&=":
            result = self._translateHelper2("And")
            self.left.setValue(result)
        elif self.operator == "|=":
            result = self._translateHelper2("Or")
            self.left.setValue(result)
        elif self.operator == "^=":
            result = self._translateHelper2("Xor")
            self.left.setValue(result)
        else:
            raise UnhandledTranslationError

class UnaryOperandExpression(Expression):
    def __init__(self, operand, operator, isPrefix):
        self.operand = operand
        self.operator = operator
        self.isPrefix = isPrefix
    def __str__(self):
        s = "("
        if self.isPrefix:
            s += self.operator
            s += str(self.operand)
        else:
            s += str(self.operand)
            s += self.operator
        s += ")"
        return s
    # for '-'
    def _translateNeg(self):
        operandResult = self.operand.translate()
        operandType = operandResult.type
        resultName = Temp.getTempName()
        if isinstance(operandType, IntType):
            function = "CreateNeg"
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            function = "CreateFNeg"
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s);" % (resultName, function, operandResult.value))
        return TranslationResult(operandType, resultName)

    def _translateNot(self):
        operandResult = self.operand.translate()
        operandType = operandResult.type
        assert isinstance(operandType, IntType)
        resultName = Temp.getTempName()
        allOne = "allone_%d" % Temp.getTempId()
        typeName = operandType.getIRType()
        CodeEmitter.appendLine("Value *%s = Constant::getAllOnesValue(%s);" % (allOne, typeName))
        function = "CreateXor"
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, operandResult.value, allOne))
        return TranslationResult(operandType, resultName)

    def _translateLNot(self):
        operandResult = self.operand.translate()
        operandType = operandResult.type
        resultName = Temp.getTempName()
        zero = "zero_%d" % Temp.getTempId()
        if isinstance(operandType, IntType):
            function = "CreateICmpEQ"
            CodeEmitter.appendLine("Value *%s = getImm%s(0);" % (zero, operandType.size))
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            function = "CreateFCmpEQ"
            CodeEmitter.appendLine("Value *%s = translator::getFp(0.0);" % zero)
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" % (resultName, function, operandResult.value, zero))
        return TranslationResult(IntType(size=1, isSigned=False), resultName)
    # for '++', '--'
    def _translateHelper(self, opType):
        operandResult = self.operand.translate()
        operandType = operandResult.type
        one = "one_%d" % Temp.getTempId()
        resultName = Temp.getTempName()
        if isinstance(operandType, IntType):
            function = "Create%s" % opType
            CodeEmitter.appendLine("Value *%s = getImm%d(1);" % (one, operandType.size))
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            function = "CreateF%s" % opType
            CodeEmitter.appendLine("Value *%s = translator::getFp(1.0);" % (one))
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" % (resultName, function, operandResult.value, one))
        result = TranslationResult(operandType, resultName)
        self.operand.setValue(result)
        if self.isPrefix:
            return result
        else:
            return operandResult
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        if self.operator == "-":
            return self._translateNeg()
        elif self.operator == "+":
            return self.operand.translate()
        elif self.operator == '~':
            return self._translateNot()
        elif self.operator == "!":
            return self._translateLNot()
        elif self.operator == "++":
            return self._translateHelper("Add")
        elif self.operator == "--":
            return self._translateHelper("Sub")
        elif self.operator == "&":
            return self.operand.getPointer()
        elif self.operator == "*":
            operandResult = self.operand.translate()
            assert isinstance(operandResult.type, PointerType)
            resultType = operandResult.type.baseType
            resultName = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (resultName, operandResult.value, resultName))
            return TranslationResult(resultType, resultName)
        else:
            raise UnhandledTranslationError

class CastExpression(Expression):
    def __init__(self, targetType, originalExpression):
        self.targetType = targetType
        self.originalExpression = originalExpression
    def __str__(self):
        return "(%s)(%s)" % (str(self.targetType), str(self.originalExpression))
    def translate(self):
        originalResult = self.originalExpression.translate()
        return TypeCaster.castTo(self.targetType, originalExpression)

class ConditionalExpression(Expression):
    def __init__(self, condition, truePart, falsePart):
        self.condition = condition
        self.truePart = truePart
        self.falsePart = falsePart
    def __str__(self):
        return "(%s)?(%s):(%s)" % (str(self.condition), str(self.truePart), str(self.falsePart))
    def translate(self):
        branch = BranchGenerator(mayAppend=True)
        branch.startCondition()
        condResult = self.condition.translate()
        condResult = TypeCaster.castTo(IntType(False, 1), condResult)
        branch.setCondName(condResult.value)
        branch.endCondition()

        branch.startTruePart()
        trueResult = self.truePart.translate()
        branch.endTruePart()

        branch.startFalsePart()
        falseResult = self.falsePart.translate()
        branch.endFalsePart()

        compareResult = trueResult.type.compare(falseResult.type)
        if compareResult == TypeCompareResult.EQ:
            pass
        elif compareResult == TypeCompareResult.LT:
            branch.startAppendToTruePart()
            trueResult = TypeCaster.castTo(falseResult.type, trueResult)
            branch.endAppendToTruePart()
        elif compareResult == TypeCompareResult.GT:
            branch.startAppendToFalsePart()
            falseResult = TypeCaster.castTo(trueResult.type, falseResult)
            branch.endAppendToFalsePart()
        else:
            raise UnhandledTranslationError

        branch.startExitPart()
        resultName = Temp.getTempName()
        resultType = trueResult.type
        resultIRType = resultType.getIRType()
        branch.addPhi(resultName, resultIRType, trueResult.value, falseResult.value)
        return TranslationResult(resultType, resultName)

class FunctionCallExpression(Expression):
    def __init__(self, function, arguments):
        self.function = function #NOTE: function might be function pointer
        self.arguments = arguments
    def __str__(self):
        return "%s(%s)" %(str(self.function), str(self.arguments))
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        resultName = Temp.getTempName()
        if str(self.function) in ("findCarry", "findOverflow", "findNegative", "findZero"):
            width = self.arguments[0].value
            code = "Value *%s = Translator::%s(this, %s" % (resultName, str(self.function), width)
            for i in range(1, len(self.arguments)):
                argumentResult = self.arguments[i].translate()
                code += ", " + argumentResult.value
            code += ");"
            CodeEmitter.appendLine(code)
            return TranslationResult(IntType(), resultName)
        else:
            raise UnhandledTranslationError

class CommaExpression(Expression):
    def __init__(self, expressionList):
        self.expressionList = expressionList
    def __str__(self):
        s = "("
        for item in self.expressionList:
            s += str(item)
            s += ","
        s = s[:-1] + ")"
        return s
    def append(self, expression):
        self.expressionList.append(expression)
    def translate(self):
        for item in self.expressionList:
            result = item.translate()
        return result

class InstanceFieldAccessExpression(Expression):
    def __init__(self, instance, field):
        self.instance = instance
        self.field = field
    def __str__(self):
        return "(%s).%s" % (str(self.instance), str(self.field))
    def setValue(self, result):
        fieldPointerResult = self.getPointer()
        fieldType = fieldPointerResult.type.baseType
        newResult = TypeCaster.castTo(fieldType, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, fieldPointerResult.value))
    def getPointer(self):
        instancePointerResult = self.instance.getPointer()
        instanceType = instancePointerResult.type.baseType
        assert isinstance(instanceType, StructUnionBaseType)
        return instanceType.getFieldPointerByName(self.field.name, instancePointerResult.value)
    def translate(self):
        fieldPointerResult = self.getPointer()
        resultName = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (resultName, fieldPointerResult.value, resultName))
        return TranslationResult(fieldPointerResult.type.baseType, resultName)

class PointerFieldAccessExpression(Expression):
    def __init__(self, pointer, field):
        self.pointer = pointer
        self.field = field
    def __str__(self):
        return "(%s)->%s" % (str(self.pointer), str(self.field))
    def setValue(self, result):
        fieldPointerResult = self.getPointer()
        fieldType = fieldPointerResult.type.baseType
        newResult = TypeCaster.castTo(fieldType, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, fieldPointerResult.value))
    def getPointer(self):
        instancePointerResult = self.pointer.translate()
        instanceType = instancePointerResult.type.baseType
        assert isinstance(instanceType, StructUnionBaseType)
        return instanceType.getFieldPointerByName(self.field.name, instancePointerResult.value)
    def translate(self):
        fieldPointerResult = self.getPointer()
        resultName = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (resultName, fieldPointerResult.value, resultName))
        return TranslationResult(fieldPointerResult.type.baseType, resultName)

class ArrayAccessExpression(Expression):
    def __init__(self, base, index):
        self.base = base
        self.index = index
    def __str__(self):
        return "(%s)[%s]" % (str(self.base), str(self.index))
    def setValue(self, result):
        pointerResult = self.getPointer()
        newResult = TypeCaster.castTo(pointerResult.type.baseType, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, pointerResult.value))
    def getPointer(self):
        baseResult = self.base.translate()
        assert isinstance(baseResult.type, PointerType)
        indexResult = self.index.translate()
        if not isinstance(indexResult.type, IntType):
            indexResult = TypeCaster.castTo(IntType(), indexResult)
        resultName = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = builder->CreateInBoundsGEP(%s, %s);" % (baseResult.value, indexResult.value))
        return TranslationResult(baseResult.type, resultName)
    def translate(self):
        pointerResult = self.getPointer()
        resultType = pointerResult.type.baseType
        resultName = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s, \"%s\");" % (resultName, pointerResult.value, resultName))
        return TranslationResult(resultType, resultName)

class Constant(object):
    def __str__(self):
        return self.value
    def __repr__(self):
        return self.__str__()
    def translate(self):
        raise UnhandledTranslationError

class IntConstant(Constant):
    def __init__(self, value):
        value = value.lower()
        isSigned = True
        size = struct.calcsize("i")*8
        suffix = value[-3:]
        if 'll' in suffix:
            size = struct.calcsize("q")*8
        elif 'l' in suffix:
            size = struct.calcsize("l")*8
        if 'u' in suffix:
            isSigned = False
        self.value = value
        self.type = IntType(isSigned, size)
    def translate(self):
        name = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = getImm%d(%s);" % (name, self.type.size, self.value))
        return TranslationResult(self.type, name)

class FloatConstant(Constant):
    def __init__(self, value):
        self.type = FloatType()
        self.value = value
    def translate(self):
        name = Temp.getTempName()
        CodeEmitter.appendLine("Value *%s = translator::getFp(%s);" % (name, self.value))
        return TranslationResult(self.type, name)

class CharConstant(IntConstant):
    def __init__(self, value):
        self.type = IntType(size=8, isSigned=True)
        self.value = value

class StringConstant(Constant):
    def __init__(self, value):
        self.type = PointerType(IntType(size=8, isSigned=True))
        self.value = value

class Declarator(object): pass

class VariableDeclarator(Declarator):
    def __init__(self, variable=None, initializer=None):
        self.variable = variable
        self.initializer = initializer
    def __str__(self):
        s = ""
        if self.variable != None:
            s += str(self.variable.type)
            s += " "
            s += str(self.variable.name)
        if self.initializer != None:
            s += " = " + str(self.initializer)
        return s
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        if isinstance(self.variable.type, TypeIDType):
            self.variable.type = self.variable.type.getActualType()
        typeName = self.variable.type.getIRType()
        allocaName = "ptr_%s_%d" % (self.variable.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateAlloca(%s);" % (allocaName, typeName))
        var = NormalVariable(self.variable.name, self.variable.type, allocaName)
        variableTable.add(self.variable.name, var)
        if self.initializer != None:
            result = self.initializer.translate()
            var.setValue(result)

class TypeDeclarator(Declarator):
    def __init__(self, type=None):
        self.type = type
    def __str__(self):
        return str(self.type)
    def translate(self):
        CodeEmitter.appendLine("/*\n%s\n*/" % str(self))
        if isinstance(self.type, StructType) or isinstance(self.type, UnionType):
            if self.type.name != None:
                typeIDTable.add(self.type.getFullName(), self.type)
        else:
            raise UnhandledTranslationError

class Statement(object):
    def __repr__(self):
        return self.__str__()
    def translate(self):
        raise UnhandledTranslationError

class Declaration(Statement):
    def __init__(self, declarators):
        assert isinstance(declarators, list)
        self.declarators = declarators
    def __str__(self):
        s = ""
        if self.declarators != None:
            s = ",".join([str(declarator) for declarator in self.declarators])
            s += ";"
        return s
    def translate(self):
        if self.declarators != None:
            for declarator in self.declarators:
                declarator.translate()

class ExpressionStatement(Statement):
    def __init__(self, expression):
        self.expression = expression
    def __str__(self):
        return str(self.expression) + ";"
    def translate(self):
        self.expression.translate()
        return None

class IfStatement(Statement):
    def __init__(self, condition, truePart=None, falsePart=None):
        self.condition = condition
        self.truePart = truePart
        self.falsePart = falsePart
    def __str__(self):
        s = "if ("
        if self.condition != None:
            s += str(self.condition)
        else:
            s += "unknown"
        s += "){\n"
        if self.truePart != None:
            s += str(self.truePart)
        s += "\n}"
        if self.falsePart != None:
            s += "else{\n"
            s += str(self.falsePart)
            s += "\n}"
        return s
    def translate(self):
        CodeEmitter.appendLine("/*\n%s\n*/" % str(self))
        branch = BranchGenerator()

        branch.startCondition()
        conditionResult = self.condition.translate()
        conditionResult = TypeCaster.castTo(IntType(False, 1), conditionResult)
        branch.setCondName(conditionResult.value)
        branch.endCondition()

        branch.startTruePart()
        if self.truePart != None:
            self.truePart.translate()
        branch.endTruePart()

        branch.startFalsePart()
        if self.falsePart!= None:
            self.falsePart.translate()
        branch.endFalsePart()

        branch.startExitPart()
        branch.endExitPart()
        return None

class ForStatement(Statement):
    def __init__(self, preLoopPart=None, condition=None, postLoopBodyPart=None, loopBodyPart=None):
        self.preLoopPart = preLoopPart
        self.condition = condition
        self.postLoopBodyPart = postLoopBodyPart
        self.loopBodyPart = loopBodyPart
    def __str__(self):
        s = "for("
        if self.preLoopPart != None:
            s += str(self.preLoopPart)
        if not isinstance(self.preLoopPart, Declaration):
            s += ";"
        if self.condition != None:
            s += str(self.condition)
        s += ";"
        if self.postLoopBodyPart != None:
            s += str(self.postLoopBodyPart)
        s += "){\n"
        if self.loopBodyPart != None:
            s += str(self.loopBodyPart)
        s += "\n}"
        return s
    def translate(self):
        variableTable.push()
        typeIDTable.push()

        CodeEmitter.appendLine("/*\n%s\n*/" % str(self))

        if self.preLoopPart != None:
            self.preLoopPart.translate()

        loop = LoopGenerator(LoopType.FOR)
        loopOrSwitchStack.push(loop)
        loop.startCondition()
        if self.condition != None:
            conditionResult = self.condition.translate()
            conditionResult = TypeCaster.castTo(IntType(False, 1), conditionResult)
            loop.setCondName(conditionResult.value)
        else:
            one = "one_%d" % Temp.getTempId()
            CodeEmitter.appendLine("Value *%s = getImm1(1);" % one)
            loop.setCondName(one)
        loop.endCondition()

        loop.startLoopBody()
        if self.loopBodyPart != None:
            self.loopBodyPart.translate()
        loop.endLoopBody()

        loop.startPostLoopBodyPart()
        if self.postLoopBodyPart != None:
            self.postLoopBodyPart.translate()
        loop.endPostLoopBodyPart()

        loop.startExitPart()
        loop.endExitPart()
        loopOrSwitchStack.pop()

        variableTable.pop()
        typeIDTable.pop()
        return None

class WhileStatement(Statement):
    def __init__(self, condition, loopBodyPart):
        self.condition = condition
        self.loopBodyPart = loopBodyPart
    def __str__(self):
        return "while(%s){\n%s\n};" % (str(self.condition), str(self.loopBodyPart))
    def translate(self):
        variableTable.push()
        typeIDTable.push()

        CodeEmitter.appendLine("/*\n%s\n*/" % str(self))
        loop = LoopGenerator(LoopType.WHILE)
        loopOrSwitchStack.push(loop)

        assert self.condition != None
        loop.startCondition()
        conditionResult = self.condition.translate()
        conditionResult = TypeCaster.castTo(IntType(False, 1), conditionResult)
        loop.setCondName(conditionResult.value)
        loop.endCondition()

        loop.startLoopBody()
        if self.loopBodyPart != None:
            self.loopBodyPart.translate()
        loop.endLoopBody()

        loop.startExitPart()
        loop.endExitPart()
        loopOrSwitchStack.pop()

        variableTable.pop()
        typeIDTable.pop()
        return None

class DoWhileStatement(Statement):
    def __init__(self, condition, loopBodyPart):
        self.condition = condition
        self.loopBodyPart = loopBodyPart
    def __str__(self):
        return "do{\n%s\n}while(%s);" % (str(self.loopBodyPart), str(self.condition))
    def translate(self):
        variableTable.push()
        typeIDTable.push()

        CodeEmitter.appendLine("/*\n%s\n*/" % str(self))
        loop = LoopGenerator(LoopType.DO_WHILE)
        loopOrSwitchStack.push(loop)

        loop.startLoopBody()
        if self.loopBodyPart != None:
            self.loopBodyPart.translate()
        loop.endLoopBody()

        assert self.condition != None
        loop.startCondition()
        conditionResult = self.condition.translate()
        conditionResult = TypeCaster.castTo(IntType(False, 1), conditionResult)
        loop.setCondName(conditionResult.value)
        loop.endCondition()

        loop.startExitPart()
        loop.endExitPart()
        loopOrSwitchStack.pop()

        variableTable.pop()
        typeIDTable.pop()
        return None

# Note: caseBody is only the first statement of this 'case'
class CaseStatement(Statement):
    def __init__(self, case, caseBody=None):
        self.case = case
        self.caseBody = caseBody
    def __str__(self):
        return "case %s: %s" %(str(self.case), str(self.caseBody))
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        switch = loopOrSwitchStack.getInnermostSwitch()
        switch.addCase(self.case)
        if self.caseBody != None:
            self.caseBody.translate()

class DefaultStatement(Statement):
    def __init__(self, body=None):
        self.body = body
    def __str__(self):
        return "default: %s" % (str(self.body))
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        switch = loopOrSwitchStack.getInnermostSwitch()
        switch.addDefault()
        if self.body != None:
            self.body.translate()

class BreakStatement(Statement):
    def __str__(self):
        return "break;"
    def translate(self):
        CodeEmitter.appendLine("/* break */")
        loopOrSwitch = loopOrSwitchStack.top()
        loopOrSwitch.startBreak()
        loopOrSwitch.endBreak()

class ContinueStatement(Statement):
    def __str__(self):
        return "continue;"
    def translate(self):
        CodeEmitter.appendLine("/* continue */")
        loop = loopOrSwitchStack.getInnermostLoop()
        loop.startContinue()
        loop.endContinue()

class SwitchStatement(Statement):
    def __init__(self, control, bodyPart):
        self.control = control
        self.bodyPart = bodyPart
    def __str__(self):
        return "switch(%s) {\n%s\n}" % (str(self.control), str(self.bodyPart))
    def translate(self):
        assert self.control != None
        CodeEmitter.appendLine("/* %s */" % (str(self)))
        variableTable.push()
        typeIDTable.push()
        controlResult = self.control.translate()
        switch = SwitchGenerator(controlResult)
        loopOrSwitchStack.push(switch)
        switch.startSwtich()
        if self.bodyPart != None:
            self.bodyPart.translate()
        switch.endSwitch()
        loopOrSwitchStack.pop()
        variableTable.pop()
        typeIDTable.pop()

class CompoundStatement(Statement):
    def __init__(self, statements=None):
        self.statements = statements
    def __str__(self):
        s = "{\n"
        if self.statements != None:
            assert isinstance(self.statements, list)
            for item in self.statements:
                s += str(item)
                s += "\n"
        s += "\n}"
        return s
    def translate(self):
        if self.statements != None:
            assert isinstance(self.statements, list)
            variableTable.push()
            typeIDTable.push()
            for item in self.statements:
                item.translate()
            variableTable.pop()
            typeIDTable.pop()
        return None

predefinedTypeID = {
    "uint8_t":IntType(False, 8),
    "uint16_t":IntType(False, 16),
    "uint32_t":IntType(False, 32),
    "uint64_t":IntType(False, 64),
    "int8_t":IntType(True, 8),
    "int16_t":IntType(True, 16),
    "int32_t":IntType(True, 32),
    "int64_t":IntType(True, 64),
    "Twin64_t":Twin64Type(),
    }

predefinedValues = {
    "Rd": Operand("Rd", IntType(True, 64)),
    "Rm": Operand("Rm", IntType(True, 64)),
    "Rn": Operand("Rn", IntType(True, 64)),
    "SHIFT": IntConstantVariable("SHIFT", IntType(True, 64)),
    "IMM6": IntConstantVariable("IMM6", IntType(True, 64))
    }

class DictStack(list):
    def push(self, item=None):
        if item != None:
            self.append(item)
        else:
            self.append({})
    def top(self):
        return self[-1]
    def get(self, name):
        for d in self[::-1]:
            try:
                val = d[name]
                return val
            except KeyError:
                pass
        return None
    def add(self, name, val):
        assert len(self) > 0
        self[-1][name] = val
    def has(self, name):
        if self.get(name) != None:
            return True
        else:
            return False

typeIDTable = DictStack()
typeIDTable.push(predefinedTypeID)

# This table is only used to identify TYPEID during lexing and parsing.
tempTypeIDTable = DictStack()
tempTypeIDTable.push(predefinedTypeID)
tempTypeIDTable.push()

variableTable = DictStack()
variableTable.push(predefinedValues)

# The stack will save the loops or swtiches being translated.
# This stack is used while translating 'continue', 'break' and 'case'
class LoopOrSwitchStack(list):
    def push(self, item):
        assert isinstance(item, LoopGenerator) or isinstance(item, SwitchGenerator)
        self.append(item)
    def top(self):
        return self[-1]
    def getInnermostLoop(self):
        for i in range(len(loopOrSwitchStack)-1, -1, -1):
            loop = loopOrSwitchStack[i]
            if isinstance(loop, LoopGenerator):
                return loop
        else:
            raise UnhandledTranslationError
    def getInnermostSwitch(self):
        for i in range(len(loopOrSwitchStack)-1, -1, -1):
            switch = loopOrSwitchStack[i]
            if isinstance(switch, SwitchGenerator):
                return switch
        else:
            raise UnhandledTranslationError

loopOrSwitchStack = LoopOrSwitchStack() 

debug = True

class Translator(object):
    @classmethod
    def translate(cls, source):
        tempTypeIDTable = DictStack()
        tempTypeIDTable.push(predefinedTypeID)
        tempTypeIDTable.push()

        CodeEmitter.init()
        source = preprocess(source)
        if debug:
            pdb.set_trace()
        parseResult = cparse.parser.parse(source, debug=debug, lexer=clex.lexer)
        parseResult.translate()
        return CodeEmitter.getCode()
    @classmethod
    def addBitfield(cls, bitfield):
        global predefinedValues
        predefinedValues[bitfield] = IntConstantVariable(bitfield, IntType(True, 64))
    @classmethod
    def addOperand(cls, operandName, operandCType):
        global predefinedValues
        global predefinedTypeID
        if operandCType in predefinedTypeID.keys():
            operandType = predefinedTypeID[operandCType]
        elif operandCType == 'float':
            operandType = FloatType()
        elif operandCType == "double":
            operandType = DoubleType()
        else:
            raise UnhandledTranslationError
        predefinedValues[operandName] = Operand(operandName, operandType)
