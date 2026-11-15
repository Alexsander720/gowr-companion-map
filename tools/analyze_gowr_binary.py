"""Offline PE64 evidence inventory. Standard library only; never executes the target.

RIP patterns are deliberately labelled candidates, not a full x64 disassembly.
Exception-directory function boundaries connect string references to globals.
Nearby register displacements are field hypotheses, never verified layouts.
"""
from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import re
import struct
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import USER, find_game_dir
DEFAULT_EXE = (find_game_dir() or USER / 'missing-game') / 'GoWR.exe'
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = USER / 'probe/gowr_pointer_candidates.json'
KEYWORDS = re.compile(r'camera|player|hero|kratos|world.?pos|listener|photo.?mode|map.?menu|realm|telemetry|mover|render.?view|view.?matrix|santamonica|goActor|goWorld', re.I)


class PE:
    def __init__(self, data):
        self.data = data
        if data[:2] != b'MZ':
            raise ValueError('not MZ')
        nt = struct.unpack_from('<I', data, 0x3c)[0]
        if data[nt:nt+4] != b'PE\0\0':
            raise ValueError('not PE')
        machine, count, self.timestamp = struct.unpack_from('<HHI', data, nt+4)
        size = struct.unpack_from('<H', data, nt+20)[0]
        opt = nt+24
        if machine != 0x8664 or struct.unpack_from('<H', data, opt)[0] != 0x20b:
            raise ValueError('requires x64 PE32+')
        self.image_base = struct.unpack_from('<Q', data, opt+24)[0]
        self.image_size = struct.unpack_from('<I', data, opt+56)[0]
        self.sections = []
        for i in range(count):
            at = opt+size+40*i
            name = data[at:at+8].rstrip(b'\0').decode('ascii')
            vs, va, raw_size, raw = struct.unpack_from('<IIII', data, at+8)
            flags = struct.unpack_from('<I', data, at+36)[0]
            if raw + raw_size > len(data):
                raise ValueError('truncated section')
            self.sections.append(dict(name=name,rva=va,virtual_size=vs,raw_offset=raw,raw_size=raw_size,flags=flags))
        self.functions = []
        ex_rva, ex_size = struct.unpack_from('<II', data, opt+112+3*8)
        ex = self.bytes_at(ex_rva,ex_size)
        for at in range(0,len(ex)-11,12):
            start,end,unwind = struct.unpack_from('<III',ex,at)
            if start < end <= self.image_size:
                self.functions.append((start,end,unwind))
        self.functions.sort()
        self.starts = [f[0] for f in self.functions]
        self._function_set=set(self.functions)
        self._primary={}
        self.families=collections.defaultdict(list)
        for function in self.functions:
            self.families[self.primary_function(function)[0]].append(function)

    def section_at(self, rva):
        return next((s for s in self.sections if s['rva'] <= rva < s['rva']+max(s['virtual_size'],s['raw_size'])),None)

    def bytes_at(self,rva,size):
        s=self.section_at(rva)
        if not s or rva-s['rva']+size > s['raw_size']:
            return b''
        at=s['raw_offset']+rva-s['rva']
        return self.data[at:at+size]

    def function_at(self,rva):
        i=bisect.bisect_right(self.starts,rva)-1
        return self.functions[i] if i>=0 and rva < self.functions[i][1] else None

    def primary_function(self,function):
        """Follow UNW_FLAG_CHAININFO, validating parent RUNTIME_FUNCTION entries."""
        if function is None:return None
        if function in self._primary:return self._primary[function]
        seen=[];current=function
        for _ in range(32):
            if current in seen:break
            seen.append(current)
            raw=self.bytes_at(current[2],4)
            if len(raw)!=4 or raw[0]&7 not in (1,2) or not (raw[0]>>3)&4:break
            chain_at=current[2]+4+((raw[2]+1)//2)*4
            chain=self.bytes_at(chain_at,12)
            if len(chain)!=12:break
            parent=struct.unpack('<III',chain)
            if parent not in self._function_set:break
            current=parent
        for item in seen:self._primary[item]=current
        return current

    def function_code(self,rva,max_bytes=4096):
        """Return contiguous chained function fragments without stitching addresses."""
        function=self.function_at(rva)
        if function is None:return rva,b''
        primary=self.primary_function(function)
        parts=self.families[primary[0]]
        start=parts[0][0];end=parts[0][1]
        for part in parts[1:]:
            gap=part[0]-end
            if gap<0 or gap>16 or part[1]-start>max_bytes:break
            if gap and any(b not in (0x90,0xcc) for b in self.bytes_at(end,gap)):break
            end=part[1]
        return start,self.bytes_at(start,min(end-start,max_bytes))


def rip_refs(code, base):
    # REX.W + MOV load/store or LEA; mod=00,r/m=101, no SIB.
    for m in re.finditer(rb'[\x48-\x4f][\x8b\x8d\x89][\x05\x0d\x15\x1d\x25\x2d\x35\x3d]',code):
        i=m.start()
        if i+7>len(code):
            continue
        disp=struct.unpack_from('<i',code,i+3)[0]
        yield dict(instruction_rva=base+i,target_rva=base+i+7+disp,
                   operation={0x8b:'mov_load',0x89:'mov_store',0x8d:'lea'}[code[i+1]],
                   register=((code[i+2]>>3)&7)+ (8 if code[i]&4 else 0),
                   bytes=code[i:i+7].hex())


def strings(pe):
    result=[]
    for s in pe.sections:
        if s['name'] not in ('.rdata','.data','_RDATA'):
            continue
        data=pe.bytes_at(s['rva'],s['raw_size'])
        for pattern,encoding in [(rb'[\x20-\x7e]{4,}', 'ascii'),(rb'(?:[\x20-\x7e]\x00){4,}','utf-16le')]:
            for m in re.finditer(pattern,data):
                value=m.group().decode(encoding)
                if KEYWORDS.search(value):
                    result.append(dict(rva=s['rva']+m.start(),length=len(m.group()),text=value[:500],section=s['name'],encoding=encoding,rtti=value.startswith(('.?AV','.?AU'))))
    return sorted(result,key=lambda x:x['rva'])


def rtti_vtables(pe,labels):
    """MSVC x64 TypeDescriptor -> self-validated COL -> vftable[-1]."""
    types={s['rva']-16:s for s in labels if s['rtti']}
    cols={};tables=[]
    for s in pe.sections:
        if s['name'] not in ('.rdata','_RDATA'):continue
        raw=pe.bytes_at(s['rva'],s['raw_size'])
        for off in range(0,len(raw)-23,4):
            if raw[off:off+4]!=b'\x01\0\0\0':continue
            sig,offset,cd,td,ch,self_rva=struct.unpack_from('<6I',raw,off)
            if td in types and self_rva==s['rva']+off and offset<0x100000 and cd<0x100000:
                cols[self_rva]=dict(col_rva=self_rva,type_descriptor_rva=td,text=types[td]['text'],base_offset=offset)
    for s in pe.sections:
        if s['name'] not in ('.rdata','_RDATA'):continue
        raw=pe.bytes_at(s['rva'],s['raw_size'])
        for off in range(0,len(raw)-7,8):
            va=struct.unpack_from('<Q',raw,off)[0]
            if va-pe.image_base in cols:
                tables.append(dict(cols[va-pe.image_base],vtable_rva=s['rva']+off+8))
    return tables


def camera_getter_seed(pe,vtables):
    """Derive camera transform from two named RTTI eval methods, fail closed.

    This recognizes a deliberately narrow instruction sequence: MOV RCX,global;
    MOV RBX,RAX; CALL accessor; accessor LEA RAX,[RCX+disp32]; RET;
    MOVUPS XMM0,[RAX+disp8]. Orbit-forward also subtracts it from zero.
    """
    found={}
    for label in ('GetCameraPosition','GetCameraOrbitForward'):
        t=next((t for t in vtables if t['text']==f'.?AV{label}@@'),None)
        if not t: return None
        ptr=pe.bytes_at(t['vtable_rva']+8,8)
        if len(ptr)!=8:return None
        method=struct.unpack('<Q',ptr)[0]-pe.image_base
        method,code=pe.function_code(method,2048)
        if not code:return None
        for m in re.finditer(rb'\x48\x8b\x0d....\x48\x8b\xd8\xe8....',code,re.S):
            at=m.start();rva=method+at
            root=rva+7+struct.unpack_from('<i',code,at+3)[0]
            accessor=rva+15+struct.unpack_from('<i',code,at+11)[0]
            access=pe.bytes_at(accessor,8)
            if len(access)!=8 or access[:3]!=b'\x48\x8d\x81' or access[-1]!=0xc3:continue
            add=struct.unpack_from('<i',access,3)[0]
            rest=code[at+15:at+48]
            field=re.search(rb'\x0f\x10\x40(.)',rest,re.S)
            if not field:continue
            offset=field.group(1)[0]
            negative=b'\x0f\x57\xc9' in rest and b'\x0f\x5c\xc8' in rest
            found[label]=dict(rva=root,chain=[add],offset=offset,negative=negative,
                              evidence=dict(vtable_rva=t['vtable_rva'],method_rva=method,
                                            load_rva=rva,accessor_rva=accessor,
                                            accessor_bytes=access.hex(),getter_bytes=code[at:at+48].hex()))
    if len(found)!=2:return None
    pos=found['GetCameraPosition'];fw=found['GetCameraOrbitForward']
    if pos['rva']!=fw['rva'] or pos['chain']!=fw['chain'] or not fw['negative']:return None
    return dict(rva=pos['rva'],chain=pos['chain'],position_offset=pos['offset'],forward_offset=fw['offset'],forward_sign=-1,
                role='camera_not_kratos',status='statically_derived_not_live_verified',
                evidence={k:v['evidence'] for k,v in found.items()})


def player_context_seed(pe,vtables):
    t=next((t for t in vtables if t['text']=='.?AVGetPlayerSpeed@@'),None)
    if not t:return None
    method=struct.unpack('<Q',pe.bytes_at(t['vtable_rva']+8,8))[0]-pe.image_base
    method,code=pe.function_code(method)
    if not code:return None
    for ref in rip_refs(code,method):
        if ref['operation']!='mov_load' or ref['register']!=0:continue
        off=ref['instruction_rva']-method
        # MOV RSI,[RAX+8], followed by virtual velocity getter in same method.
        after=code[off+7:off+23]
        m=re.search(rb'\x48\x8b\x70(.)',after,re.S)
        if not m or b'\x4c\x8b\x41\x38' not in code:continue
        return dict(rva=ref['target_rva'],chain=[m.group(1)[0],0],role='player_context_not_yet_position',
                    status='statically_derived_not_live_verified',
                    evidence=dict(vtable_rva=t['vtable_rva'],method_rva=method,load_rva=ref['instruction_rva'],
                                  load_and_member_bytes=code[off:off+23].hex(),velocity_virtual_slot=0x38),
                    note='GetPlayerSpeed obtains a player-associated context through global->member. XYZ field is not statically established.')
    return None


def player_position_recipe(pe,vtables):
    """Prove the same local-point/frame expression in two named player methods.

    XYZ is *not* just context+0x50: GetPlayerLocation transforms a homogeneous
    local point by a parent-frame matrix. Retain that distinction for live reads.
    """
    sites={};recipes=[]
    for label,slot in [('GetPlayerLocation',0x40),('GetDistanceToPlayer',8)]:
        table=next((t for t in vtables if t['text']==f'.?AV{label}@@'),None)
        if not table:return None
        raw=pe.bytes_at(table['vtable_rva']+slot,8)
        if len(raw)!=8:return None
        method=struct.unpack('<Q',raw)[0]-pe.image_base
        start,code=pe.function_code(method)
        for ref in rip_refs(code,start):
            if ref['operation']!='mov_load' or ref['register']!=0:continue
            at=ref['instruction_rva']-start;tail=code[at+7:at+176]
            context=re.search(rb'\x48\x8b\x78(.)',tail,re.S)
            parent=re.search(rb'\x48\x8b\x5f(.)',tail,re.S)
            frame=re.search(rb'\x48\x8d\x8b(.{4})\xe8(.{4})\x0f\x10\x57(.)',tail,re.S)
            if not context or not parent or not frame or not context.start()<parent.start()<frame.start():continue
            helper=ref['instruction_rva']+7+frame.start()+12+struct.unpack('<i',frame.group(2))[0]
            item=(ref['target_rva'],context.group(1)[0],parent.group(1)[0],struct.unpack('<i',frame.group(1))[0],frame.group(3)[0],helper)
            sites[label]=dict(vtable_rva=table['vtable_rva'],virtual_slot=slot,method_rva=method,
                              load_rva=ref['instruction_rva'],point_load_rva=ref['instruction_rva']+7+frame.start()+12,
                              expression_bytes=code[at:at+7+frame.end()].hex())
            recipes.append(item);break
    if len(recipes)!=2 or recipes[0]!=recipes[1]:return None
    root,context,parent,frame_offset,point_offset,helper=recipes[0]
    helper_start,body=pe.function_code(helper)
    kind=re.search(rb'\x8b\x81(.{4})\x83\xf8\x02',body,re.S)
    parent_test=re.search(rb'\x48\x83\xb9(.{4})\x00',body,re.S)
    other_parent=re.search(rb'\x48\x8b\x81(.{4})\x48\x85\xc0',body,re.S)
    other_flag=re.search(rb'\xf6\x80(.{4})\x01',body,re.S)
    # Five consecutive 16-byte loads: revision stamp then four cached matrix rows.
    cached=re.search(rb'\x0f\x10\x41(.)\x45\x33\xff\x8b\xc7\x0f\x10\x49(.)',body,re.S)
    if not all((kind,parent_test,other_parent,other_flag,cached)):return None
    stamp_offset=cached.group(1)[0];matrix_offset=cached.group(2)[0]
    if matrix_offset!=stamp_offset+16:return None
    for pattern in (b'\x0f\x10\x41'+bytes([matrix_offset+16]),b'\x0f\x10\x49'+bytes([matrix_offset+32]),b'\x0f\x10\x81'+struct.pack('<I',matrix_offset+48)):
        if pattern not in body:return None
    # The helper compares cached revision HIGH against own/ancestor change LOW,
    # under distinct frame and ancestor locks. Recover those exact fields too.
    freshness_patterns={
        'frame_lock_offset':rb'\xf0\x0f\xb1\xb9(.{4})\x74',
        'ancestor_stamp_offset':rb'\x0f\x10\x91(.{4})\x8b\xc7',
        'ancestor_next_offset':rb'\x48\x8b\x89(.{4})\x48\x85\xc9',
        'ancestor_flags_offset':rb'\x8b\x81(.{4})\xc1\xe8\x1d',
        'ancestor_byte_flags_offset':rb'\xf6\x81(.{4})\x08',
        'ancestor_lock_offset':rb'\x33\xc0\xf0\x0f\xb1\xb9(.{4})\x74',
    }
    matches={name:re.search(pattern,body,re.S) for name,pattern in freshness_patterns.items()}
    if not all(matches.values()):return None
    # Select ancestor-lock occurrence after the ancestor flag test, not frame prologue.
    ancestor_begin=matches['ancestor_flags_offset'].start()
    ancestor_lock=re.search(freshness_patterns['ancestor_lock_offset'],body[ancestor_begin:],re.S)
    if not ancestor_lock or b'\x48\x39\x44\x24\x78' not in body or b'\x0f\x11\x44\x24\x70' not in body:return None
    freshness={name:struct.unpack('<i',m.group(1))[0] for name,m in matches.items()}
    freshness['ancestor_lock_offset']=struct.unpack('<i',ancestor_lock.group(1))[0]
    sites['frame_helper']=dict(method_rva=helper,fragment_count=len(pe.families[pe.primary_function(pe.function_at(helper))[0]]),
                               kind_test_rva=helper_start+kind.start(),cache_load_rva=helper_start+cached.start(),
                               cache_load_bytes=body[cached.start():cached.start()+49].hex())
    return dict(rva=root,chain=[context,0],position_offset=point_offset,role='player_world_via_frame',
                frame_chain=[context,parent,frame_offset],frame_matrix_offset=matrix_offset,frame_stamp_offset=stamp_offset,
                frame_kind_offset=struct.unpack('<i',kind.group(1))[0],frame_parent_offset=struct.unpack('<i',parent_test.group(1))[0],
                frame_other_parent_offset=struct.unpack('<i',other_parent.group(1))[0],frame_other_flag_offset=struct.unpack('<i',other_flag.group(1))[0],
                status='statically_derived_not_live_verified',evidence=sites,**freshness,
                note='World position = local point * parent frame. Cache HIGH revision must cover own/ancestor LOW revisions; reader never acquires engine locks.')


def field_hypotheses(pe,ref):
    code=pe.bytes_at(ref['instruction_rva']+7,72)
    result=set()
    # movss/movups/mov reg,[same base+disp8/32]; no dataflow/liveness claim.
    for m in re.finditer(rb'(?:[\x40-\x4f])?(?:\x0f[\x10\x28]|[\x8b\x8d])',code):
        i=m.end()
        if i>=len(code): continue
        modrm=code[i]; mod=modrm>>6; base=modrm&7
        if base != (ref['register']&7) or base==4: continue
        if mod==1 and i+2<=len(code): result.add(struct.unpack_from('<b',code,i+1)[0])
        if mod==2 and i+5<=len(code): result.add(struct.unpack_from('<i',code,i+1)[0])
    return sorted(x for x in result if 0<=x<=0x4000)


def analyze(path):
    data=path.read_bytes(); pe=PE(data)
    labels=strings(pe); starts=[s['rva'] for s in labels]
    vtables=rtti_vtables(pe,labels);table_map={t['vtable_rva']:t for t in vtables}
    camera_seed=camera_getter_seed(pe,vtables)
    player_seed=player_context_seed(pe,vtables)
    position_recipe=player_position_recipe(pe,vtables)
    text=next(s for s in pe.sections if s['name']=='.text')
    refs=list(rip_refs(pe.bytes_at(text['rva'],text['raw_size']),text['rva']))
    func_labels=collections.defaultdict(list)
    global_refs=collections.defaultdict(list)
    for ref in refs:
        fragment=pe.function_at(ref['instruction_rva'])
        f=pe.primary_function(fragment)
        ref['fragment_rva']=fragment[0] if fragment else None
        ref['function_rva']=f[0] if f else None
        j=bisect.bisect_right(starts,ref['target_rva'])-1
        if j>=0 and ref['target_rva']<labels[j]['rva']+labels[j]['length'] and f:
            func_labels[f[0]].append(dict(string_rva=labels[j]['rva'],text=labels[j]['text'],xref_rva=ref['instruction_rva']))
        if f and ref['target_rva'] in table_map:
            t=table_map[ref['target_rva']]
            func_labels[f[0]].append(dict(string_rva=t['type_descriptor_rva']+16,text=t['text'],xref_rva=ref['instruction_rva'],vtable_rva=t['vtable_rva']))
        section=pe.section_at(ref['target_rva'])
        if section and section['flags']&0x80000000 and ref['target_rva']%8==0:
            global_refs[ref['target_rva']].append(ref)
    candidates=[]
    for rva, uses in global_refs.items():
        evidence={}
        for ref in uses:
            for label in func_labels.get(ref['function_rva'],[]):
                evidence[(label['string_rva'],label['xref_rva'])]=label
        loads=sum(ref['operation']=='mov_load' for ref in uses)
        cookie_hits=sum(pe.bytes_at(ref['instruction_rva']+7,3)==b'\x48\x33\xc4' for ref in uses if ref['register']==0 and ref['operation']=='mov_load')
        score= min(len(uses),10)+(20 if loads else 0)
        unique_labels={label['text']:label for label in evidence.values()}
        registration=any(len(func_labels.get(ref['function_rva'],[]))>12 for ref in uses)
        for label in unique_labels.values():
            value=label['text'].lower()
            score+= 30 if any(t in value for t in ('primary listener','goheroa00','worldposition','heromover','cameramanager','viewmatrix')) else 8
            if any(t in value for t in ('mapmenu','photomode','telemetry')): score-=5
        # Many script/property names in one function usually describe registration,
        # not a runtime player instance. Keep evidence but demote that association.
        if registration:score=min(score,25)+(10 if loads else 0)
        if cookie_hits>=10:score=-100000
        if camera_seed and rva==camera_seed['rva']:score+=1000
        s=pe.section_at(rva)
        fields=sorted({off for ref in uses[:50] for off in field_hypotheses(pe,ref)})
        candidates.append(dict(rva=rva,rva_hex=hex(rva),score=score,section=s['name'],
                               storage='zero_fill' if rva-s['rva']>=s['raw_size'] else 'file_backed',
                               status='unverified_static_hypothesis',reference_count=len(uses),load_count=loads,
                               security_cookie_pattern_hits=cookie_hits,
                               registration_function=registration,references=uses[:12],
                               related_string_count=len(evidence),related_strings=list(evidence.values())[:24],field_offset_hypotheses=fields))
    candidates.sort(key=lambda c:(-c['score'],c['rva']))
    old=[]
    for rva in (0x03B3A420,0x03B6A528):
        s=pe.section_at(rva)
        old.append(dict(rva=hex(rva),section=s['name'] if s else None,storage='zero_fill' if s and rva-s['rva']>=s['raw_size'] else 'file_backed',references=global_refs.get(rva,[])))
    total=len(candidates);candidates=candidates[:4096]
    return dict(schema=1,binary=dict(path=str(path),size=len(data),timestamp=pe.timestamp,
                sha256=hashlib.sha256(data).hexdigest(),header_sha256=hashlib.sha256(data[:4096]).hexdigest(),image_base=pe.image_base,image_size=pe.image_size),
                sections=pe.sections,old_offsets=old,strings=labels,rtti_vtables=vtables,candidates=candidates,
                semantic_seeds=[s for s in (camera_seed,player_seed,position_recipe) if s],
                excluded_security_cookies=[dict(rva=hex(rva),reason='MSVC MOV RAX,global; XOR RAX,RSP',references=len(uses)) for rva,uses in global_refs.items() if sum(pe.bytes_at(ref['instruction_rva']+7,3)==b'\x48\x33\xc4' for ref in uses if ref['register']==0 and ref['operation']=='mov_load')>=10],
                statistics=dict(keyword_strings=len(labels),rtti_strings=sum(s['rtti'] for s in labels),rtti_vtables=len(vtables),rip_pattern_hits=len(refs),roots_total=total,roots_retained=len(candidates),exception_functions=len(pe.functions),primary_functions=len(pe.families)),
                limitations=['Pattern decoder is not an instruction-boundary disassembler: overlaps/immediates may produce false xrefs.',
                              'Function association uses PE exception ranges; missing/split functions and indirect references are not covered.',
                              'Shared function/string and nearby register displacement do not prove singleton type or field meaning.',
                              'Inventory retains top 4096 roots, 12 xrefs/24 related strings per root; old-offset xrefs are retained in full.',
                              'BSS cannot be inspected on disk. No live pointer or semantic identity is verified.'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,default=Path(DEFAULT_EXE));ap.add_argument('--out',type=Path,default=DEFAULT_OUT)
    args=ap.parse_args();result=analyze(args.exe)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(binary=result['binary'],statistics=result['statistics'],old_offsets=[dict(rva=x['rva'],section=x['section'],storage=x['storage'],xref_count=len(x['references'])) for x in result['old_offsets']],top=[dict(rva=x['rva_hex'],score=x['score'],strings=[s['text'] for s in x['related_strings'][:3]]) for x in result['candidates'][:12]],output=str(args.out)),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
