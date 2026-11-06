"""Audita exportaciones IEEE aportadas sin redistribuir sus abstracts íntegros."""
from pathlib import Path
import argparse,csv,hashlib,json,re

def parse_exports(paths):
    unique={};files=[];occurrences=0
    for path in sorted(map(Path,paths),key=lambda p:p.name):
        raw=path.read_bytes();text=raw.decode('utf-8-sig')
        blocks=[s.strip() for s in re.split(r'\n\s*\n',text) if s.strip()]
        assert all('Abstract:' in block for block in blocks),path.name
        files.append(dict(file=path.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),records=len(blocks)))
        for number,block in enumerate(blocks,1):
            citation,body=block.split('Abstract:',1)
            abstract=re.split(r'\bkeywords\s*:',body,flags=re.I)[0].strip()
            title=re.search(r'"(.*?)"',citation,re.S)
            title=title.group(1).rstrip(', ') if title else citation.strip()
            doi=re.search(r'doi:\s*(10\.\d+/\S+)',citation,re.I)
            doi=doi.group(1).rstrip('.,') if doi else ''
            years=re.findall(r'\b(?:19|20)\d{2}\b',citation)
            key=doi.casefold() or re.sub(r'\W+','',title.casefold())
            occurrences+=1
            if key in unique:
                unique[key]['source_records']+=';'+path.name+'#'+str(number)
                continue
            unique[key]=dict(record_id=f'IEEE{len(unique)+1:03d}',year=years[-1] if years else '',
                title=title,doi=doi,url='https://doi.org/'+doi if doi else '',citation=citation.strip(),
                source_records=path.name+'#'+str(number),
                abstract_sha256=hashlib.sha256(abstract.encode()).hexdigest(),abstract_characters=len(abstract))
    return list(unique.values()),dict(files=files,exported_records=occurrences,unique_records=len(unique),
        duplicates_removed=occurrences-len(unique),search_strings_provided=False,
        source='Cinco exportaciones IEEE Xplore proporcionadas por el usuario; no consulta nueva a la plataforma.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('files',nargs='+',type=Path)
    parser.add_argument('--output',type=Path,default=Path('literature/ieee_abstracts_2026-11-06'))
    args=parser.parse_args();records,manifest=parse_exports(args.files)
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'records.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');writer.writeheader();writer.writerows(records)
    (args.output/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},ensure_ascii=False))

if __name__=='__main__':main()
