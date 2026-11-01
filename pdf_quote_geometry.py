"""Source-exact PDF quote geometry. No Meta calls, no invented OCR boxes."""
from __future__ import annotations
import fitz
import unicodedata

def fold(s):
    return "".join(c.lower() for c in unicodedata.normalize("NFKC",s) if c.isalnum())

def boxes(rects,page):
    if not rects or len(rects)>16:return None
    bounds=page.rect; w,h=bounds.width,bounds.height
    if w<=0 or h<=0:return None
    output=[]
    for source in rects:
        r=fitz.Rect(source)&bounds
        if r.is_empty or r.width<=0 or r.height<=0:return None
        vals=[r.x0/w,r.y0/h,r.width/w,r.height/h]
        if any(v<0 or v>1 for v in vals):return None
        output.append(dict(x0=round(r.x0,2),y0=round(r.y0,2),
                           x1=round(r.x1,2),y1=round(r.y1,2),
                           norm_x=round(vals[0],6),norm_y=round(vals[1],6),
                           norm_w=round(vals[2],6),norm_h=round(vals[3],6)))
    return output

def locate_quote_geometry(page,quote,is_ocr_page=False):
    out=dict(match_method="unlocated",char_span=None,
             page_dimensions={"width":round(page.rect.width,2),"height":round(page.rect.height,2)},
             bounding_boxes=None)
    if is_ocr_page:
        out["match_method"]="ocr_page_level_only";return out
    if not isinstance(quote,str) or not quote.strip() or len(quote)>2000:return out
    quote=quote.strip(); text=page.get_text("text",sort=True); target=fold(quote)
    if len(target)<6 or target not in fold(text):
        out["match_method"]="page_verified_no_bbox";return out
    at=text.find(quote)
    if at>=0:out["char_span"]=[at,at+len(quote)]
    direct=boxes(page.search_for(quote),page)
    if direct:out.update(match_method="pymupdf_search_for",bounding_boxes=direct);return out
    # Word-boundary safe normalized text search across any line wraps.
    words=page.get_text("words",sort=True)[:2000]
    seq=[(fold(str(w[4])),i) for i,w in enumerate(words)]
    seq=[x for x in seq if x[0]]
    corpus="".join(x[0] for x in seq)
    starts={};ends={};cursor=0
    for i,(token,_) in enumerate(seq):
        starts[cursor]=i;cursor+=len(token);ends[cursor]=i
    matches=[];at=corpus.find(target)
    while at>=0:
        end=at+len(target)
        if at in starts and end in ends:matches.append((starts[at],ends[end]))
        if len(matches)>1:break
        at=corpus.find(target,at+1)
    if len(matches)!=1:
        out["match_method"]="page_verified_no_bbox";return out
    i,j=matches[0];line_rects={}
    for token,k in seq[i:j+1]:
        w=words[k];key=(w[5],w[6]);r=fitz.Rect(w[:4])
        line_rects[key]=(line_rects[key]|r) if key in line_rects else r
    rects=boxes(list(line_rects.values()),page)
    if rects:out.update(match_method="normalized_word_span",bounding_boxes=rects)
    else:out["match_method"]="page_verified_no_bbox"
    return out
