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
const cmd=elements.command;
function resetTerminal(){history=[];cursor=0;if(typeof commandDraft!=='undefined')commandDraft='';}
function assertHistory(expected,label){assert.deepEqual(Array.from(history),expected,label);}
function browse(){resetTerminal();execute('help');execute('date');cmd.value='sta';previous();assert.equal(cursor,1,'browsing before rejection');}

openPage(0);
browse();let before=output;cmd.value='\u0001help';submit();
assert(output.slice(before.length).includes('Rejected:'),'control submission rejected');
assertHistory(['help','date'],'control submission not stored');
assert(!output.slice(before.length).includes('\u0001help'),'control submission not echoed raw');
next();assert.equal(cmd.value,'','rejected control does not restore stale draft');

browse();before=output;execute(null);cmd.value='';
assert(output.slice(before.length).includes('Rejected:'),'null submission rejected');
assertHistory(['help','date'],'null submission not stored');
next();assert.equal(cmd.value,'','rejected null does not restore stale draft');

browse();before=output;const tooLong='z'.repeat(97);cmd.value=tooLong;submit();
assert(output.slice(before.length).includes('Rejected:'),'overlimit submission rejected');
assertHistory(['help','date'],'overlimit submission not stored');
assert(!output.slice(before.length).includes('zzzz'),'overlimit submission not echoed raw');
next();assert.equal(cmd.value,'','rejected overlimit does not restore stale draft');

browse();elements.help.events.click();
assert.equal(cmd.value,'','help clears browsing input');
assert.equal(document.activeElement,cmd,'help restores command focus');
assertHistory(['help','date','help'],'help submission still recorded');
next();assert.equal(cmd.value,'','help resets browsing draft');

console.log('preview: rejected control, null and overlimit submissions reset browsing; Help parity passed (DOM double only)');
