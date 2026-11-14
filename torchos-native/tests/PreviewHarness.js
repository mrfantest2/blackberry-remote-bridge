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
function event(key,target=elements.home){return {key,target,preventDefault(){this.prevented=true;}};}
for(let i=0;i<12;i++){openPage(i);assert.equal(elements.home.hidden,true);assert.equal(elements.title.textContent,pages[i][0]);back();assert.equal(elements.home.hidden,false);assert.equal(document.activeElement,buttons[i<6?i:11]);}
openPage(0);assert.equal(elements.terminal.hidden,false);elements.command.value='help';submit();assert(elements.output.textContent.includes('Local only:'));
elements.command.value='status; reboot';submit();assert(elements.output.textContent.includes('Rejected:'));
elements.command.value='status';submit();assert(elements.output.textContent.includes('disconnected'));
for(let i=0;i<200;i++){elements.command.value='help';submit();}
assert(output.length<=4096);assert.equal(history.length,16);
previous();assert.equal(elements.command.value,'help');next();assert.equal(elements.command.value,'');
elements.command.value='x'.repeat(97);submit();assert(elements.output.textContent.includes('Rejected:'));
clearOutput();assert.equal(elements.output.textContent,'');back();
openPage(6);elements.draft.value='offline draft';elements.task1.checked=true;elements.label0.value='My device';saveNotes();back();openPage(6);
assert.equal(elements.draft.value,'offline draft');assert.equal(elements.task1.checked,true);assert(elements.saved.textContent.includes('session only'));back();
openPage(3);assert(elements.copy.textContent.includes('My device'));assert(elements.copy.textContent.includes('unavailable'));back();
openPage(5);assert(elements.copy.textContent.includes('Hardware readings unavailable'));
back();document.keydown(event('2'));assert.equal(elements.title.textContent,'Network Center');document.keydown(event('Escape'));assert.equal(elements.home.hidden,false);
buttons[0].focus();document.keydown(event('ArrowDown'));assert.equal(document.activeElement,buttons[1]);
openPage(11);openPage(7);back();assert.equal(elements.title.textContent,'More / secondary');back();
openPage(0);const typed=event('n',elements.command);document.keydown(typed);assert.equal(elements.title.textContent,'Terminal');
console.log('preview: terminal, bounds, navigation, keyboard, session notes and honest hardware assertions passed (DOM double only)');
