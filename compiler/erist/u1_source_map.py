"""Private U1 diagnostic-map ingress/remapping; never execution authority.

No public UIR format is frozen here. Source revisions use owned logical names
and SHA-256, independent of checkout paths and the producer's local IDs.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Mapping

MAX_MAP_BYTES=16*1024*1024
MAX_RECORDS=1048576

@dataclass(frozen=True)
class Source:
    name:str
    digest:str
    length:int

    def excerpt(self,content:bytes,start:int,end:int)->str:
        if len(content)!=self.length or hashlib.sha256(content).hexdigest()!=self.digest:
            raise ValueError('stale source revision: excerpt refused')
        if not 0<=start<=end<=self.length:raise ValueError('source span out of bounds')
        return content[start:end].decode('utf-8')

@dataclass(frozen=True)
class Location:
    source:Source
    start:int
    end:int
    anchor:int
    line:int
    column:int
    reason:int
    parents:tuple[tuple[int,int],...]

@dataclass(frozen=True)
class SourceMap:
    sources:tuple[Source,...]
    locations:tuple[Location,...]

    @classmethod
    def decode(cls,data:bytes,expected:Mapping[str,tuple[str,int]])->SourceMap:
        if len(data)>MAX_MAP_BYTES:raise ValueError('source map byte quota')
        # Reject duplicate keys and non-integral JSON values before any remap.
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('duplicate map key')
                result[key]=value
            return result
        raw=json.loads(data,object_pairs_hook=unique)
        if not isinstance(raw,dict) or set(raw)!={'schema','native_contract','sources','bytes','locations','origins'}:
            raise ValueError('invalid private source map schema')
        if type(raw['schema']) is not int or raw['schema']!=1 or type(raw['native_contract']) is not int or raw['native_contract']!=1:
            raise ValueError('stale source map or native contract')
        def table(name,width):
            values=raw[name]
            if not isinstance(values,list) or len(values)>MAX_RECORDS or len(values)%width or any(type(v) is not int or not -(1<<63)<=v<(1<<63) for v in values):
                raise ValueError('invalid bounded source map table')
            return [tuple(values[i:i+width]) for i in range(0,len(values),width)]
        sources,locations,origins=table('sources',4),table('locations',7),table('origins',3)
        bytes_table=table('bytes',1)
        if any(not 0<=row[0]<=255 for row in bytes_table):raise ValueError('invalid source identity bytes')
        storage=bytes(row[0] for row in bytes_table)
        decoded=[];names=set();cursor=0
        for start,count,digest_start,length in sources:
            if start!=cursor or count<1 or digest_start!=start+count or digest_start>len(storage)-64 or length<0:
                raise ValueError('invalid source identity ranges')
            name=storage[start:start+count].decode('utf-8')
            digest=storage[digest_start:digest_start+64].decode('ascii')
            if any(c not in '0123456789abcdef' for c in digest) or name in names:
                raise ValueError('invalid or duplicate source revision')
            if expected.get(name)!=(digest,length):raise ValueError('stale or unknown source revision')
            decoded.append(Source(name,digest,length));names.add(name);cursor=digest_start+64
        if cursor!=len(storage):raise ValueError('unclaimed source map identity bytes')
        extra=[[] for _ in locations];previous=0;seen=set()
        for child,parent,role in origins:
            if not previous<=child<=len(locations) or not 1<=parent<child or not 1<=role<=4 or (child,parent,role) in seen:
                raise ValueError('invalid ordered acyclic origin set')
            extra[child-1].append((parent,role));previous=child;seen.add((child,parent,role))
        result=[]
        for index,(source,start,end,anchor,line,column,encoded) in enumerate(locations,1):
            if not 1<=source<=len(decoded) or not 0<=start<=anchor<=end<=decoded[source-1].length or min(line,column)<1 or encoded<0:
                raise ValueError('invalid source location')
            reason,parent=divmod(encoded,1048577)
            parents=[]
            if encoded:
                if not 1<=reason<=4 or not 0<=parent<index or (not parent and reason!=1):
                    raise ValueError('cyclic or unsupported primary origin')
                if parent:
                    old=locations[parent-1]
                    if (source,start,end,anchor,line,column)!=old[:6]:raise ValueError('changed original diagnostic anchor')
                    parents.append((parent,0))
            parents.extend(extra[index-1])
            result.append(Location(decoded[source-1],start,end,anchor,line,column,reason,tuple(parents)))
        return cls(tuple(decoded),tuple(result))

    def remap(self,existing:Mapping[Source,int],start:int=1)->tuple[Mapping[Source,int],tuple[int,...]]:
        if type(start) is not int or not 1<=start<=MAX_RECORDS:raise ValueError('invalid source remap start')
        mapped=dict(existing)
        if any(type(value) is not int or not 1<=value<=MAX_RECORDS for value in mapped.values()) or len(set(mapped.values()))!=len(mapped):
            raise ValueError('invalid destination source IDs')
        used=set(mapped.values());next_id=start;ids=[]
        for source in self.sources:
            if source not in mapped:
                while next_id in used:next_id+=1
                if next_id>MAX_RECORDS:raise ValueError('source remap ID quota')
                mapped[source]=next_id;used.add(next_id)
            ids.append(mapped[source])
        return MappingProxyType(mapped),tuple(ids)
