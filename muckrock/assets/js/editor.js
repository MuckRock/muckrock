import { ProseMirror } from 'prosemirror';
import {elt} from 'prosemirror/dist/dom';
import "prosemirror/dist/inputrules/autoinput";
import 'prosemirror/dist/markdown';
import 'prosemirror/dist/menu/tooltipmenu';

let editor = document.querySelector('textarea.prose-editor');
let toggle = document.getElementById('toggle-prosemirror');
let getContent, te, pm;

function toTextArea(focus) {
    te = editor.parentNode.insertBefore(elt('textarea'), editor.nextSibling);
    te.value = editor.value;
    if (pm) pm.wrapper.remove();
    if (focus !== false) {
        te.focus();
    }
    getContent = function() {
        return te.value;
    }
    $(te).change(function(){
        editor.value = getContent();
    });
}

function toProseMirror() {
    pm = window.pm = new ProseMirror({
        place: function(newNode){
            editor.parentNode.insertBefore(newNode, editor.nextSibling);
        },
        doc: editor.value,
        autoInput: true,
        docFormat: 'markdown',
        tooltipMenu: true
    });
    if (te) te.remove();
    pm.focus();
    getContent = function() {
        return pm.getContent("markdown");
    }
    pm.on('change', function(){
        editor.value = getContent();
    });
}

if (editor) {
    toProseMirror();
    editor.style.display = 'none';
}
if (toggle) {
    toggle.addEventListener('change', function() {
        if (toggle.checked) {
            toProseMirror();
        } else {
            let isFocused = editor === document.activeElement;
            toTextArea(isFocused);
        }
    });
}
