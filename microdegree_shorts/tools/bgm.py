# 잔잔한 로파이 피아노 BGM (절차적 합성, 저작권 문제 없음)
import numpy as np, wave, sys
SR=44100; DUR=30.5; bpm=84; beat=60/bpm
t=np.arange(int(SR*DUR))/SR; out=np.zeros_like(t)
def note(f,start,length,amp):
    n=int(length*SR); s=int(start*SR)
    if s>=len(out): return
    tt=np.arange(min(n,len(out)-s))/SR
    env=np.exp(-tt*2.2)*(1-np.exp(-tt*80))
    w=(np.sin(2*np.pi*f*tt)+0.35*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*4)+0.12*np.sin(2*np.pi*3*f*tt)*np.exp(-tt*6))
    out[s:s+len(tt)]+=amp*env*w*(1+0.003*np.sin(2*np.pi*5*tt))
m=lambda k:440*2**((k-69)/12)
# Fmaj7 - Em7 - Dm7 - G7sus / C
prog=[[53,57,60,64],[52,55,59,62],[50,53,57,60],[55,60,62,65]]
bar=4*beat; i=0; st=0.0
while st<DUR:
    ch=prog[i%4]
    note(m(ch[0]-12),st,bar*1.2,0.22)
    for k,b in enumerate([0,1.5,2,3]):
        for nn in ch[1:]:
            note(m(nn),st+b*beat+0.012*k,beat*2.5,0.07 if b else 0.09)
    mel=[ch[3]+12,ch[2]+12,ch[1]+12,ch[2]+12]
    for k,b in enumerate([0.5,1.5,2.5,3.5]):
        if (i+k)%3!=2: note(m(mel[k]),st+b*beat,beat*1.5,0.05)
    st+=bar; i+=1
# 부드러운 브러시 하이햇
rng=np.random.default_rng(1); hh=np.zeros_like(t)
for b in np.arange(0.5,DUR/beat,1.0):
    s=int(b*beat*SR); n=int(0.08*SR)
    if s+n<len(hh): hh[s:s+n]+=rng.normal(0,1,n)*np.exp(-np.arange(n)/SR*60)*0.02
hh=np.diff(hh,prepend=0)
out=out+hh
# 간단한 리버브(피드백 딜레이)
for d,g in [(0.031,0.3),(0.047,0.25),(0.089,0.2),(0.13,0.15)]:
    k=int(d*SR); out[k:]+=g*out[:-k]
out/=np.abs(out).max()*1.05
L=int(SR*DUR); fade=np.ones(L); fi=int(0.8*SR); fo=int(1.5*SR)
fade[:fi]=np.linspace(0,1,fi); fade[-fo:]=np.linspace(1,0,fo); out*=fade
with wave.open(sys.argv[1],'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())
