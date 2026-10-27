"""Engine laboratory analysis and reproducible figures; raw measurements are supplied separately."""
from pathlib import Path
import re,json,csv,math
import argparse
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.integrate import quad
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser = argparse.ArgumentParser(description="Recalculate the supplied engine experiment and draw all report figures.")
parser.add_argument("--data-dir", type=Path, required=True, help="Folder containing engine lab.xlsx and engine lab111.XML")
parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
args = parser.parse_args()
DATA = args.data_dir
O = args.output_dir
for filename in ["engine lab.xlsx", "engine lab111.XML"]:
 if not (DATA / filename).is_file():
  parser.error(f"Missing input: {DATA / filename}")
O.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.size':12,'font.family':'DejaVu Sans','text.color':'black','axes.labelcolor':'black','axes.titlecolor':'black','axes.spines.top':False,'axes.spines.right':False,'figure.dpi':180,'savefig.dpi':300})
from zipfile import ZipFile
z=ZipFile(DATA/'engine lab.xlsx');ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
ss=[''.join(n.itertext()) for n in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
rows=[]
for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:sheetData/s:row',ns):
 vals=[]
 for c in row:
  v=c.find('s:v',ns);value=v.text if v is not None else '';vals.append((c.get('r'),ss[int(value)] if c.get('t')=='s' else value))
 rows.append(vals)
data=[]
for row in rows[4:]:
 d={re.sub(r'\d','',k):v for k,v in row}; data.append({k:pd.to_numeric(v,errors='coerce') for k,v in d.items()})
df=pd.DataFrame(data);assert len(df)==104
Vd=math.pi/4*.069**2*.062;Vc=Vd/21
rho=df.M*100/(287*(df.J+273.15));df['ma']=.6*math.pi/4*(df.N/1000)**2*np.sqrt(2*rho*df.L.abs())
df['Pb']=2*math.pi*df.Q*df.P.abs()/60;df['bmep']=120*df.Pb/(df.Q.replace(0,np.nan)*Vd)/1e5
df['ev']=df.ma/(rho*Vd*df.Q.replace(0,np.nan)/120)*100
df['mf']=df.B*1e-6/60*df.D;df['afr']=df.ma/df.mf;df['bsfc']=df.mf*3.6e6/df.Pb;df['eta']=df.Pb/(df.mf*df.E*1e6)*100
# Exclude adjustment and shutdown from representative means; retain every raw sample in the CSV.
windows=[(20,60),(100,140),(180,192)];summ=[]
for lo,hi in windows:
 x=df[(df.A>=lo)&(df.A<=hi)];d={k:float(x[k].mean()) for k in ['Q','P','Pb','R','K','J','L','M','ma','bmep','ev','B','mf','afr','bsfc','eta']};d.update(lo=lo,hi=hi,n=len(x),Nmin=float(x.Q.min()),Nmax=float(x.Q.max()),Tmin=float(x.K.min()),Tmax=float(x.K.max()),Pmin=float(x.P.min()),Pmax=float(x.P.max()));summ.append(d)
rename={'A':'time_s','B':'fuel_mL_min','C':'software_fuel_kg_s','D':'fuel_density_setting_kg_m3','E':'LHV_setting_MJ_kg','F':'software_fuel_power_W','G':'software_exhaust_enthalpy_W','H':'software_inlet_enthalpy_W','I':'software_exhaust_loss_W','J':'ambient_C','K':'exhaust_C','L':'airbox_differential_Pa','M':'ambient_mbar','N':'orifice_mm','O':'software_air_g_s','P':'torque_Nm','Q':'speed_rpm','R':'software_power_W','S':'calorimeter_T1_C','T':'calorimeter_T2_C','U':'calorimeter_T3_C','V':'calorimeter_T4_C','W':'water_L_min','X':'software_AFR','Y':'software_BSFC','Z':'software_eff_percent','AA':'software_vol_eff_percent','AB':'capacity_setting_cc','AC':'stroke_setting','AD':'software_BMEP_bar'}
df.rename(columns=rename).to_csv(O/'Engine_recalculated_data.csv',index=False)
fig,ax=plt.subplots(3,1,figsize=(7.2,6.5),sharex=True)
for a,col,label in zip(ax,['Q','P','K'],['Speed (rpm)','Torque (N m)','Exhaust temperature (°C)']):
 a.plot(df.A,df[col],lw=1.6);a.set_ylabel(label);a.grid(alpha=.2)
 for lo,hi in windows:a.axvspan(lo,hi,color='#399681',alpha=.13)
ax[-1].set_xlabel('Elapsed time (s)');fig.tight_layout();fig.savefig(O/'engine_history.png');fig.savefig(O/'engine_history.pdf');plt.close(fig)
fig,ax=plt.subplots(3,2,figsize=(8.0,6.0));N=[s['Q'] for s in summ]
for a,k,label in zip(ax.flat,['P','Pb','K','bmep','ma','ev'],['Torque (N m)','Brake power (W)','Exhaust temperature (°C)','BMEP (bar)','Air mass flow (kg/s)','Volumetric efficiency (%)']):
 a.plot(N,[s[k] for s in summ],'o-',color='#222222');a.set_xlabel('Speed (rpm)');a.set_ylabel(label);a.grid(alpha=.2)
fig.tight_layout();fig.savefig(O/'engine_performance.png');fig.savefig(O/'engine_performance.pdf');plt.close(fig)
root=ET.parse(DATA/'engine lab111.XML').getroot();cycles=[]
for i,c in enumerate(root.findall('.//Cycle')):
 a=np.array([[float(x.findtext(k)) for k in ['Angle','Volume','Pressure','Voltage']] for x in c.findall('.//Reading')]);n=float(c.findtext('CycleParameters/Speed'));angle=np.arange(len(a))-180;t=np.arange(len(a))/(6*n)
 cycles.append(dict(a=a,n=n,angle=angle,t=t,clipped=int(sum(a[:,2]==-30)),pmax=float(a[:,2].max()),imep=float(c.findtext('CycleParameters/IMEP')),ip=float(c.findtext('CycleParameters/IndicatedPower'))))
 with open(O/f'Engine_ECA_cycle_{i+1}.csv','w') as f:
  writer=csv.writer(f);writer.writerow(['unwrapped_angle_deg','relative_time_s','exported_angle_deg','volume_cm3','pressure_exported','voltage']);writer.writerows(zip(angle,t,*a.T))
fig,ax=plt.subplots(1,3,figsize=(10,3.4))
for i,c in enumerate(cycles):
 for a,x in zip(ax,[c['angle'],c['t']*1000,c['a'][:,1]]):a.plot(x,c['a'][:,2],lw=.8,alpha=.7,label=str(i+1))
for a,xlabel in zip(ax,['Crank angle (deg)','Relative time (ms)','Cylinder volume (cm³)']):a.set_xlabel(xlabel);a.set_ylabel('Pressure (nominal bar)');a.grid(alpha=.2)
ax[0].legend(title='Cycle',fontsize=10);fig.tight_layout();fig.savefig(O/'engine_pressure.png');fig.savefig(O/'engine_pressure.pdf');plt.close(fig)
# Cycle model: 79/21 ideal N2/O2 air surrogate. Same R and gamma for the constant-cp baseline.
R=8.314462618/(.79*.0280134+.21*.0319988)/1000;gamma=1.4;cv=R/(gamma-1);cp=cv+R;r=22
coeffN=[[28.98641,1.853978,-9.647459,16.63537,.000117],[19.50583,19.88705,-8.598535,1.369784,.527601],[35.51872,1.128728,-.196103,.014662,-4.553760]]
coeffO=[[31.32234,-20.23531,57.86644,-36.50624,-.007374],[30.03235,8.772972,-3.988133,.788313,-.741599],[20.91111,10.72071,-2.020498,.146449,9.245722]]
M=.79*28.0134+.21*31.9988
# Integrate piecewise across NIST coefficient boundaries rather than through discontinuities.
def cpv(T):
 t=T/1000
 def val(c):return c[0]+c[1]*t+c[2]*t*t+c[3]*t**3+c[4]/t**2
 return (.79*val(coeffN[0 if T<500 else 1 if T<2000 else 2])+.21*val(coeffO[0 if T<700 else 1 if T<2000 else 2]))/M
def integ(a,b,kind):
 if a==b:return 0.
 if b<a:return -integ(b,a,kind)
 pts=[a]+[x for x in [500,700,2000] if a<x<b]+[b]
 return sum(quad(lambda T:(cpv(T)-R if kind in ['u','sv'] else cpv(T))/(T if kind in ['s','sv'] else 1),x,y,epsabs=1e-8)[0] for x,y in zip(pts[:-1],pts[1:]))
def isent(Ta,va,vb,var):
 if not var:return Ta*(va/vb)**(gamma-1)
 return brentq(lambda Tb:integ(Ta,Tb,'sv')+R*np.log(vb/va),100,6000)
def cycle(kind,T1,p1,q,var=False,f=.5):
 v1=R*T1/p1;v2=v1/r;T2=isent(T1,v1,v2,var);p2=R*T2/v2
 def heat(Ta,dq,atv):return brentq(lambda Tb:integ(Ta,Tb,'u' if atv else 'h')-dq,Ta,5999) if var else Ta+dq/(cv if atv else cp)
 if kind=='Otto':T3=heat(T2,q,True);states=[(T1,p1,v1),(T2,p2,v2),(T3,R*T3/v2,v2)];modes=['s','v'];endv=v2
 elif kind=='Diesel':T3=heat(T2,q,False);endv=R*T3/p2;states=[(T1,p1,v1),(T2,p2,v2),(T3,p2,endv)];modes=['s','p']
 else:
  T3=heat(T2,f*q,True);p3=R*T3/v2;T4=heat(T3,(1-f)*q,False);endv=R*T4/p3;states=[(T1,p1,v1),(T2,p2,v2),(T3,p3,v2),(T4,p3,endv)];modes=['s','v','p']
 assert endv<v1
 Te=isent(states[-1][0],endv,v1,var);states.append((Te,R*Te/v1,v1));modes+=['s','v'];qout=integ(T1,Te,'u') if var else cv*(Te-T1);w=q-qout
 assert 0<w<q
 return dict(states=states,modes=modes,q=q,w=w,eta=w/q,rc=endv/v2,rp=states[2][1]/p2)
models=[]
for j,s in enumerate(summ):
 T=s['J']+273.15;p=s['M']/10;mass=p*(Vd+Vc)/(R*T);target=s['Pb']*120/s['Q']/mass/1000
 for kind in ['Otto','Diesel','Dual']:
  q=brentq(lambda q:cycle(kind,T,p,q)['w']-target,.01,1800)
  for var in [False,True]:
   c=cycle(kind,T,p,q,var);c.update(window=j,kind=kind,var=var,mass=mass,power=c['w']*1000*mass*s['Q']/120,mean_pressure=c['w']*1000*mass/Vd/1e5);models.append(c)
  assert abs(models[-2]['power']-s['Pb'])<1e-6
# Curves and independent p-dV checks for all models.
def curves(c):
 st=c['states'];out=[];s0=0.
 for i,mode in enumerate(c['modes']):
  Ta,pa,va=st[i];Tb,pb,vb=st[(i+1)%len(st)]
  if mode=='s':v=np.geomspace(va,vb,80);T=np.array([isent(Ta,va,x,c['var']) for x in v]);p=R*T/v;s=np.full(80,s0)
  elif mode=='v':T=np.linspace(Ta,Tb,80);v=np.full(80,va);p=R*T/v;s=s0+np.array([integ(Ta,x,'sv') if c['var'] else cv*np.log(x/Ta) for x in T])
  else:T=np.linspace(Ta,Tb,80);p=np.full(80,pa);v=R*T/p;s=s0+np.array([integ(Ta,x,'s') if c['var'] else cp*np.log(x/Ta) for x in T])
  s0=s[-1];out.append((T,p,v,s))
 assert abs(s0)<1e-6
 work=sum(np.trapezoid(p,v) for T,p,v,s in out);assert abs(work-c['w'])/c['w']<.002
 return out
for c in models:curves(c)
for kind in ['Otto','Diesel','Dual']:
 fig,ax=plt.subplots(1,2,figsize=(8.4,3.4));colors=['#222222','#386cb0','#b45f06']
 for c in [x for x in models if x['kind']==kind and not x['var']]:
  for i,(T,p,v,s) in enumerate(curves(c)):
   ax[0].plot(v*c['mass']*1e6,p/100,color=colors[c['window']],label=f"{summ[c['window']]['Q']:.0f} rpm" if i==0 else None);ax[1].plot(s,T,color=colors[c['window']])
 # Label representative states only, leaving overlays legible.
 c=[x for x in models if x['kind']==kind and x['window']==0 and not x['var']][0];cs=curves(c)
 for i,((T,p,v),curve) in enumerate(zip(c['states'],cs)):
  ax[0].annotate(str(i+1),(v*c['mass']*1e6,p/100),xytext=(3,4),textcoords='offset points',fontsize=11);ax[1].annotate(str(i+1),(curve[3][0],T),xytext=(3,4),textcoords='offset points',fontsize=11)
 ax[0].set(xlabel='Cylinder volume (cm³)',ylabel='Absolute pressure (bar)');ax[1].set(xlabel='s − s₁ (kJ kg⁻¹ K⁻¹)',ylabel='Temperature (K)');ax[0].legend(fontsize=11)
 for a in ax:a.grid(alpha=.2)
 fig.tight_layout();fig.savefig(O/f'cycle_{kind.lower()}.png');fig.savefig(O/f'cycle_{kind.lower()}.pdf');plt.close(fig)
fig,ax=plt.subplots(1,2,figsize=(8.4,3.4))
for kind,color in zip(['Otto','Diesel','Dual'],['#237a57','#2e69a3','#bb6b22']):
 c=[x for x in models if x['kind']==kind and x['window']==1 and x['var']][0]
 for i,(T,p,v,s) in enumerate(curves(c)):
  ax[0].plot(v*c['mass']*1e6,p/100,color=color,label=kind if i==0 else None);ax[1].plot(s,T,color=color)
ax[0].set(xlabel='Cylinder volume (cm³)',ylabel='Absolute pressure (bar)');ax[1].set(xlabel='s − s₁ (kJ kg⁻¹ K⁻¹)',ylabel='Temperature (K)');ax[0].legend()
for a in ax:a.grid(alpha=.2)
fig.tight_layout();fig.savefig(O/'cycles_variable.png');fig.savefig(O/'cycles_variable.pdf');plt.close(fig)
result={'Vd':Vd,'Vc':Vc,'Rcycle':R,'cv':cv,'cp':cp,'summary':summ,'models':models,'ECA':[{k:v for k,v in c.items() if k not in ['a','angle','t']} for c in cycles]}
(O/'calculation_results.json').write_text(json.dumps(result,indent=2))
print('GEOMETRY',Vd*1e6,'cycle R',R)
for s in summ:print('MEAN',s)
for c in models:print(c['window'],c['kind'],'variable',c['var'],'q',round(c['q'],2),'eta',round(c['eta'],4),'power',round(c['power'],2),'Tmax',round(max(s[0] for s in c['states']),2),'pmax',round(max(s[1] for s in c['states'])/100,2),'rc',round(c['rc'],3),'rp',round(c['rp'],3))
print('ECA',result['ECA']);print('SELF-CHECKS PASSED: 18 energy/entropy/p-dV checks and 9 output fits')
