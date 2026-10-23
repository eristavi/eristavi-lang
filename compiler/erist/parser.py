from __future__ import annotations

from .diagnostics import ParseError
from .lexer import Token, TokenKind
from .syntax import *

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens=tokens; self.i=0
        self.known_type_names=set(); self.import_aliases=set()
        for j,t in enumerate(tokens[:-1]):
            if t.kind is TokenKind.TYPE and tokens[j+1].kind is TokenKind.IDENTIFIER:
                self.known_type_names.add(str(tokens[j+1].value))
            if t.kind is TokenKind.ERROR and (j==0 or tokens[j-1].kind is not TokenKind.ELSE) and tokens[j+1].kind is TokenKind.IDENTIFIER:
                self.known_type_names.add(str(tokens[j+1].value))
            if t.kind is TokenKind.IMPORT:
                k=j+1; last=None; alias=None
                while k<len(tokens) and tokens[k].kind is not TokenKind.SEMICOLON:
                    if tokens[k].kind is TokenKind.AS and k+1<len(tokens): alias=str(tokens[k+1].value); break
                    if tokens[k].kind is TokenKind.IDENTIFIER: last=str(tokens[k].value)
                    k+=1
                if alias or last: self.import_aliases.add(alias or last)
    def parse(self)->Program:
        out=[]
        while not self._check(TokenKind.EOF): out.append(self._statement())
        return Program(out)

    def _statement(self):
        if self._match(TokenKind.IMPORT): return self._import_decl(self._previous())
        if self._match(TokenKind.PUBLIC):
            loc=self._previous().location
            if self._match(TokenKind.FUNCTION): return self._function_decl(True,loc)
            if self._match(TokenKind.TYPE): return self._type_decl(True,loc)
            if self._match(TokenKind.ERROR): return self._error_decl(True,loc)
            raise ParseError("'public' must precede a function, type, or error declaration",self._current().location)
        if self._match(TokenKind.FUNCTION): return self._function_decl(False,self._previous().location)
        if self._match(TokenKind.TYPE): return self._type_decl(False,self._previous().location)
        if self._match(TokenKind.ERROR): return self._error_decl(False,self._previous().location)
        if self._match(TokenKind.RETURN): return self._return_stmt(self._previous())
        if self._match(TokenKind.FAIL): return self._fail_stmt(self._previous())
        if self._match(TokenKind.LET): return self._let_stmt(self._previous())
        if self._match(TokenKind.IF): return self._if_stmt(self._previous())
        if self._match(TokenKind.WHILE): return self._while_stmt(self._previous())
        if self._match(TokenKind.FOR): return self._for_stmt(self._previous())
        if self._match(TokenKind.WITH): return self._with_stmt(self._previous())
        expr=self._expression()
        if self._match(TokenKind.EQUAL):
            if not isinstance(expr,(NameExpr,MemberExpr,IndexExpr)):
                raise ParseError("left side of assignment must be a writable name/member/index path",expr.location)
            value=self._value_expression(); self._consume(TokenKind.SEMICOLON,"expected ';' after assignment")
            return AssignStmt(expr,value,expr.location)
        expr=self._handled_tail(expr)
        self._consume(TokenKind.SEMICOLON,"expected ';' after expression")
        return ExprStmt(expr,expr.location)

    def _import_decl(self,tok):
        path=self._qualified_identifier("expected module path after 'import'")
        alias=None
        if self._match(TokenKind.AS): alias=str(self._consume(TokenKind.IDENTIFIER,"expected alias after 'as'").value)
        self._consume(TokenKind.SEMICOLON,"expected ';' after import")
        return ImportDecl(path,alias,tok.location)

    def _function_decl(self,public,loc):
        name=self._consume(TokenKind.IDENTIFIER,"expected function name")
        self._consume(TokenKind.LPAREN,"expected '(' after function name")
        params=[]
        if not self._check(TokenKind.RPAREN):
            while True:
                p=self._consume(TokenKind.IDENTIFIER,"expected parameter name")
                tref=None
                if not self._check(TokenKind.COMMA) and not self._check(TokenKind.RPAREN): tref=self._type_ref()
                params.append(Parameter(str(p.value),tref,p.location))
                if not self._match(TokenKind.COMMA): break
        self._consume(TokenKind.RPAREN,"expected ')' after parameters")
        ret=None
        if self._match(TokenKind.RETURNS): ret=self._type_ref()
        fails=[]
        if self._match(TokenKind.FAILS):
            while True:
                fails.append(self._error_type_ref())
                if not self._match(TokenKind.COMMA): break
        ob=self._consume(TokenKind.LBRACE,"expected '{' before function body")
        return FunctionDecl(str(name.value),params,ret,fails,self._block(ob),loc,public)

    def _type_decl(self,public,loc):
        name=self._consume(TokenKind.IDENTIFIER,"expected type name")
        self._consume(TokenKind.LBRACE,"expected '{' after type name")
        fields=[]
        while not self._check(TokenKind.RBRACE):
            if self._check(TokenKind.EOF): raise ParseError("unterminated type declaration",loc)
            fixed=self._match(TokenKind.FIXED)
            f=self._consume(TokenKind.IDENTIFIER,"expected field name")
            tref=self._type_ref(); self._consume(TokenKind.SEMICOLON,"expected ';' after field declaration")
            fields.append(FieldDecl(str(f.value),tref,fixed,f.location))
        self._advance(); return TypeDecl(str(name.value),fields,loc,public)

    def _error_decl(self,public,loc):
        name=self._consume(TokenKind.IDENTIFIER,"expected error name")
        self._consume(TokenKind.LBRACE,"expected '{' after error name")
        fields=[]
        while not self._check(TokenKind.RBRACE):
            if self._check(TokenKind.EOF): raise ParseError("unterminated error declaration",loc)
            f=self._consume(TokenKind.IDENTIFIER,"expected error field name")
            tref=self._type_ref(); self._consume(TokenKind.SEMICOLON,"expected ';' after error field")
            fields.append(FieldDecl(str(f.value),tref,False,f.location))
        self._advance(); return ErrorDecl(str(name.value),fields,loc,public)

    def _return_stmt(self,tok):
        if self._match(TokenKind.SEMICOLON): return ReturnStmt(None,tok.location)
        val=self._value_expression(); self._consume(TokenKind.SEMICOLON,"expected ';' after return value"); return ReturnStmt(val,tok.location)
    def _fail_stmt(self,tok):
        val=self._expression(); self._consume(TokenKind.SEMICOLON,"expected ';' after failure value"); return FailStmt(val,tok.location)
    def _let_stmt(self,tok):
        fixed=self._match(TokenKind.FIXED); name=self._consume(TokenKind.IDENTIFIER,"expected binding name after 'let'")
        tref=None
        if not self._check(TokenKind.BE): tref=self._type_ref()
        self._consume(TokenKind.BE,"expected 'be' after binding declaration")
        val=self._value_expression(); self._consume(TokenKind.SEMICOLON,"expected ';' after binding declaration")
        return LetStmt(str(name.value),fixed,tref,val,tok.location)
    def _if_stmt(self,tok):
        cond=self._block_delimited_expression(); ob=self._consume(TokenKind.LBRACE,"expected '{' after if condition"); then=self._block(ob); other=None
        if self._match(TokenKind.ELSE): other=self._block(self._consume(TokenKind.LBRACE,"expected '{' after else"))
        return IfStmt(cond,then,other,tok.location)
    def _while_stmt(self,tok):
        cond=self._block_delimited_expression(); return WhileStmt(cond,self._block(self._consume(TokenKind.LBRACE,"expected '{' after while condition")),tok.location)
    def _for_stmt(self,tok):
        name=self._consume(TokenKind.IDENTIFIER,"expected loop binding after 'for'"); self._consume(TokenKind.IN,"expected 'in' after loop binding")
        iterable=self._block_delimited_expression(); body=self._block(self._consume(TokenKind.LBRACE,"expected '{' after for iterable")); return ForStmt(str(name.value),iterable,body,tok.location)
    def _with_stmt(self,tok):
        name=self._consume(TokenKind.IDENTIFIER,"expected resource binding after 'with'"); tref=None
        if not self._check(TokenKind.BE): tref=self._type_ref()
        self._consume(TokenKind.BE,"expected 'be' in with statement"); resource=self._expression(); body=self._block(self._consume(TokenKind.LBRACE,"expected '{' after resource expression"))
        return WithStmt(str(name.value),tref,resource,body,tok.location)
    def _block(self,ob):
        stmts=[]
        while not self._check(TokenKind.RBRACE):
            if self._check(TokenKind.EOF): raise ParseError("unterminated block; expected '}'",ob.location)
            stmts.append(self._statement())
        self._advance(); return Block(stmts,ob.location)

    def _type_ref(self):
        loc=self._current().location; maybe=self._match(TokenKind.MAYBE); identity=self._match(TokenKind.IDENTITY)
        if identity and self._check(TokenKind.MAYBE): raise ParseError("use 'maybe identity T', not 'identity maybe T'",self._current().location)
        path=self._qualified_identifier("expected type name")
        return TypeRef(path,maybe,identity,loc)
    def _error_type_ref(self):
        loc=self._current().location; path=self._qualified_identifier("expected checked error type")
        return TypeRef(path,False,False,loc)
    def _qualified_identifier(self,message):
        first=self._consume(TokenKind.IDENTIFIER,message); parts=[str(first.value)]
        while self._match(TokenKind.DOT): parts.append(str(self._consume(TokenKind.IDENTIFIER,"expected identifier after '.'").value))
        return tuple(parts)

    def _block_delimited_expression(self):
        return self._expression()

    def _value_expression(self): return self._handled_tail(self._expression())
    def _handled_tail(self,expr):
        handlers=[]
        while self._check(TokenKind.ELSE) and self._peek(1).kind is TokenKind.ERROR:
            e=self._advance(); self._advance(); tref=None
            if not self._check(TokenKind.LBRACE): tref=self._error_type_ref()
            block=self._block(self._consume(TokenKind.LBRACE,"expected '{' after else error handler"))
            handlers.append(ErrorHandler(tref,block,e.location))
        return HandledExpr(expr,handlers,expr.location) if handlers else expr

    def _expression(self): return self._or()
    def _or(self):
        expr=self._and()
        while self._match(TokenKind.OR):
            op=self._previous(); expr=BinaryExpr(expr,"or",self._and(),op.location)
        return expr
    def _and(self):
        expr=self._not()
        while self._match(TokenKind.AND):
            op=self._previous(); expr=BinaryExpr(expr,"and",self._not(),op.location)
        return expr
    def _not(self):
        if self._match(TokenKind.NOT):
            op=self._previous(); return UnaryExpr("not",self._not(),op.location)
        return self._comparison()
    def _comparison(self):
        expr=self._additive(); kinds={TokenKind.EQUAL_EQUAL:"==",TokenKind.BANG_EQUAL:"!=",TokenKind.LESS:"<",TokenKind.LESS_EQUAL:"<=",TokenKind.GREATER:">",TokenKind.GREATER_EQUAL:">="}
        if self._current().kind in kinds:
            op=self._advance(); expr=BinaryExpr(expr,kinds[op.kind],self._additive(),op.location)
            if self._current().kind in kinds: raise ParseError("comparison chaining is not part of pre-0.1; use 'and' explicitly",self._current().location)
        return expr
    def _additive(self):
        expr=self._multiplicative()
        while self._current().kind in (TokenKind.PLUS,TokenKind.MINUS):
            op=self._advance(); expr=BinaryExpr(expr,"+" if op.kind is TokenKind.PLUS else "-",self._multiplicative(),op.location)
        return expr
    def _multiplicative(self):
        expr=self._prefix(); sy={TokenKind.STAR:"*",TokenKind.SLASH:"/",TokenKind.PERCENT:"%"}
        while self._current().kind in sy:
            op=self._advance(); expr=BinaryExpr(expr,sy[op.kind],self._prefix(),op.location)
        return expr
    def _prefix(self):
        if self._match(TokenKind.MINUS):
            op=self._previous(); return UnaryExpr("-",self._prefix(),op.location)
        if self._match(TokenKind.TRY):
            op=self._previous(); return TryExpr(self._prefix(),op.location)
        if self._match(TokenKind.IDENTITY):
            op=self._previous(); return IdentityExpr(self._prefix(),op.location)
        return self._postfix()
    def _postfix(self):
        expr=self._primary()
        while True:
            if self._check(TokenKind.LBRACE):
                path=self._expr_qualified_path(expr)
                if path is not None and (path[0] in self.known_type_names or path[0] in self.import_aliases):
                    expr=self._construction(path,expr.location); continue
            if self._match(TokenKind.LPAREN):
                loc=self._previous().location; args=[]
                if not self._check(TokenKind.RPAREN):
                    while True:
                        args.append(self._expression())
                        if not self._match(TokenKind.COMMA): break
                self._consume(TokenKind.RPAREN,"expected ')' after arguments"); expr=CallExpr(expr,args,loc); continue
            if self._match(TokenKind.DOT):
                name=self._consume(TokenKind.IDENTIFIER,"expected member name after '.'"); expr=MemberExpr(expr,str(name.value),name.location); continue
            if self._match(TokenKind.LBRACKET):
                loc=self._previous().location; idx=self._expression(); self._consume(TokenKind.RBRACKET,"expected ']' after index"); expr=IndexExpr(expr,idx,loc); continue
            break
        return expr
    def _construction(self,path,loc):
        self._consume(TokenKind.LBRACE,"expected '{' for construction"); fields=[]
        while not self._check(TokenKind.RBRACE):
            if self._check(TokenKind.EOF): raise ParseError("unterminated construction",loc)
            name=self._consume(TokenKind.IDENTIFIER,"expected field name in construction"); self._consume(TokenKind.EQUAL,"expected '=' after field name")
            value=self._expression(); self._consume(TokenKind.SEMICOLON,"expected ';' after field initializer"); fields.append(FieldInit(str(name.value),value,name.location))
        self._advance(); return ConstructionExpr(path,fields,loc)
    def _expr_qualified_path(self,expr):
        parts=[]; cur=expr
        while isinstance(cur,MemberExpr): parts.append(cur.name); cur=cur.base
        if not isinstance(cur,NameExpr): return None
        parts.append(cur.name); return tuple(reversed(parts))
    def _primary(self):
        if self._match(TokenKind.INTEGER): t=self._previous(); return LiteralExpr(t.value,"Int",t.location)
        if self._match(TokenKind.FLOAT): t=self._previous(); return LiteralExpr(t.value,"Float",t.location)
        if self._match(TokenKind.TEXT): t=self._previous(); return LiteralExpr(t.value,"Text",t.location)
        if self._match(TokenKind.TRUE): t=self._previous(); return LiteralExpr(True,"Bool",t.location)
        if self._match(TokenKind.FALSE): t=self._previous(); return LiteralExpr(False,"Bool",t.location)
        if self._match(TokenKind.NONE): return NoneExpr(self._previous().location)
        if self._match(TokenKind.LBRACKET):
            loc=self._previous().location; elems=[]
            if not self._check(TokenKind.RBRACKET):
                while True:
                    elems.append(self._expression())
                    if not self._match(TokenKind.COMMA): break
            self._consume(TokenKind.RBRACKET,"expected ']' after List literal"); return ListExpr(elems,loc)
        if self._match(TokenKind.IDENTIFIER): t=self._previous(); return NameExpr(str(t.value),t.location)
        if self._match(TokenKind.ERROR): t=self._previous(); return NameExpr("error",t.location)
        if self._match(TokenKind.LPAREN):
            e=self._expression()
            self._consume(TokenKind.RPAREN,"expected ')' after grouped expression"); return e
        raise ParseError(f"expected expression, found {self._current().lexeme!r}",self._current().location)

    def _current(self): return self.tokens[self.i]
    def _peek(self,off): return self.tokens[min(self.i+off,len(self.tokens)-1)]
    def _previous(self): return self.tokens[self.i-1]
    def _advance(self):
        t=self._current()
        if t.kind is not TokenKind.EOF: self.i+=1
        return t
    def _check(self,k): return self._current().kind is k
    def _match(self,*ks):
        if self._current().kind in ks: self._advance(); return True
        return False
    def _consume(self,k,msg):
        if self._check(k): return self._advance()
        raise ParseError(msg,self._current().location)
