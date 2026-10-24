"""Normalize Stage-0 AST into the documented eristavi-ast-v1 report schema."""
from compiler.erist import syntax as s
from compiler.erist.lexer import Lexer, TokenKind
from compiler.erist.parser import Parser


def reference_tree(source):
    tokens = Lexer(source).lex()
    program = Parser(tokens).parse()
    by_location = {(t.location.line, t.location.column): t for t in tokens}

    def node(kind, obj, text='', extra=0, flag=False, first=(), second=(), third=()):
        location = obj.location
        return [kind, text, extra, flag, location.line, location.column,
                list(first), list(second), list(third)]

    def optional(value):
        return [] if value is None else [convert(value)]

    def convert(value):
        if isinstance(value, s.TypeRef):
            return node(17, value, '.'.join(value.path), int(value.maybe)+2*int(value.identity))
        if isinstance(value, s.ImportDecl):
            # Alias locations are lexical metadata; reconstruct their token.
            alias = []
            if value.alias:
                start = next(i for i,t in enumerate(tokens) if t.location == value.location)
                end = next(i for i in range(start,len(tokens)) if tokens[i].kind is TokenKind.AS)
                alias = [node(32, tokens[end+1], value.alias)]
            return node(1,value,'.'.join(value.path),first=alias)
        if isinstance(value,s.FunctionDecl):
            failures = [convert(t) for t in value.fails]
            for failure in failures:
                failure[3] = True
            return node(2,value,value.name,flag=value.public,
                        first=[convert(p) for p in value.parameters]+failures,
                        second=optional(value.return_type),third=[convert(value.body)])
        if isinstance(value,s.Parameter):
            return node(3,value,value.name,first=optional(value.type_annotation))
        if isinstance(value,(s.TypeDecl,s.ErrorDecl)):
            return node(4 if isinstance(value,s.TypeDecl) else 5,value,value.name,
                        flag=value.public,first=[convert(f) for f in value.fields])
        if isinstance(value,s.FieldDecl):
            return node(6,value,value.name,flag=value.fixed,first=[convert(value.type_ref)])
        if isinstance(value,s.Block):
            return node(7,value,first=[convert(t) for t in value.statements])
        if isinstance(value,s.ReturnStmt):
            return node(8,value,first=optional(value.value))
        if isinstance(value,s.FailStmt):
            return node(9,value,first=[convert(value.value)])
        if isinstance(value,s.LetStmt):
            return node(10,value,value.name,flag=value.fixed,first=optional(value.type_annotation),second=[convert(value.initializer)])
        if isinstance(value,s.IfStmt):
            return node(11,value,first=[convert(value.condition)],second=[convert(value.then_branch)],third=optional(value.else_branch))
        if isinstance(value,s.WhileStmt):
            return node(12,value,first=[convert(value.condition)],second=[convert(value.body)])
        if isinstance(value,s.ForStmt):
            return node(13,value,value.name,first=[convert(value.iterable)],second=[convert(value.body)])
        if isinstance(value,s.WithStmt):
            return node(14,value,value.name,first=optional(value.type_annotation),second=[convert(value.resource)],third=[convert(value.body)])
        if isinstance(value,s.AssignStmt):
            return node(15,value,first=[convert(value.target)],second=[convert(value.value)])
        if isinstance(value,s.ExprStmt):
            return node(16,value,first=[convert(value.expression)])
        if isinstance(value,s.ErrorHandler):
            return node(18,value,first=optional(value.type_ref),second=[convert(value.block)])
        if isinstance(value,s.HandledExpr):
            return node(19,value,first=[convert(value.value)],second=[convert(h) for h in value.handlers])
        if isinstance(value,s.BinaryExpr):
            return node(20,value,value.operator,first=[convert(value.left)],second=[convert(value.right)])
        if isinstance(value,s.UnaryExpr):
            return node(21,value,value.operator,first=[convert(value.operand)])
        if isinstance(value,(s.TryExpr,s.IdentityExpr)):
            return node(22 if isinstance(value,s.TryExpr) else 23,value,first=[convert(value.value)])
        if isinstance(value,s.CallExpr):
            return node(24,value,first=[convert(value.callee)],second=[convert(a) for a in value.arguments])
        if isinstance(value,s.MemberExpr):
            return node(25,value,value.name,first=[convert(value.base)])
        if isinstance(value,s.IndexExpr):
            return node(26,value,first=[convert(value.base)],second=[convert(value.index)])
        if isinstance(value,s.ConstructionExpr):
            return node(27,value,'.'.join(value.type_path),first=[convert(f) for f in value.fields])
        if isinstance(value,s.FieldInit):
            return node(28,value,value.name,first=[convert(value.value)])
        if isinstance(value,s.LiteralExpr):
            token = by_location[(value.location.line,value.location.column)]
            text = value.value if value.type_name == 'Text' else token.lexeme
            return node(29,value,text,token.kind.value-1,flag=value.value is True)
        if isinstance(value,s.NoneExpr):
            return node(30,value)
        if isinstance(value,s.ListExpr):
            return node(31,value,first=[convert(e) for e in value.elements])
        if isinstance(value,s.NameExpr):
            return node(32,value,value.name)
        raise AssertionError(type(value))

    return node(0,tokens[-1],first=[convert(statement) for statement in program.statements])
