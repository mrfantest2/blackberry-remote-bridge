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

openPage(0);
resetTerminal();execute('help');cmd.value='sta';
previous();assert.equal(cmd.value,'help','previous recalls newest history');
next();assert.equal(cmd.value,'sta','next restores typed draft');
assertHistory(['help'],'navigation does not mutate history');

resetTerminal();execute('help');execute('status');cmd.value='sta';
previous();assert.equal(cmd.value,'status','first previous recalls newest');
previous();assert.equal(cmd.value,'help','second previous recalls older');
next();assert.equal(cmd.value,'status','next returns toward newest');
next();assert.equal(cmd.value,'sta','next restores saved draft after multiple previous');
next();assert.equal(cmd.value,'sta','repeated next at newest preserves live draft');
assertHistory(['help','status'],'browsing never mutates history');
cmd.value='edited';previous();assert.equal(cmd.value,'status','previous after edit captures new draft');
next();assert.equal(cmd.value,'edited','edited draft restored');

resetTerminal();cmd.value='sta';
previous();assert.equal(cmd.value,'sta','empty history previous keeps typed text');
next();assert.equal(cmd.value,'sta','empty history next keeps typed text');
assertHistory([],'empty history stays empty');

resetTerminal();execute('help');const outputBefore=output;cmd.value='clear';
previous();assert.equal(output,outputBefore,'navigation never executes draft');
next();assert.equal(output,outputBefore,'navigation never echoes draft');

resetTerminal();execute('help');cmd.value='sta';previous();cmd.value='status';submit();
next();assert.equal(cmd.value,'','submission clears saved draft');
previous();assert.equal(cmd.value,'status','submission resets browsing state');
next();assert.equal(cmd.value,'','cleared draft restored after submission');

resetTerminal();execute('help');cmd.value='sta';previous();elements.clear.events.click();
assert.equal(cmd.value,'','clear clears input field');
next();assert.equal(cmd.value,'','clear leaves empty draft');
previous();assert.equal(cmd.value,'clear','clear resets browsing to newest');

resetTerminal();execute('help');cmd.value='x'.repeat(200);previous();next();
assert.equal(cmd.value.length,96,'draft bounded to input limit');
assertHistory(['help'],'bounded draft never stored in history');

console.log('preview: history draft preservation, empty history, reset and bounds assertions passed (DOM double only)');
