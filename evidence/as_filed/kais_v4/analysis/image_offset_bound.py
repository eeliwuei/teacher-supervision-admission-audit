"""Upper bound, per image, of the offset between the stock adapter mapping and the corrected mapping
for ANY coordinate inside the image (hence for any teacher box), for rows the stock gate admitted.
Input: runtime_gate_rows_pass1_seed42.csv. No training outcome is read."""
import csv, math, sys, collections
def stock(h0,w0,h,w):
    r=min(w/max(w0,1.0),h/max(h0,1.0)); nw,nh=round(w0*r),round(h0*r)
    return r,r,float(int(round((w-nw)/2.0-0.1))),float(int(round((h-nh)/2.0-0.1)))
def fixed(h0,w0,h,w):
    imgsz=int(max(h,w)); r=imgsz/max(h0,w0)
    if r!=1: nw,nh=min(math.ceil(w0*r),imgsz),min(math.ceil(h0*r),imgsz)
    else: nw,nh=w0,h0
    return nw/max(w0,1),nh/max(h0,1),float(int(round((w-nw)/2.0-0.1))),float(int(round((h-nh)/2.0-0.1)))
rows=list(csv.DictReader(open(sys.argv[1])))
adm=[r for r in rows if r['admitted']=='1']
bx=[];obs=[]
for r in adm:
    h0,w0=int(r['ori_h']),int(r['ori_w']); h,w=float(r['resized_h']),float(r['resized_w'])
    a=stock(h0,w0,h,w); b=fixed(h0,w0,h,w)
    ex=max(abs(a[2]-b[2]),abs(w0*(a[0]-b[0])+a[2]-b[2])); ey=max(abs(a[3]-b[3]),abs(h0*(a[1]-b[1])+a[3]-b[3]))
    bx.append(max(ex,ey))
    obs.append(max(abs(float(r[k])) for k in ('d_x1_px','d_y1_px','d_x2_px','d_y2_px')))
n=len(adm); print('admitted rows',n,'resized shapes',collections.Counter((r['resized_h'],r['resized_w']) for r in adm).most_common(3))
print('image-level bound: max %.4f  rows>0.01: %d  >0.25: %d  >0.5: %d'%(max(bx),sum(v>0.01 for v in bx),sum(v>0.25 for v in bx),sum(v>0.5 for v in bx)))
print('observed matched-box offset: max %.4f  rows>0.01: %d  >0.25: %d'%(max(obs),sum(v>0.01 for v in obs),sum(v>0.25 for v in obs)))
print('rows where observed > bound+1e-3:',sum(o>b+1e-3 for o,b in zip(obs,bx)))
