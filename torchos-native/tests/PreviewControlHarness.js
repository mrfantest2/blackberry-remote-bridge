'use strict';
const assert=require('assert');
class Element {
 constructor(id){this.id=id;this.hidden=false;this.value='';this.textContent='';this.checked=false;this.dataset={};this.events={};this.children=[];}
 addEventListener(name,fn){this.events[name]=fn;}
 focus(){document.activeElement=this;}
 querySelectorAll(){return this.children;}
 querySelector(){return this.children[0];}
}
const elements={};
const ids=['home','detail','back','title','copy','clock','terminal','output','command','run','previous','next','help','clear','notes','draft','save','saved','about','primary','secondary'];
for(const id of ids)elements[id]=new Element(id);
for(let i=0;i<3;i++){elements['task'+i]=new Element('task'+i);elements['label'+i]=new Element('label'+i);}
const buttons=[];
for(let i=0;i<12;i++){const b=new Element('page'+i);b.dataset.page=String(i);buttons.push(b);}
elements.home.children=buttons.slice(0,6).concat(buttons[11]);elements.primary.children=elements.home.children;
const document={activeElement:null,getElementById:id=>{assert(elements[id],id);return elements[id];},querySelectorAll:()=>buttons,querySelector:selector=>buttons[Number(selector.match(/\d+/)[0])],addEventListener:(name,fn)=>{document[name]=fn;}};
function setInterval(){}
/*@@SCRIPT@@*/
function cleanHistory(){return history.every(entry=>!/[\u0000-\u001f\u007f]/.test(entry));}
function rejectedControl(raw,label){
 const historyBefore=history.length;
 const outputBefore=output;
 execute(raw);
 assert(output.includes('Rejected:'),label+' rejected');
 assert.equal(history.length,historyBefore,label+' not stored');
 assert(!output.slice(outputBefore.length).includes('local> '),label+' not echoed raw');
 assert(cleanHistory(),label+' history clean');
}
for(let c=0;c<=0x1f;c++){
 const control=String.fromCharCode(c);
 rejectedControl(control+'help','leading control '+c);
 rejectedControl('help'+control,'trailing control '+c);
 rejectedControl('hel'+control+'p','embedded control '+c);
}
const del=String.fromCharCode(0x7f);
rejectedControl(del+'help','leading DEL');
rejectedControl('help'+del,'trailing DEL');
rejectedControl('hel'+del+'p','embedded DEL');
const historyBefore=history.length;
execute(null);
assert(output.includes('Rejected:'),'null rejected');
assert.equal(history.length,historyBefore,'null not stored');
assert(cleanHistory(),'null history clean');
execute('  help  ');
assert.equal(history[history.length-1],'help','spaces normalized out of history');
assert(output.includes('local> help\n'),'spaced allowed command runs');
assert(cleanHistory(),'accepted history clean');
execute('\nhelp');
assert(output.includes('Rejected:'),'newline still rejected');
execute('help');
assert(output.includes('Local only:'),'terminal recovers after rejection');
console.log('preview: control-character rejection parity assertions passed (DOM double only)');
